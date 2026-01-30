# Project Knowledge & Analysis

## 1. Problem Statement: Agentic Honey-Pot

**Goal:** Build an AI-powered system to detect scam intent and autonomously engage scammers to extract intelligence.

### Key Requirements

- **Detection:** Identify scam/fraudulent messages.
- **Engagement:** Activate an AI agent to converse with the scammer primarily to extract info, maintaining a human-like persona.
- **Intelligence Extraction:** Gather Bank Accounts, UPI IDs, Phishing Links, Phone Numbers, Suspicious Keywords.
- **API Output:** Structured JSON with engagement metrics and extracted intelligence.
- **Mandatory Callback:** Send final results to `https://hackathon.guvi.in/api/updateHoneyPotFinalResult`.

### API Specifications

- **Input:** JSON with `sessionId`, `message` (sender, text, timestamp), `conversationHistory`, `metadata`.
- **Output:** JSON with `status`, `scamDetected`, `engagementMetrics`, `extractedIntelligence`, `agentNotes`.

### Constraints

- No impersonation of real individuals.
- No illegal instructions or harassment.
- Responsible data handling.

## 2. Reference Architecture (mas-ai / qharmony-bot)

Based on `qharmony-bot/docs/agents` analysis.

### System Components

- **mas-ai Framework:** Likely the underlying engine for agent orchestration.
- **Agent API:**
  - `/agent/query`: Non-streaming response.
  - `/agent/query/stream`: Streaming response (SSE).
  - `/agent/upload-document`: For context/RAG (PDF/CSV/XLSX).
  - `/agent/delete-document`: Cleanup.
- **Session Management:** Unique sessions with TTL (e.g., 30 mins).
- **Agents:** Named agents (e.g., CLARA, BREA) specialized for tasks.

### Relevance to Honey-Pot

- **Streaming:** Essential for real-time conversation simulation if the honey-pot needs to feel "live", though the API spec implies a request-response model for the hackathon endpoint itself.
- **Context/Memory:** `conversationHistory` in the input must be processed. `mas-ai` likely handles context retention.
- **Document Upload:** Could be used if we need to "seed" the agent with specific persona documents or scam knowledge bases dynamically, but likely less critical for the core honey-pot logic than the conversation engine.
- **Agent Types:** We will likely define a `SCAM_DEFENDER` or `HONEYPOT` agent type.

### Usage Patterns

- **Python Client:** `requests.post` to interact with the local agent server.
- **Interactive Testing:** CLI scripts (`test_agent_query.py`) are useful for debugging agent prompts and flows.

## 3. Proposed Implementation Strategy

1.  **Project Structure:** Mimic `qharmony-bot` but simplified.
    - `src/`: Core logic.
    - `docs/`: Documentation.
    - `tests/`: Validation.
    - `scripts/`: Utility scripts.
2.  **Tech Stack:** Python (likely FastAPI or Flask given the API requirements).
3.  **Agent Logic:**
    - **Detector:** Lightweight model or prompt to classify "Scam" vs "Safe".
    - **Engager:** LLM (e.g., Gemini/GPT) with a specific system prompt to act as a naive/curious victim.
    - **Extractor:** Regular expressions or structured extraction prompt to pull intelligence during/after the chat.
