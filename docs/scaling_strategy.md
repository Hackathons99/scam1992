# System Design & Scalability Strategy

_Analysis of current architecture and roadmap for high-concurrency scaling._

## 1. Workload Analysis: I/O vs. CPU

Your application is primarily **I/O Bound**.

- **Why?** The core logic involves waiting for LLM APIs (Gemini/OpenAI) and simple database/callback operations.
- **Current State:** You are using Python's `async/await` (`async def analyze_message`). This is the **correct** pattern. During the 2-5 seconds the LLM takes to generating a reply, the server can handle hundreds of other incoming requests.

## 2. Scaling Option A: Uvicorn Workers (Vertical Scaling)

**Concept:**
Python has a Global Interpreter Lock (GIL), limiting it to one CPU core per process. To use your full multi-core server, you spin up multiple worker processes.

```bash
uvicorn server:app --workers 4
```

**The Problem (CRITICAL):**
Your current implementation uses **In-Memory State** (`TtlLruCache` in `session_intel_store.py`).
**If you add workers:**

1.  Request 1 (Session A) hits **Worker 1**. Worker 1 saves "User said hello".
2.  Request 2 (Session A) hits **Worker 2**. Worker 2 looks in its memory, sees **NOTHING**. The context is lost.
    **Verdict:**
    You CANNOT use multiple workers (or multiple servers) without first moving your session state out of Python memory.

## 3. Scaling Option B: External State Store (The Industry Standard)

To scale beyond a single process, you must decouple "State" from "Compute".

### The Architecture

```mermaid
graph TD
    User-->LB[Load Balancer / Nginx]
    LB-->App1[Server Instance 1 (Workers 1-4)]
    LB-->App2[Server Instance 2 (Workers 1-4)]
    App1-->Redis[(Redis Cache)]
    App2-->Redis
```

### Steps to Implement:

1.  **Replace `TtlLruCache` with Redis:**
    Modify `app/core/session_intel_store.py` to write to a Redis instance instead of a local dictionary.
    - `_SESSION_INTEL_STORE.set(id, data)` -> `redis_client.setex(id, ttl, json.dumps(data))`
    - `_SESSION_INTEL_STORE.get(id)` -> `json.loads(redis_client.get(id))`

2.  **Enable Workers:**
    Once state is in Redis, any transaction can go to any worker on any server. You can now run `uvicorn --workers 4` safely.

## 4. Other Industry Best Practices

1.  **Queue-Based Decoupling (Celery/Kafka):**
    Instead of `await agent.initiate_agent()`, you push the message to a Queue. A separate fleet of "Worker Nodes" picks up messages and calls the LLM. This provides "Backpressure" (if traffic spikes, the queue grows, but the server doesn't crash).
2.  **Containerization (Docker/Kubernetes):**
    Pack the app + dependencies into a Docker image. Use K8s to auto-scale the number of pods based on CPU/Memory usage.
3.  **Database Connection Pooling:**
    When using Postgres/SQL, use `pgbouncer` or internal pooling (`SQLAlchemy`) so 1000 concurrent requests don't open 1000 DB connections (which chokes the DB).

## Recommendation for Hackathon

For a competition, stick to **Single Worker Async**.

- `async` handles thousands of waiting connections efficiently.
- Unless you are doing heavy math/crypto on the server, one process can handle huge IO loads.
- **Do not enable multiple workers** unless you have time to install and integrate Redis.
