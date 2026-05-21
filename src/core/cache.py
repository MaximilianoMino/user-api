"""Simple TTL cache for async functions."""

import time
from typing import Any, Callable, Dict, Optional, Tuple


class TTLCache:
    """Thread-safe TTL cache with simple dict backend."""

    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None

        if time.time() > entry["expires_at"]:
            del self._cache[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        expires_at = time.time() + (ttl if ttl is not None else self.default_ttl)
        self._cache[key] = {"value": value, "expires_at": expires_at}

    def invalidate(self, key: str) -> None:
        """Remove specific key from cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)


# Global cache instances
user_cache = TTLCache(default_ttl=300)  # 5 minutes
org_cache = TTLCache(default_ttl=300)  # 5 minutes
lote_cache = TTLCache(default_ttl=60)  # 1 minute


def cache_key_user(token: str) -> str:
    return f"user:{token}"


def cache_key_org(user_id: int, org_id: int) -> str:
    return f"org:{user_id}:{org_id}"


def cache_key_lote(org_id: int, lote_id: str) -> str:
    return f"lote:{org_id}:{lote_id}"
