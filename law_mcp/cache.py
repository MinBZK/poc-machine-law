"""
Caching system for MCP law execution server.
Provides in-memory caching with TTL to improve performance.
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with TTL support"""

    value: Any
    expires_at: float

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class TTLCache:
    """Thread-safe TTL cache with automatic cleanup"""

    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Get value from cache if not expired"""
        async with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired:
                logger.debug(f"Cache hit for key: {key}")
                return entry.value
            elif entry:
                # Remove expired entry
                del self._cache[key]
                logger.debug(f"Cache miss (expired) for key: {key}")
            else:
                logger.debug(f"Cache miss for key: {key}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with TTL"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl

        async with self._lock:
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
            logger.debug(f"Cache set for key: {key} (TTL: {ttl}s)")

    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            logger.debug("Cache cleared")

    async def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed"""
        async with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired]
            for key in expired_keys:
                del self._cache[key]
            logger.debug(f"Removed {len(expired_keys)} expired cache entries")
            return len(expired_keys)


def generate_cache_key(prefix: str, **kwargs) -> str:
    """Generate a consistent cache key from parameters"""
    # Sort kwargs for consistent key generation
    sorted_kwargs = sorted(kwargs.items())
    key_data = f"{prefix}:{json.dumps(sorted_kwargs, sort_keys=True)}"
    return hashlib.md5(key_data.encode()).hexdigest()


# Global cache instance
law_cache = TTLCache(default_ttl=300)  # 5 minutes
