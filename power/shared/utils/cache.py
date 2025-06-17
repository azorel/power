"""
Response cache utility for adapters.
Provides thread-safe caching with TTL and size limits.
"""

import time
import threading
import hashlib
import json
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import OrderedDict


@dataclass
class CacheEntry:  # pylint: disable=too-many-instance-attributes
    """Individual cache entry with metadata."""

    value: Any
    created_at: float
    ttl_seconds: int
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.ttl_seconds <= 0:  # Never expires
            return False
        return time.time() - self.created_at > self.ttl_seconds

    @property
    def expires_at(self) -> datetime:
        """Get expiration datetime."""
        if self.ttl_seconds <= 0:
            return datetime.max
        return datetime.fromtimestamp(self.created_at + self.ttl_seconds)

    def access(self) -> Any:
        """Record access and return value."""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value


@dataclass
class CacheStats:  # pylint: disable=too-many-instance-attributes
    """Cache performance statistics."""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    expired_entries: int = 0

    current_size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary format."""
        return {
            'total_requests': self.total_requests,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'evictions': self.evictions,
            'expired_entries': self.expired_entries,
            'current_size': self.current_size,
            'max_size': self.max_size,
            'hit_rate': self.hit_rate,
            'miss_rate': self.miss_rate
        }


class ResponseCache:
    """
    Thread-safe response cache with TTL and LRU eviction.
    Designed for caching API responses to reduce external calls.
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: int = 3600,
        cleanup_interval_seconds: int = 300
    ):
        """
        Initialize response cache.

        Args:
            max_size: Maximum number of entries to store
            default_ttl_seconds: Default time-to-live for entries
            cleanup_interval_seconds: How often to clean expired entries
        """
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds

        # Thread-safe storage
        self._lock = threading.RLock()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # Statistics
        self._stats = CacheStats(max_size=max_size)

        # Cleanup tracking
        self._last_cleanup = time.time()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            self._stats.total_requests += 1

            # Periodic cleanup
            self._maybe_cleanup()

            if key not in self._cache:
                self._stats.cache_misses += 1
                return None

            entry = self._cache[key]

            if entry.is_expired:
                # Remove expired entry
                del self._cache[key]
                self._stats.cache_misses += 1
                self._stats.expired_entries += 1
                return None

            # Move to end (most recently used) and record access
            self._cache.move_to_end(key)
            self._stats.cache_hits += 1

            return entry.access()

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live override (uses default if None)
        """
        with self._lock:
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds

            # Create new entry
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl_seconds=ttl
            )

            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]

            # Add new entry
            self._cache[key] = entry

            # Enforce size limit
            while len(self._cache) > self.max_size:
                # Remove least recently used item
                self._cache.popitem(last=False)
                self._stats.evictions += 1

            self._stats.current_size = len(self._cache)

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was found and deleted, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.current_size = len(self._cache)
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._stats.current_size = 0

    def has_key(self, key: str) -> bool:
        """Check if key exists in cache (doesn't check expiration)."""
        with self._lock:
            return key in self._cache

    def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        with self._lock:
            stats = CacheStats(
                total_requests=self._stats.total_requests,
                cache_hits=self._stats.cache_hits,
                cache_misses=self._stats.cache_misses,
                evictions=self._stats.evictions,
                expired_entries=self._stats.expired_entries,
                current_size=len(self._cache),
                max_size=self.max_size
            )
            return stats

    def get_keys(self) -> List[str]:
        """Get list of all cache keys."""
        with self._lock:
            return list(self._cache.keys())

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries with optimized performance.

        Returns:
            Number of entries removed
        """
        with self._lock:
            now = time.time()
            expired_keys = []

            # Optimize: Use list comprehension for better performance
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.ttl_seconds > 0 and now - entry.created_at > entry.ttl_seconds
            ]

            # Batch delete expired entries
            for key in expired_keys:
                del self._cache[key]

            # Update stats in batch
            removed_count = len(expired_keys)
            self._stats.expired_entries += removed_count
            self._stats.current_size = len(self._cache)
            self._last_cleanup = now

            return removed_count

    def _maybe_cleanup(self) -> None:
        """Run cleanup if enough time has passed."""
        current_time = time.time()
        if (current_time - self._last_cleanup) > self.cleanup_interval_seconds:
            # Optimize: only cleanup if cache is getting full
            if len(self._cache) > self.max_size * 0.7:
                self.cleanup_expired()
            else:
                # Just update the timestamp to avoid repeated checks
                self._last_cleanup = current_time


def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate a deterministic cache key from arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        SHA-256 hash of the serialized arguments
    """
    # Create deterministic representation
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())  # Sort for deterministic ordering
    }

    # Serialize to JSON (handles most common types)
    try:
        key_string = json.dumps(key_data, sort_keys=True, default=str)
    except (TypeError, ValueError):
        # Fallback to string representation if JSON fails
        key_string = str(key_data)

    # Generate hash
    return hashlib.sha256(key_string.encode('utf-8')).hexdigest()


class CacheDecorator:  # pylint: disable=too-few-public-methods
    """
    Decorator for caching function results.
    Useful for adapter methods that make expensive API calls.
    """

    def __init__(
        self,
        cache: ResponseCache,
        ttl_seconds: Optional[int] = None,
        key_func: Optional[Callable] = None
    ):
        """
        Initialize cache decorator.

        Args:
            cache: ResponseCache instance to use
            ttl_seconds: TTL override for cached results
            key_func: Custom function to generate cache keys
        """
        self.cache = cache
        self.ttl_seconds = ttl_seconds
        self.key_func = key_func or generate_cache_key

    def __call__(self, func: Callable) -> Callable:
        """Apply caching to function."""
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = self.key_func(func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Call function and cache result
            result = func(*args, **kwargs)
            self.cache.set(cache_key, result, self.ttl_seconds)

            return result

        return wrapper


# Global cache instance for adapters to use
_global_cache: Optional[ResponseCache] = None


def get_global_cache() -> ResponseCache:
    """Get or create global cache instance."""
    global _global_cache  # pylint: disable=global-statement
    if _global_cache is None:
        _global_cache = ResponseCache(
            max_size=1000,
            default_ttl_seconds=3600
        )
    return _global_cache


def cache_response(
    ttl_seconds: Optional[int] = None,
    key_func: Optional[Callable] = None
) -> Callable:
    """
    Decorator for caching method responses using global cache.

    Args:
        ttl_seconds: TTL override for cached results
        key_func: Custom function to generate cache keys

    Returns:
        Decorator function
    """
    cache = get_global_cache()
    decorator = CacheDecorator(cache, ttl_seconds, key_func)
    return decorator
