# HackathonScam Project

This project implements a scam detection agent using a "Honeypot" strategy. It engages with potential scammers to extract intelligence (UPI IDs, bank accounts, etc.) and determines if the interaction is malicious.

## 🚀 Getting Started

### 1. Installation

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/Hackathons99/scam1992.git
    cd scam1992
    ```

2.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables**:
    Copy the example file and update it with your API keys:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` and set:
    - `API_KEY`: A secret key to secure your API (default: `YOUR_SECRET_API_KEY`).
    - `LLM_API_KEY`: Your OpenAI or Google Gemini API Key.
    - `LLM_PROVIDER`: e.g., `openai` or `gemini`.

---

## 🏃‍♂️ Running the Server

To start the API server locally:

```bash
python server.py
# OR
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`.
You can view the interactive API docs at: `http://localhost:8000/docs`.

---

## 🧪 Testing

We provide two ways to test the application:

### 1. Interactive Console Test (No Server Required)

This script runs the agent logic directly in your terminal, mirroring exactly what the API does. It's the fastest way to debug the conversation flow.

```bash
python scripts/test_honeypot.py
```

- **Usage**: Type messages as if you are the scammer. The agent will reply.
- **Features**: Displays extracted intelligence (UPIs, Bank #s) and scam detection alerts in real-time.

### 2. API Integration Test

This script sends actual HTTP requests to your running local server to verify the endpoints.

1.  Ensure the server is running (`python server.py`).
2.  Run the test script:
    ```bash
    python scripts/test_api.py
    ```
    _(Note: You may need to update the `x-api-key` header in this script if you changed the default key in `.env`)._

---

## 📡 API Reference

### **1. Analyze Message**

**Endpoint**: `POST /api/v1/analyze`  
**Description**: Analyzes a user's message, detects scam intent, and generates a reply.

- **Headers**: `x-api-key: <YOUR_API_KEY>`
- **Payload** (`AnalysisRequest`):
  ```json
  {
    "sessionId": "unique_session_id",
    "message": {
      "sender": "scammer",
      "text": "Win a lottery! Click here.",
      "timestamp": "2023-10-27T10:00:00Z"
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "whatsapp",
      "language": "en"
    }
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "reply": "Tell me more about this lottery."
  }
  ```

### **2. Update Final Result**

**Endpoint**: `POST /api/v1/update-result`  
**Description**: (Callback) Reports the final verdict and extracted intel for a session.

- **Payload** (`FinalResultPayload`):
  ```json
  {
    "sessionId": "unique_session_id",
    "scamDetected": true,
    "totalMessagesExchanged": 5,
    "extractedIntelligence": {
      "bankAccounts": ["1234567890"],
      "suspiciousKeywords": ["lottery", "urgent"]
    }
  }
  ```

---

## 🔧 Experimental: Cognee Persistence

This project includes experimental support for **Cognee** (Graph Memory).
To verify the multi-user persistence features, you can run:

```bash
python scripts/reproduce_cognee_multiuser.py
```

This script demonstrates how to segregate memory between different users using Cognee's `User` models.
