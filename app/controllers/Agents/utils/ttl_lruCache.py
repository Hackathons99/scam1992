from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple
import time

class TtlLruCache:
    """Simple in-process TTL + LRU cache for arbitrary Python objects.
    - Expiration is enforced on get/set; optional sweep() can proactively prune.
    - LRU is approximated by updating timestamp on get/set and evicting the oldest.
    - Supports custom cleanup callback for values that don't have cleanup() method.
    """

    def __init__(
        self,
        maxsize: int = 100,
        ttl_seconds: int = 1800,
        cleanup_callback: Optional[Callable[[Any], None]] = None
    ):
        self.maxsize = maxsize
        self.ttl = ttl_seconds
        self.cleanup_callback = cleanup_callback
        self._store: Dict[Any, Tuple[float, Any]] = {}

    def _is_expired(self, ts: float) -> bool:
        return (time.time() - ts) > self.ttl

    def get(self, key: Any) -> Any:
        item = self._store.get(key)
        if not item:
            return None
        ts, value = item
        if self._is_expired(ts):
            # Call cleanup if value has cleanup method
            self._cleanup_value(value)
            self._store.pop(key, None)
            return None
        # touch
        self._store[key] = (time.time(), value)
        return value

    def set(self, key: Any, value: Any) -> None:
        # prune expired
        self.sweep()
        # evict if needed
        if len(self._store) >= self.maxsize:
            oldest_key = min(self._store.items(), key=lambda kv: kv[1][0])[0]
            oldest_value = self._store[oldest_key][1]
            # Call cleanup if value has cleanup method
            self._cleanup_value(oldest_value)
            self._store.pop(oldest_key, None)
        self._store[key] = (time.time(), value)

    def delete(self, key: Any) -> None:
        item = self._store.get(key)
        if item:
            # Call cleanup if value has cleanup method
            self._cleanup_value(item[1])
        self._store.pop(key, None)

    def clear(self) -> None:
        # Call cleanup on all values
        for _, value in self._store.values():
            self._cleanup_value(value)
        self._store.clear()

    def sweep(self) -> None:
        """Remove all expired entries proactively."""
        now = time.time()
        expired_keys = [k for k, (ts, _) in self._store.items() if (now - ts) > self.ttl]
        for k in expired_keys:
            item = self._store.get(k)
            if item:
                # Call cleanup if value has cleanup method
                self._cleanup_value(item[1])
            self._store.pop(k, None)

    def _cleanup_value(self, value: Any) -> None:
        """
        Internal helper to clean up a value when it is removed from the cache.
        This is called during:
        - get() if item is expired
        - set() if cache is full (LRU eviction)
        - delete() explicit removal
        - clear() removal of all items
        - sweep() removal of expired items

        Cleanup Order (Dual-Safety):
        1. FIRST calls `cleanup_callback` (if provided). This allows an external orchestrator
           (like cleanupAgentResources) to handle complex, async, or aggregated cleanup logic.
        2. THEN calls `value.cleanup()` (if available). This ensures that even if the callback
           misses something, the object is given a chance to free its own internal resources.
        
        This redundancy ensures "full responsibility" is taken by the cache to free resources,
        while the callback acts as an enhanced safety layer for external dependencies.
        """
        try:
            if self.cleanup_callback:
                # Use custom cleanup callback (External Orchestrator)
                self.cleanup_callback(value)
            
            if hasattr(value, 'cleanup') and callable(value.cleanup):
                # Call value's native cleanup method (Internal Responsibility)
                value.cleanup()
            
            # else: No cleanup needed - Python's GC handles it
        except Exception as e:
            # Don't fail cache operations due to cleanup errors
            print(f"Warning: Error during value cleanup: {e}")

