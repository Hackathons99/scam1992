"""
Execution Context for request-scoped data.
Uses ContextVar for async-safe, per-request isolation.

Only stores: session_id and message_count (needed by tools during execution).
Intel accumulation is handled by session_intel_store.py instead.
"""
from contextvars import ContextVar
from typing import Dict, Any

# Request-scoped context
session_context: ContextVar[Dict[str, Any]] = ContextVar("session_context", default={})

def get_session_id() -> str:
    return session_context.get().get("session_id", "")

def get_message_count() -> int:
    return session_context.get().get("message_count", 0)

def get_metadata() -> Dict[str, Any]:
    return session_context.get().get("metadata", {})
