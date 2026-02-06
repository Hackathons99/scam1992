# 🍯 Agentic Honey-Pot

> **AI-Powered Scam Detection & Intelligence Extraction System**

An autonomous AI honeypot that detects scam messages, engages scammers in believable conversations, and extracts actionable intelligence—all without revealing its true nature.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange.svg)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 🎯 What It Does

When a scammer sends a message like:
> *"URGENT: Your bank account will be blocked. Share OTP now!"*

Our system:
1. **Detects** the scam intent instantly
2. **Activates** an AI agent that pretends to be a confused, naive victim
3. **Engages** the scammer in a prolonged conversation (wasting their time)
4. **Extracts** valuable intelligence (phone numbers, bank accounts, UPI IDs)
5. **Reports** everything to the central evaluation system

---

## 📊 Sample Output

```json
{
  "scamDetected": true,
  "totalMessagesExchanged": 18,
  "extractedIntelligence": {
    "bankAccounts": ["1234567890123456"],
    "upiIds": ["scammer.fraud@fakebank"],
    "phoneNumbers": ["+91-9876543210"],
    "suspiciousKeywords": ["urgent", "blocked", "otp", "verify"]
  },
  "agentNotes": "Scammer used urgency/fear tactics, credential theft attempts. Extracted: 1 bank account(s), 1 UPI ID(s), 1 phone number(s)."
}
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Gemini API Key

### Installation

```bash
# Clone the repository
git clone https://github.com/Hackathons99/scam1992.git
cd scam1992

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys
```

### Running Locally

```bash
python server.py
```

The API will be available at `http://localhost:8000`

---

## 📡 API Usage

### Endpoint
```
POST /api/v1/analyze
```

### Headers
```
x-api-key: YOUR_SECRET_API_KEY
Content-Type: application/json
```

### Request Body
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked. Share OTP now.",
    "timestamp": 1770005528731
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

### Response
```json
{
  "status": "success",
  "reply": "Oh no! Blocked?? That sounds really bad! What do I need to do? Im not very good with computers plz help me"
}
```

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Scammer API    │────▶│   FastAPI Server │────▶│  HONEYPOT Agent │
│    Request      │     │   (routes.py)    │     │  (Gemini AI)    │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                        ┌──────────────────┐              │
                        │ Session Intel    │◀─────────────┘
                        │     Store        │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │  GUVI Callback   │
                        │   (Final Intel)  │
                        └──────────────────┘
```

---

## 📁 Project Structure

```
scam1992/
├── server.py              # Entry point
├── Procfile               # Railway deployment
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
├── docs/
│   └── CODEBASE_DOCUMENTATION.md  # Detailed documentation
└── app/
    ├── main.py            # FastAPI setup
    ├── api/routes.py      # API endpoints
    ├── models/schemas.py  # Data structures
    ├── core/
    │   ├── session_intel_store.py  # Intelligence storage
    │   └── execution_context.py    # Request tracking
    └── controllers/Agents/
        ├── HONEYPOT/
        │   ├── PROMPTS.py           # Agent personality
        │   └── honeypot_agent.py    # Agent creation
        └── Tools/
            └── scam_extraction_tools.py  # Intel extraction
```

📖 **For detailed documentation, see [CODEBASE_DOCUMENTATION.md](docs/CODEBASE_DOCUMENTATION.md)**

---

## 🤖 Agent Behavior

The HONEYPOT agent is designed to:

| Behavior | Purpose |
|----------|---------|
| 😰 Act confused and scared | Build trust with scammer |
| ⏳ Create delays ("let me check...") | Waste scammer's time |
| 🔍 Ask clarifying questions | Extract more information |
| 🎭 Never reveal it's an AI | Maintain believability |
| 📝 Extract intelligence | Gather actionable data |

### Sample Conversation

**Scammer**: Your account will be blocked. Share your UPI ID now.

**Honeypot**: Oh no blocked?? That sounds really bad 😥 But whats a UPI ID? Is that like my phone number? Im not very good with these things plz explain slowly

---

## ☁️ Deployment

### Railway (Recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway up
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ | Gemini AI API key |
| `API_KEY` | ✅ | Secret key for API authentication |
| `PORT` | ❌ | Server port (default: 8000) |

---

## 🔒 Security

- ✅ API key authentication required
- ✅ No real user data stored
- ✅ Session data auto-expires after 1 hour
- ✅ Sensitive files excluded via `.gitignore`

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Average Response Time | ~3.5 seconds |
| Model Used | Gemini 2.5 Flash Lite |
| Max Concurrent Sessions | 500 |
| Session TTL | 1 hour |

---

## 👥 Team

This project was built for **GUVI Hackathon** by:

| Name | LinkedIn | GitHub |
|------|----------|--------|
| **Sathvik V** | [Connect](http://www.linkedin.com/in/sathvik-v17) | [@404-GeniusNotFound](https://github.com/404-GeniusNotFound) |
| **Shaunak G Roy** | [Connect](https://www.linkedin.com/in/shaunak-g-r-652225289/) | [@shaunthecomputerscientist](https://github.com/shaunthecomputerscientist) |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev) for the AI backbone
- [FastAPI](https://fastapi.tiangolo.com) for the web framework
- [GUVI](https://guvi.in) for organizing the hackathon

---

<p align="center">
  <b>Built with 💜 for fighting online scams</b>
</p>
