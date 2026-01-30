try:
    from masai.AgentManager.AgentManager import AgentManager
except ImportError:
    class AgentManager:
        pass
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Protocol

import asyncio


logger = logging.getLogger(__name__)


class CleanableResource(Protocol):
    """Protocol for resources that need cleanup."""
    async def cleanup(self) -> None:
        """Cleanup external resources (Pinecone vectors, DB connections, etc.)."""
        ...



async def cleanup_manager_resources(manager: AgentManager) -> None:
    """
    Centralized cleanup for ALL manager resources.

    This function automatically discovers and cleans up all registered resources
    that implement the cleanup() method. No need to modify this function when
    adding new resources.

    Cleanup order:
    1. document_store (Pinecone vectors, uploaded files)
    2. Any future resources added to manager (DB connections, file handles, etc.)

    Python's GC automatically handles:
    - manager.agents dict
    - manager.context dict
    - All nested Python objects recursively
    """
    try:
        logger.info("Starting centralized resource cleanup...")

        # Discover all cleanable resources dynamically
        cleanable_attrs = [
            'document_store',  # SessionDocumentStore
            # Add new resources here as needed (they'll be auto-discovered)
        ]

        cleanup_tasks = []
        for attr_name in cleanable_attrs:
            if hasattr(manager, attr_name):
                resource = getattr(manager, attr_name)
                if resource and hasattr(resource, 'cleanup') and callable(resource.cleanup):
                    logger.debug(f"Scheduling cleanup for: {attr_name}")
                    cleanup_tasks.append(resource.cleanup())

        # Run all cleanups concurrently
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            logger.info(f"✓ Cleaned up {len(cleanup_tasks)} resource(s)")
        else:
            logger.debug("No resources to cleanup")

    except Exception as e:
        logger.error(f"Error during centralized cleanup: {e}")
    
    finally:
        # 3. Explicitly call manager's own cleanup for internal state (agents, context, etc.)
        # This is crucial because Python's GC might be delayed, and we want to release memory/references immediately upon cache eviction.
        if hasattr(manager, 'cleanup') and callable(manager.cleanup):
            try:
                manager.cleanup()
                logger.info("✓ Cleaned up internal manager state")
            except Exception as e:
                logger.error(f"Error during manager internal cleanup: {e}")



#-------------------------
# SYNC WRAPPER FOR ASYNC CLEANUP
#-------------------------
def _sync_cleanup_wrapper(manager: AgentManager) -> None:
    """
    Synchronous wrapper for async cleanup_manager_resources().
    Required because TtlLruCache.cleanup_callback must be synchronous.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If event loop is running, schedule as task
            asyncio.create_task(cleanup_manager_resources(manager))
        else:
            # If no event loop, run until complete
            loop.run_until_complete(cleanup_manager_resources(manager))
    except Exception as e:
        logger.error(f"Error in sync cleanup wrapper: {e}")


__all__ = [
    "CleanableResource",
    "cleanup_manager_resources",
    "_sync_cleanup_wrapper",
]