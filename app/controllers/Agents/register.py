from __future__ import annotations
from typing import Callable, Dict, Optional, Any
import logging

try:
    from masai.AgentManager.AgentManager import AgentManager
except ImportError:
    class AgentManager:
        def __init__(self, **kwargs): 
            self.agents = {}
            self.context = kwargs.get('context', {})
        def create_agent(self, **kwargs):
            name = kwargs.get('agent_name')
            print(f"[Mock] Creating agent: {name}")
            # Minimal mock agent
            class MockAgent:
                def __init__(self, name): self.name = name
                async def initiate_agent(self, query, passed_from=None):
                    # Simulate tool usage for testing
                    query_lower = query.lower()
                    if "bank" in query_lower or "upi" in query_lower:
                        print(f"[{self.name} Mock Agent] Detected scam potential. *Trigggering save_scam_intel*")
                        try:
                            from app.controllers.Agents.Tools.scam_extraction_tools import save_scam_intel
                            
                            banks = ["MOCK-BANK-456"] if "bank" in query_lower else []
                            upis = ["mock@upi"] if "upi" in query_lower else []
                            
                            if hasattr(save_scam_intel, 'func'):
                                save_scam_intel.func(bank_accounts=banks, upi_ids=upis, scam_score=90)
                            else:
                                save_scam_intel(bank_accounts=banks, upi_ids=upis, scam_score=90)
                        except Exception as e:
                            print(f"[Mock Agent] Tool call failed: {e}")
                            
                    return f"[Mock Response from {self.name}] Analysis complete for turn."
            self.agents[name] = MockAgent(name)
        def get_agent(self, name):
            return self.agents.get(name)
        def cleanup(self):
            print("[Mock] Cleanup called")

from app.controllers.Agents.HONEYPOT.honeypot_agent import create_honeypot_agent
from app.controllers.Agents.utils.cleanupAgentResources import _sync_cleanup_wrapper
from app.controllers.Agents.utils.ttl_lruCache import TtlLruCache
from app.models.context import UserContext

logger = logging.getLogger(__name__)

# Agent factories
AgentFactory = Callable[[AgentManager], Any]

_AGENT_FACTORIES: Dict[str, AgentFactory] = {
    "HONEYPOT": create_honeypot_agent,
}

_MANAGER_CACHE = TtlLruCache(
    maxsize=100,
    ttl_seconds=3600,
    cleanup_callback=_sync_cleanup_wrapper  # Centralized cleanup on expiry
)



def get_or_create_manager(ctx: UserContext) -> AgentManager:
    """
    Create a lightweight AgentManager per user context, cached with TTL.

    When the manager expires (30 min TTL) or is evicted (LRU maxsize=100),
    the cache automatically cleans up external resources (Pinecone vectors).

    Python's GC automatically frees all Python objects (agents, context, DataFrame).
    """
    
    # We maintain one manager per session to ensure continuity.
    # The key is derived primarily from the unique session_id.
    # Metadata can be part of the key if it defines the agent's configuration (e.g. language).
    # For now, we assume one manager per session_id is sufficient.
    key = ctx.session_id
    manager = _MANAGER_CACHE.get(key)

    if manager is None:
        # Create new AgentManager
        try:
            manager = AgentManager(
                logging=True,
                context=ctx.to_dict(),
                model_config_path="model_config/model_config.json",
            )
        except Exception:
            # Fallback if model_config isn't present
            manager = AgentManager(
                logging=True,
                context=ctx.to_dict(),
            )

        _MANAGER_CACHE.set(key, manager)
        logger.info(f"Created new AgentManager for session {ctx.session_id}")
    else:
        # Keep manager context updated (e.g., new namespaces/features)
        try:
            manager.context.update(ctx.to_dict())
        except Exception:
            pass

    return manager


def ensure_agent(
    agent_type: str,
    ctx: UserContext,
):
    """Ensure the agent for this user exists on the user's manager; return the agent.
    agent_config: optional per-agent overrides.
    """
    mgr = get_or_create_manager(ctx)

    factory = _AGENT_FACTORIES.get(agent_type)
    if not factory:
        raise ValueError(f"Unknown agent_type '{agent_type}'. Register it in _AGENT_FACTORIES.")

    # Create the agent idempotently via factory
    return factory(mgr)




# -----------------------------
# Maintenance helpers
# -----------------------------

def expire_session_manager(session_id: str) -> None:
    """
    Explicitly expire a session's AgentManager from cache.
    """
    key = session_id
    _MANAGER_CACHE.delete(key)
    logger.info(f"Expired AgentManager for session {session_id}")

async def cleanup_managers_background_task(interval_seconds: int = 180):
    """
    Background task: periodically sweep expired managers from cache.

    This function is called by the FastAPI lifespan handler.
    It runs continuously in the background, sweeping expired managers
    every `interval_seconds` seconds.

    The actual cleanup is handled by cleanup_manager_resources() which
    automatically discovers and cleans up all registered resources.
    """
    logger.info(f"🚀 AgentManager cleanup task started (interval={interval_seconds}s)")
    while True:
        try:
            expired_count = len([k for k, (ts, _) in _MANAGER_CACHE._store.items()
                                if _MANAGER_CACHE._is_expired(ts)])
            if expired_count > 0:
                logger.info(f"🧹 Sweeping {expired_count} expired AgentManager(s)...")
            _MANAGER_CACHE.sweep()
        except Exception as e:
            logger.error(f"❌ Error during cache sweep: {e}")
        await asyncio.sleep(interval_seconds)


__all__ = [
    "get_or_create_manager",
    "ensure_agent",
    "expire_user_manager",
    "cleanup_managers_background_task",
]
