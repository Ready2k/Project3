"""
Centralized cache management for expensive operations.

This module provides caching capabilities for LLM calls, diagram generation,
and other expensive operations to improve performance.
"""

import time
import hashlib
import json
from typing import Any, Optional, Callable, Dict, Union, TypeVar
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import threading

from app.utils.result import Result
from app.utils.logger import app_logger


T = TypeVar('T')


class CacheStrategy(Enum):
    """Cache strategy options."""
    LRU = "lru"
    TTL = "ttl"
    LRU_TTL = "lru_ttl"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    timestamp: float
    access_count: int = 0
    last_access: float = 0.0
    ttl: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl
    
    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_access = time.time()


class CacheManager:
    """
    Centralized cache management with multiple strategies.
    
    Provides caching for expensive operations like LLM calls and diagram generation
    with configurable TTL, size limits, and eviction policies.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600.0, 
                 strategy: CacheStrategy = CacheStrategy.LRU_TTL):
        """
        Initialize the cache manager.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default time-to-live in seconds
            strategy: Cache eviction strategy
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.strategy = strategy
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                app_logger.debug(f"Cache entry expired: {key}")
                return None
            
            # Update access metadata
            entry.touch()
            self._hits += 1
            app_logger.debug(f"Cache hit: {key}")
            return entry.value
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Put a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live override
        """
        with self._lock:
            # Use provided TTL or default
            entry_ttl = ttl if ttl is not None else self.default_ttl
            
            # Create cache entry
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=entry_ttl
            )
            
            # Check if we need to evict entries
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_entries()
            
            self._cache[key] = entry
            app_logger.debug(f"Cache put: {key} (TTL: {entry_ttl}s)")
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if key was found and removed
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                app_logger.debug(f"Cache invalidated: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            app_logger.info("Cache cleared")
    
    def _evict_entries(self) -> None:
        """Evict entries based on the configured strategy."""
        if not self._cache:
            return
        
        entries_to_remove = max(1, len(self._cache) // 10)  # Remove 10% of entries
        
        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used entries
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].last_access
            )
        elif self.strategy == CacheStrategy.TTL:
            # Remove entries closest to expiration
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].timestamp + (x[1].ttl or self.default_ttl)
            )
        else:  # LRU_TTL
            # Combine LRU and TTL factors
            current_time = time.time()
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: (
                    x[1].last_access,  # LRU factor
                    x[1].timestamp + (x[1].ttl or self.default_ttl) - current_time  # TTL factor
                )
            )
        
        # Remove the selected entries
        for key, _ in sorted_entries[:entries_to_remove]:
            del self._cache[key]
            self._evictions += 1
        
        app_logger.debug(f"Evicted {entries_to_remove} cache entries")
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                app_logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 2),
                "evictions": self._evictions,
                "strategy": self.strategy.value,
                "default_ttl": self.default_ttl
            }
    
    def cached(self, ttl: Optional[float] = None, key_func: Optional[Callable] = None):
        """
        Decorator for caching function results.
        
        Args:
            ttl: Time-to-live override
            key_func: Custom key generation function
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.put(cache_key, result, ttl)
                return result
            
            return wrapper
        return decorator
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        Generate a cache key from function name and arguments.
        
        Args:
            func_name: Function name
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create a stable representation of arguments
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        
        # Convert to JSON and hash
        key_json = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.sha256(key_json.encode()).hexdigest()[:16]
        
        return f"{func_name}_{key_hash}"


# Global cache manager instance
_global_cache_manager: Optional[CacheManager] = None
_cache_lock = threading.Lock()


def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance.
    
    Returns:
        The global cache manager
    """
    global _global_cache_manager
    
    if _global_cache_manager is None:
        with _cache_lock:
            if _global_cache_manager is None:
                _global_cache_manager = CacheManager()
    
    return _global_cache_manager


def cached(ttl: Optional[float] = None, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results using the global cache manager.
    
    Args:
        ttl: Time-to-live override
        key_func: Custom key generation function
        
    Returns:
        Decorator function
    """
    cache_manager = get_cache_manager()
    return cache_manager.cached(ttl=ttl, key_func=key_func)


def cache_result(key: str, value: Any, ttl: Optional[float] = None) -> None:
    """
    Cache a result using the global cache manager.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time-to-live override
    """
    cache_manager = get_cache_manager()
    cache_manager.put(key, value, ttl)


def get_cached_result(key: str) -> Optional[Any]:
    """
    Get a cached result using the global cache manager.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None
    """
    cache_manager = get_cache_manager()
    return cache_manager.get(key)


def invalidate_cache(key: str) -> bool:
    """
    Invalidate a cache entry using the global cache manager.
    
    Args:
        key: Cache key to invalidate
        
    Returns:
        True if key was found and removed
    """
    cache_manager = get_cache_manager()
    return cache_manager.invalidate(key)


def clear_cache() -> None:
    """Clear all cache entries using the global cache manager."""
    cache_manager = get_cache_manager()
    cache_manager.clear()


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics using the global cache manager.
    
    Returns:
        Dictionary with cache statistics
    """
    cache_manager = get_cache_manager()
    return cache_manager.get_stats()