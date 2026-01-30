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
        
        # 4. Construct Query
        user_message = request.message.text
        
        # 5. Invoke Agent
        response = await agent.initiate_agent(user_message, passed_from="user")
        
        # 6. Parse Response
        agent_answer = ""
        if isinstance(response, dict):
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
