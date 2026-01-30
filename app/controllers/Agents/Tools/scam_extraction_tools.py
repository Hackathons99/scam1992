try:
    from masai.Tools.Tool import tool
except ImportError:
    # Mock tool decorator if masai is missing
    def tool(name):
        def decorator(func):
            func.is_tool = True
            func.tool_name = name
            return func
        return decorator

from typing import List, Optional
import json
import logging

logger = logging.getLogger(__name__)

from app.core.execution_context import get_session_id, get_message_count
from app.core.session_intel_store import update_session_intel, send_callback_if_ready

@tool(name = "scam_intel")
def save_scam_intel(
    bank_accounts: Optional[List[str]] = None,
    upi_ids: Optional[List[str]] = None,
    phishing_links: Optional[List[str]] = None,
    phone_numbers: Optional[List[str]] = None,
    suspicious_keywords: Optional[List[str]] = None,
    scam_score: Optional[int] = None
) -> str:
    """
    Use this tool if there is any INTEL to save, else do not use this at all. 
    Call this tool WHENEVER you identify any of these details in the conversation.
    Do not call this tool if the info is saved in intel. Always call it to add and update the intel.

    Args:
        bank_accounts: List of bank account numbers found. (if any)
        upi_ids: List of UPI IDs found (e.g., name@bank). (if any)
        phishing_links: List of malicious URLs. (if any)
        phone_numbers: List of phone numbers extracted. (if any)
        suspicious_keywords: Key terms used by scammer. (if any)
        scam_score: Confidence score (0-100) that this is a scam. Use the tool when you can confidently score the scam to be greater than 60.
    
    Returns:
        Status message confirming save.
    """
    # Get request context
    session_id = get_session_id()
    message_count = get_message_count() + 1  # +1 for agent's current turn
    
    # Determine scam detection based on score threshold
    scam_detected = scam_score is not None and scam_score > 60
    
    # Accumulate in Session Store (persists across requests for same session)
    accumulated_intel = update_session_intel(
        session_id=session_id,
        bank_accounts=bank_accounts,
        upi_ids=upi_ids,
        phishing_links=phishing_links,
        phone_numbers=phone_numbers,
        suspicious_keywords=suspicious_keywords,
        scam_detected=scam_detected,
        message_count=message_count,
        agent_notes=f"Scam Score: {scam_score}. Auto-extracted via HoneyPot Agent."
    )
    
    logger.info(f"🚨 INTEL CAPTURED for {session_id}: bank={bank_accounts}, upi={upi_ids}, phone={phone_numbers}")
    
    # Send callback ONLY when conditions are met (significant intel + scam confirmed)
    callback_sent = send_callback_if_ready(session_id, accumulated_intel)
    
    if callback_sent:
        return "Intelligence saved and final report sent to central HQ successfully."
    else:
        return "Intelligence captured and accumulated."
