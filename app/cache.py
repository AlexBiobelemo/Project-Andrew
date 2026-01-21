"""
Simple in-memory caching system without external dependencies.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import threading


class SimpleCache:
    """
    A simple in-memory cache implementation without external dependencies.
    
    Features:
    - Thread-safe operations
    - Time-based expiration
    - Size-based eviction
    - Cache statistics
    """
    
    def __init__(self, max_size: int = 1000, default_timeout: int = 300):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of items to store in cache
            default_timeout: Default timeout in seconds for cache items
        """
        self.max_size = max_size
        self.default_timeout = default_timeout
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'sets': 0
        }
    
    def _cleanup(self) -> None:
        """Remove expired items from cache."""
        now = datetime.utcnow().timestamp()
        expired_keys = [
            key for key, item in self._cache.items() 
            if item['expires_at'] is not None and item['expires_at'] <= now
        ]
        
        for key in expired_keys:
            del self._cache[key]
    
    def _evict_if_needed(self) -> None:
        """Evict items if cache size exceeds maximum."""
        if len(self._cache) > self.max_size:
            # Simple LRU eviction: remove oldest items first
            sorted_items = sorted(
                self._cache.items(), 
                key=lambda x: x[1]['accessed_at']
            )
            
            while len(self._cache) > self.max_size:
                key, _ = sorted_items.pop(0)
                del self._cache[key]
                self._stats['evictions'] += 1
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get an item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            self._cleanup()
            
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            item = self._cache[key]
            
            # Check if expired
            if item['expires_at'] is not None and item['expires_at'] <= datetime.utcnow().timestamp():
                del self._cache[key]
                self._stats['misses'] += 1
                return None
            
            # Update access time
            item['accessed_at'] = datetime.utcnow().timestamp()
            self._stats['hits'] += 1
            
            return item['value']
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """
        Set an item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            timeout: Optional timeout in seconds (uses default if None)
        """
        with self._lock:
            expires_at = None
            if timeout is not None or self.default_timeout:
                timeout_val = timeout if timeout is not None else self.default_timeout
                expires_at = datetime.utcnow().timestamp() + timeout_val
            
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'accessed_at': datetime.utcnow().timestamp()
            }
            
            self._stats['sets'] += 1
            self._evict_if_needed()
    
    def delete(self, key: str) -> bool:
        """
        Delete an item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if item was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from cache."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        with self._lock:
            return {
                **self._stats,
                'current_size': len(self._cache),
                'max_size': self.max_size
            }
    
    def has(self, key: str) -> bool:
        """
        Check if a key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists and is not expired, False otherwise
        """
        with self._lock:
            self._cleanup()
            return key in self._cache


# Global cache instance
cache = SimpleCache(max_size=500, default_timeout=300)