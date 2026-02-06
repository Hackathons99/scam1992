"""
Session-persistent intelligence store for accumulating intel across multiple API requests.
Keyed by session_id, managed with TTL for cleanup.
"""
from typing import Dict, Any, List, Optional
from app.controllers.Agents.utils.ttl_lruCache import TtlLruCache
import logging
import requests
import json
import re

# ============ REGEX PATTERNS FOR INTEL NORMALIZATION ============
# UPI ID pattern: name@bank or name@upi
UPI_PATTERN = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+')
# Phone pattern: +91 followed by 10 digits (Indian format)
PHONE_PATTERN = re.compile(r'\+?91?[\s-]?([6-9]\d{9})')
# URL pattern: http or https links
URL_PATTERN = re.compile(r'https?://[^\s<>"\')\]]+', re.IGNORECASE)
# Bank account pattern: digits with optional dashes/spaces
BANK_PATTERN = re.compile(r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{0,4}')

def normalize_upi_ids(raw_list: List[str]) -> List[str]:
    """Extract and normalize UPI IDs to format: name@bank"""
    result = []
    for item in raw_list:
        matches = UPI_PATTERN.findall(item)
        result.extend(matches)
    return list(set(result)) if result else raw_list

def normalize_phone_numbers(raw_list: List[str]) -> List[str]:
    """Normalize phone numbers to format: +91-XXXXXXXXXX"""
    result = []
    for item in raw_list:
        # Try to find 10-digit number
        match = PHONE_PATTERN.search(item)
        if match:
            result.append(f"+91-{match.group(1)}")
        else:
            # Fallback: extract any 10-digit sequence
            digits = re.sub(r'\D', '', item)
            if len(digits) >= 10:
                result.append(f"+91-{digits[-10:]}")
    return list(set(result)) if result else raw_list

def normalize_phishing_links(raw_list: List[str]) -> List[str]:
    """Extract and normalize URLs to format: http://... or https://..."""
    result = []
    for item in raw_list:
        matches = URL_PATTERN.findall(item)
        result.extend(matches)
    return list(set(result)) if result else raw_list

def normalize_keywords(raw_list: List[str]) -> List[str]:
    """Normalize keywords to lowercase, stripped format"""
    return list(set([kw.lower().strip() for kw in raw_list if kw.strip()]))

def generate_agent_notes(intel: Dict[str, Any]) -> str:
    """
    Generate descriptive agent notes based on extracted intelligence.
    Analyzes keywords and collected data to create a human-readable summary.
    """
    notes_parts = []
    keywords = [kw.lower() for kw in intel.get("suspiciousKeywords", [])]
    keywords_text = " ".join(keywords)
    
    # Detect tactics used
    tactics = []
    
    # Urgency/Fear tactics
    urgency_words = ["urgent", "immediate", "block", "suspend", "lock", "freeze", "expire", "hour", "minute", "today"]
    if any(word in keywords_text for word in urgency_words):
        tactics.append("urgency/fear tactics")
    
    # Credential theft attempts
    credential_words = ["otp", "pin", "password", "cvv", "expiry", "card number", "secret"]
    if any(word in keywords_text for word in credential_words):
        tactics.append("credential theft attempts")
    
    # Authority impersonation
    authority_words = ["bank", "rbi", "police", "government", "official", "department", "officer"]
    if any(word in keywords_text for word in authority_words):
        tactics.append("authority impersonation")
    
    # Payment redirection
    payment_words = ["upi", "transfer", "send", "payment", "account", "deposit"]
    if any(word in keywords_text for word in payment_words):
        tactics.append("payment redirection")
    
    # Build tactics summary
    if tactics:
        notes_parts.append(f"Scammer used {', '.join(tactics)}")
    else:
        notes_parts.append("Scam attempt detected")
    
    # Summarize collected intel
    collected = []
    bank_count = len(intel.get("bankAccounts", []))
    upi_count = len(intel.get("upiIds", []))
    phone_count = len(intel.get("phoneNumbers", []))
    link_count = len(intel.get("phishingLinks", []))
    
    if bank_count > 0:
        collected.append(f"{bank_count} bank account(s)")
    if upi_count > 0:
        collected.append(f"{upi_count} UPI ID(s)")
    if phone_count > 0:
        collected.append(f"{phone_count} phone number(s)")
    if link_count > 0:
        collected.append(f"{link_count} phishing link(s)")
    
    if collected:
        notes_parts.append(f"Extracted: {', '.join(collected)}")
    
    return ". ".join(notes_parts) + "."

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
            "upiIds": normalize_upi_ids(intel.get("upiIds", [])),
            "phishingLinks": normalize_phishing_links(intel.get("phishingLinks", [])),
            "phoneNumbers": normalize_phone_numbers(intel.get("phoneNumbers", [])),
            "suspiciousKeywords": normalize_keywords(intel.get("suspiciousKeywords", []))
        },
        "agentNotes": generate_agent_notes(intel)
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
