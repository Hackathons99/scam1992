"""
Context callable for the HoneyPot agent.
Provides the agent with its own 'memory' of extracted intelligence.
"""
from app.core.execution_context import get_session_id
from app.core.session_intel_store import get_session_intel
import logging

logger = logging.getLogger(__name__)

async def context_tool_callable(query: str) -> str:
    """
    Provides the current state of extracted intelligence for the current session.
    This helps the agent realize what it has already captured so it doesn't repeat itself.
    """
    session_id = get_session_id()
    if not session_id:
        return "No session information available."

    intel = get_session_intel(session_id)
    
    # Build a single clean string (no trailing commas/tuples)
    context_lines = [
        "### CURRENT EXTRACTED INTELLIGENCE SUMMARY",
        f"- Scam Detected: {intel.get('scam_detected', False)}",
        f"- Bank Accounts: {intel.get('bankAccounts', [])}",
        f"- UPI IDs: {intel.get('upiIds', [])}",
        f"- Phishing Links: {intel.get('phishingLinks', [])}",
        f"- Phone Numbers: {intel.get('phoneNumbers', [])}",
        f"- Suspicious Keywords: {intel.get('suspiciousKeywords', [])}",
        "",
        "### GUIDANCE",
        "1. If info is already in the list above, DO NOT call scam_intel again for it.",
        "2. Only call scam_intel to ADD NEW intelligence or UPDATE the scam score.",
        "3. Continue the persona to extract the MISSING items above."
    ]
    
    return "\n".join(context_lines)