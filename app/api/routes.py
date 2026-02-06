from fastapi import APIRouter, HTTPException
from app.models.schemas import AnalysisRequest, AnalysisResponse, FinalResultPayload, EngagementMetrics, ExtractedIntelligence
from app.controllers.Agents.register import get_or_create_manager, ensure_agent
from app.models.context import UserContext
from app.core.execution_context import session_context
from app.core.session_intel_store import get_session_intel
from dotenv import load_dotenv
load_dotenv()
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants for context keys
KEY_SESSION_ID = "session_id"
KEY_MESSAGE_COUNT = "message_count"
KEY_METADATA = "metadata"

# API Auth
from fastapi import Security, Depends
from fastapi.security import APIKeyHeader
import os
API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    # In production, use a secure comparison or env var
    # For Hackathon, we can accept any key or a specific one if defined
    expected_key = os.getenv("API_KEY", "YOUR_SECRET_API_KEY") # Default per doc
    if api_key != expected_key:
         raise HTTPException(
             status_code=403,
             detail="Could not validate credentials"
         )
    return api_key

import asyncio
import random

# Timeout for agent response (25 seconds to leave buffer for network latency)
AGENT_TIMEOUT_SECONDS = 25

# Fallback responses for different scam scenarios
FALLBACK_RESPONSES = [
    "Oh my goodness, I'm so worried now! What do I need to do? Please tell me more about this case.",
    "This is very scary, Officer. I want to cooperate fully. What details do you need from me?",
    "I don't want any trouble! Please help me understand what's happening with my account.",
    "Oh no, I had no idea! What information do you need to verify my identity?",
    "Please don't arrest me! I'll do whatever you say. What should I do next?"
]

async def run_agent_with_timeout(agent, user_message: str, timeout: float):
    """Run agent with timeout, return fallback response if timeout occurs."""
    try:
        response = await asyncio.wait_for(
            agent.initiate_agent(user_message, passed_from="user"),
            timeout=timeout
        )
        return response, False  # response, timed_out
    except asyncio.TimeoutError:
        logger.warning(f"Agent timed out after {timeout}s, using fallback response")
        return None, True  # response, timed_out

@router.post("/analyze", response_model=AnalysisResponse, dependencies=[Depends(get_api_key)])
async def analyze_message(request: AnalysisRequest):
    """
    Analyze incoming message for scam intent using the HoneyPot Agent.
    """
    token = None
    try:
        # 1. Create User Context
        ctx_metadata = request.metadata.dict() if request.metadata else {}
        ctx = UserContext(
            session_id=request.sessionId,
            metadata=ctx_metadata
        )
        
        # 2. Get Manager & Agent
        agent = ensure_agent("HONEYPOT", ctx)
        
        # 3. Set Execution Context (Inject into ContextVar for Deep Tools)
        # Message count = history + incoming message
        current_msg_count = len(request.conversationHistory) + 1
        
        token = session_context.set({
            KEY_SESSION_ID: request.sessionId,
            KEY_MESSAGE_COUNT: current_msg_count,
            KEY_METADATA: ctx_metadata,
            "extracted_intelligence": {},
            "scam_detected": False
        })
        
        # 4. Construct Query with Full Conversation Context
        # Format history for the agent to understand conversation flow
        history_context = ""
        if request.conversationHistory:
            history_lines = []
            for msg in request.conversationHistory:
                role = "Scammer" if msg.sender == "scammer" else "You (victim)"
                history_lines.append(f"{role}: {msg.text}")
            history_context = "Previous conversation:\n" + "\n".join(history_lines) + "\n\n"
        
        # Combine history with current message
        full_query = f"{history_context}Scammer's latest message: {request.message.text}"
        
        # 5. Invoke Agent with Timeout
        response, timed_out = await run_agent_with_timeout(
            agent, full_query, AGENT_TIMEOUT_SECONDS
        )
        
        # 6. Parse Response or use fallback
        agent_answer = ""
        if timed_out:
            # Use a random fallback response that sounds like a naive victim
            agent_answer = random.choice(FALLBACK_RESPONSES)
        elif isinstance(response, dict):
            agent_answer = response.get("answer", str(response))
        else:
            agent_answer = str(response)

        # 7. Return Simplified Response (Per ORIGINALDOC.TXT Section 8)
        # Detailed intel is handled via the Mandatory Callback (Section 12) managed by scam_extraction_tools.py
        return AnalysisResponse(
            status="success",
            reply=agent_answer
        )

    except Exception as e:
        logger.error(f"Error in /analyze: {e}")
        return AnalysisResponse(
            status="error",
            reply=f"Internal Error: {str(e)}"
        )
    finally:
        # Reset ContextVar to prevent leak across requests
        if token:
            session_context.reset(token)

@router.post("/update-result")
async def update_result(payload: FinalResultPayload):
    """
    Mock endpoint to simulate the mandatory callback to GUVI.
    In production, this logic might be internal or proxy to the actual external API.
    """
    print(f"Received Final Result Update for Session {payload.sessionId}:")
    print(payload.dict())
    return {"status": "success", "message": "Result updated successfully"}
