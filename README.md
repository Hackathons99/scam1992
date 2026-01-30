# HackathonScam Project

This project implements a scam detection agent using a "Honeypot" strategy and integrates with the **Cognee** framework for persistent, graph-based memory.

## 🚀 Setup

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/Hackathons99/scam1992.git
    cd scam1992
    ```

2.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

    _(Ensure you have the `cognee` dependencies installed as well if not included in requirements)._

3.  **Environment Variables**:
    Copy `.env.example` to `.env` and fill in your keys:
    ```ini
    API_KEY=your_secret_api_key
    LLM_API_KEY=your_openai_or_gemini_key
    # ... other config ...
    ```

---

## 🧪 Running the Cognee Test Script

We have a dedicated script to demonstrate **Multi-User Data Persistence** using Cognee. This scripts shows how to create users, segregate their data, and inspect local storage.

### **1. Script Location**

The script is located at: `scripts/reproduce_cognee_multiuser.py`

### **2. How to Run**

You need to ensure the `cognee` package is in your python path.

```bash
# Set PYTHONPATH to include the cognee repo if it's cloned locally
# Windows PowerShell
$env:PYTHONPATH="path\to\cognee_repo"; python scripts/reproduce_cognee_multiuser.py

# Linux/Mac
PYTHONPATH=path/to/cognee_repo python scripts/reproduce_cognee_multiuser.py
```

### **3. What it does**

- **Creates Users**: Generates two unique users with distinct IDs.
- **Adds Data**: Ingests separate "Secret Code" text for each user.
- **Verifies Storage**: Checks the local `.cognee_data` and `.cognee_system` directories to confirm data persistence.
- **Gemini Support**: The script includes comments on how to enable Google Gemini by setting `LLM_PROVIDER="gemini"` and your `LLM_API_KEY`.

---

## 📡 API Usage

The main application exposes the following endpoints (defined in `app/api/routes.py`).

### **1. Analyze Message (`POST /analyze`)**

Analyzes a user's message to detect scam intent.

- **Headers**: `x-api-key: <YOUR_API_KEY>`
- **Payload** (`AnalysisRequest`):
  ```json
  {
    "sessionId": "session_123",
    "message": {
      "sender": "user",
      "text": "I got a message about winning a lottery.",
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
    "reply": "This sounds suspicious. Do not share your bank details..."
  }
  ```

### **2. Update Final Result (`POST /update-result`)**

Callback endpoint to report the final verdict of a session.

- **Payload** (`FinalResultPayload`):
  ```json
  {
    "sessionId": "session_123",
    "scamDetected": true,
    "totalMessagesExchanged": 5,
    "extractedIntelligence": {
      "bankAccounts": ["1234567890"],
      "suspiciousKeywords": ["lottery", "urgent", "click here"]
    },
    "agentNotes": "User was targeted by a lottery scam."
  }
  ```

---

## 🧠 Cognee Integration Notes

- **Multi-User**: Uses `cognee.modules.users.methods.create_user` to ensure data isolation. Do **not** pass raw strings as user IDs; you must use valid `User` objects.
- **Storage**: Data is persisted in `.cognee_data` (files) and `.cognee_system` (databases).
- **Gemini**: Validated to work with `gemini-1.5-flash` via the `gemini` provider setting.
