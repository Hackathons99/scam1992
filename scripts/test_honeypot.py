import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.schemas import AnalysisRequest, AnalysisResponse, Message, Metadata
from app.controllers.Agents.register import ensure_agent
from app.models.context import UserContext
from app.core.execution_context import session_context
from app.core.session_intel_store import get_session_intel

# Constants for context keys (matching routes.py)
KEY_SESSION_ID = "session_id"
KEY_MESSAGE_COUNT = "message_count"
KEY_METADATA = "metadata"

async def run_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """
    Functionally mirrors the logic in app/api/routes.py:analyze_message
    """
    token = None
    try:
        # 1. Create User Context
        ctx_metadata = request.metadata.model_dump() if request.metadata else {}
        ctx = UserContext(
            session_id=request.sessionId,
            metadata=ctx_metadata
        )
        
        # 2. Get Agent
        agent = ensure_agent("HONEYPOT", ctx)
        
        # 3. Set Execution Context
        current_msg_count = len(request.conversationHistory) + 1
        
        token = session_context.set({
            KEY_SESSION_ID: request.sessionId,
            KEY_MESSAGE_COUNT: current_msg_count,
            KEY_METADATA: ctx_metadata,
            "extracted_intelligence": {},
            "scam_detected": False
        })
        
        # 4. Invoke Agent
        user_message = request.message.text
        response = await agent.initiate_agent(user_message, passed_from="user")
        
        # 5. Parse Response
        agent_answer = ""
        if isinstance(response, dict):
            agent_answer = response.get("answer", str(response))
        else:
            agent_answer = str(response)

        # 6. Get Accumulated Intelligence
        accumulated_intel = get_session_intel(request.sessionId)
        
        # Build Response (matching routes.py structure)
        return AnalysisResponse(
            status="success",
            reply=agent_answer
        )

    except Exception as e:
        print(f"ERROR in run_analysis: {e}")
        return AnalysisResponse(
            status="error",
            reply=str(e)
        )
    finally:
        if token:
            session_context.reset(token)

async def main():
    print("🚀 Honey-Pot Functional Test (Mirroring API Logic)")
    print("-------------------------------------------------")
    
    session_id = "wertyu-dfghj-ertyui-test"
    history = []
    
    # Competition-accurate metadata
    metadata = Metadata(
        channel="SMS",
        language="English",
        locale="IN"
    )

    print(f"Session started: {session_id}")
    print("Type 'exit' to quit. Use keywords like 'UPI' or 'bank' to trigger tool logic.\n")

    while True:
        user_input = input("Scammer> ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        # 1. Prepare Request (Competition Format)
        request_obj = AnalysisRequest(
            sessionId=session_id,
            message=Message(
                sender="scammer",
                text=user_input,
                timestamp=datetime.now().isoformat()
            ),
            conversationHistory=history,
            metadata=metadata
        )
        
        # 2. Execute Analysis (Functional Mirror)
        print("🤖 Processing...", end="\r")
        response = await run_analysis(request_obj)
        
        # 3. Handle Result
        if response.status == "success":
            print(f"🤖 HoneyPot> {response.reply}")
            
            # SIMULATE CALLBACK CHECK: Fetch directly from store to verify intel
            intel = get_session_intel(session_id)
            if intel.get("scam_detected"):
                 print(f"⚠️ [SCAM DETECTED] Score > Threshold")
            
            if any([intel.get("bankAccounts"), intel.get("upiIds"), intel.get("phoneNumbers")]):
                print(f"📊 [INTEL CAPTURED in STORE]: {json.dumps(intel, indent=2)}")
            
            # Update history for next turn
            history.append(request_obj.message)
            history.append(Message(
                sender="user",
                text=response.reply,
                timestamp=datetime.now().isoformat()
            ))
        else:
            print(f"❌ Error: {response.reply}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
