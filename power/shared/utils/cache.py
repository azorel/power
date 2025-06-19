"""
Response Cache Utility

Simple in-memory cache for caching API responses and other data
with TTL (time-to-live) support.
"""

import time
import threading
from typing import Any, Optional, Dict
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Represents a cached entry with TTL."""
    value: Any
    expires_at: float
    created_at: float


class ResponseCache:
    """
    Thread-safe in-memory cache with TTL support.
    
    Used for caching API responses and other expensive operations.
    """
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        """
        Initialize the cache.
        
        Args:
            ttl_seconds: Time to live for cache entries in seconds
            max_size: Maximum number of entries to store
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return None
            
            # Check if expired
            if time.time() > entry.expires_at:
                del self._cache[key]
                return None
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Override default TTL for this entry
        """
        with self._lock:
            ttl = ttl_seconds or self.ttl_seconds
            now = time.time()
            
            entry = CacheEntry(
                value=value,
                expires_at=now + ttl,
                created_at=now
            )
            
            self._cache[key] = entry
            
            # Evict oldest entries if cache is full
            if len(self._cache) > self.max_size:
                self._evict_oldest()
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was found and deleted, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            now = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if now > entry.expires_at
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def _evict_oldest(self) -> None:
        """Evict oldest entries to make room."""
        if not self._cache:
            return
        
        # Find oldest entry by creation time
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        
        del self._cache[oldest_key]
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            now = time.time()
            expired_count = sum(
                1 for entry in self._cache.values()
                if now > entry.expires_at
            )
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'expired_entries': expired_count,
                'ttl_seconds': self.ttl_seconds
            }