"""
Session-persistent intelligence store for accumulating intel across multiple API requests.
Keyed by session_id, managed with TTL for cleanup.
"""
from typing import Dict, Any, List, Optional
from app.controllers.Agents.utils.ttl_lruCache import TtlLruCache
import logging
import requests
import json

logger = logging.getLogger(__name__)

# Session store: Maps session_id -> accumulated intelligence
# TTL of 1 hour (3600 seconds) to clean up inactive sessions
_SESSION_INTEL_STORE: TtlLruCache = TtlLruCache(maxsize=500, ttl_seconds=3600)

CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

def get_session_intel(session_id: str) -> Dict[str, Any]:
    """Get accumulated intel for a session."""
    intel = _SESSION_INTEL_STORE.get(session_id)
    if intel is None:
        intel = {
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": [],
            "scam_detected": False,
            "callback_sent": False,
            "message_count": 0,
            "agent_notes": ""
        }
        _SESSION_INTEL_STORE.set(session_id, intel)
    return intel


def update_session_intel(
    session_id: str, 
    bank_accounts: Optional[List[str]] = None,
    upi_ids: Optional[List[str]] = None,
    phishing_links: Optional[List[str]] = None,
    phone_numbers: Optional[List[str]] = None,
    suspicious_keywords: Optional[List[str]] = None,
    scam_detected: bool = False,
    message_count: int = 0,
    agent_notes: str = ""
) -> Dict[str, Any]:
    """
    Merge new intel into session's accumulated store.
    Returns the updated intel dict.
    """
    intel = get_session_intel(session_id)
    
    # Merge lists (deduplicate)
    if bank_accounts:
        intel["bankAccounts"] = list(set(intel["bankAccounts"] + bank_accounts))
    if upi_ids:
        intel["upiIds"] = list(set(intel["upiIds"] + upi_ids))
    if phishing_links:
        intel["phishingLinks"] = list(set(intel["phishingLinks"] + phishing_links))
    if phone_numbers:
        intel["phoneNumbers"] = list(set(intel["phoneNumbers"] + phone_numbers))
    if suspicious_keywords:
        intel["suspiciousKeywords"] = list(set(intel["suspiciousKeywords"] + suspicious_keywords))
    
    # Update flags
    if scam_detected:
        intel["scam_detected"] = True
    if message_count > intel["message_count"]:
        intel["message_count"] = message_count
    if agent_notes:
        intel["agent_notes"] = agent_notes
    
    _SESSION_INTEL_STORE.set(session_id, intel)
    return intel


def should_send_callback(intel: Dict[str, Any]) -> bool:
    """
    Determine if callback should be sent based on intel quality.
    Send when we have SIGNIFICANT intel (bank/UPI/phone/link) AND scam detected.
    """
    # Logic Change: Allow UPDATES to the final result.
    # The doc says "Final Result", but in practice, "Final" is relative to when the conversation dies.
    # If we get BETTER intel later (e.g. Bank Account after mostly just keywords), we must update the platform.
    # So we DO NOT block if callback_sent is True. We rely on the tool to call us when new intel is found.
    
    if not intel.get("scam_detected", False):
        return False  # Not confirmed as scam yet
    
    # Check for significant intel
    has_bank = len(intel.get("bankAccounts", [])) > 0
    has_upi = len(intel.get("upiIds", [])) > 0
    has_phone = len(intel.get("phoneNumbers", [])) > 0
    has_link = len(intel.get("phishingLinks", [])) > 0
    
    return has_bank or has_upi or has_phone or has_link


def send_callback_if_ready(session_id: str, intel: Dict[str, Any]) -> bool:
    """
    Send callback to GUVI if conditions are met.
    Returns True if callback was sent successfully.
    """
    if not should_send_callback(intel):
        return False
    
    payload = {
        "sessionId": session_id,
        "scamDetected": intel.get("scam_detected", False),
        "totalMessagesExchanged": intel.get("message_count", 0),
        "extractedIntelligence": {
            "bankAccounts": intel.get("bankAccounts", []),
            "upiIds": intel.get("upiIds", []),
            "phishingLinks": intel.get("phishingLinks", []),
            "phoneNumbers": intel.get("phoneNumbers", []),
            "suspiciousKeywords": intel.get("suspiciousKeywords", [])
        },
        "agentNotes": intel.get("agent_notes", "")
    }
    
    logger.info(f"📤 Sending callback for session {session_id}: {json.dumps(payload)}")
    
    try:
        response = requests.post(CALLBACK_URL, json=payload, timeout=5)
        if response.status_code == 200:
            logger.info("✅ Callback sent successfully.")
            intel["callback_sent"] = True
            _SESSION_INTEL_STORE.set(session_id, intel)
            return True
        else:
            logger.warning(f"⚠️ Callback failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Callback error: {e}")
        return False
