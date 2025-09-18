"""Comprehensive caching service for expensive operations."""

import hashlib
import json
import time
from typing import Any, Dict, Optional, Union, Callable, TypeVar, Generic
from functools import wraps
from dataclasses import dataclass
from datetime import datetime, timedelta

import redis
from diskcache import Cache
from loguru import logger

from app.config import Settings
from app.utils.imports import require_service

T = TypeVar('T')

@dataclass
class CacheConfig:
    """Configuration for cache behavior."""
    ttl_seconds: int = 3600  # 1 hour default
    max_size_mb: int = 100   # 100MB default
    eviction_policy: str = "least-recently-used"
    enable_compression: bool = True
    enable_stats: bool = True

@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class CacheService:
    """Multi-layer caching service with Redis and disk cache fallback."""
    
    def __init__(self, settings: Settings, config: Optional[CacheConfig] = None) -> None:
        """Initialize cache service.
        
        Args:
            settings: Application settings
            config: Cache configuration
        """
        self.settings = settings
        self.config = config or CacheConfig()
        self._stats = CacheStats()
        
        # Get logger from service registry
        self.logger = require_service('logger', context='CacheService')
        
        # Initialize Redis cache (L1)
        self._redis_cache: Optional[redis.Redis] = None
        self._init_redis_cache()
        
        # Initialize disk cache (L2)
        self._disk_cache = Cache(
            directory="cache/l2_cache",
            size_limit=self.config.max_size_mb * 1024 * 1024,
            eviction_policy=self.config.eviction_policy
        )
        
        self.logger.info(f"Initialized cache service with Redis: {self._redis_cache is not None}")
    
    def _init_redis_cache(self) -> None:
        """Initialize Redis cache if available."""
        try:
            redis_url = getattr(self.settings, 'redis_url', None) or "redis://localhost:6379"
            self._redis_cache = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self._redis_cache.ping()
            self.logger.info("Redis cache initialized successfully")
        except Exception as e:
            self.logger.warning(f"Redis cache unavailable, using disk cache only: {e}")
            self._redis_cache = None
    
    def _make_cache_key(self, key: str, namespace: str = "default") -> str:
        """Create a standardized cache key.
        
        Args:
            key: Base key
            namespace: Cache namespace
            
        Returns:
            Standardized cache key
        """
        # Hash long keys to avoid Redis key length limits
        if len(key) > 200:
            key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
            key = f"hash_{key_hash}"
        
        return f"aaa:{namespace}:{key}"
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            Cached value or None if not found
        """
        cache_key = self._make_cache_key(key, namespace)
        
        try:
            # Try Redis first (L1)
            if self._redis_cache:
                try:
                    value = self._redis_cache.get(cache_key)
                    if value is not None:
                        self._stats.hits += 1
                        self.logger.debug(f"Cache hit (Redis): {cache_key}")
                        return json.loads(value)
                except Exception as e:
                    self.logger.warning(f"Redis cache error: {e}")
            
            # Try disk cache (L2)
            value = self._disk_cache.get(cache_key)
            if value is not None:
                self._stats.hits += 1
                self.logger.debug(f"Cache hit (Disk): {cache_key}")
                
                # Promote to Redis if available
                if self._redis_cache:
                    try:
                        self._redis_cache.setex(
                            cache_key,
                            self.config.ttl_seconds,
                            json.dumps(value)
                        )
                    except Exception:
                        pass  # Ignore Redis promotion errors
                
                return value
            
            # Cache miss
            self._stats.misses += 1
            self.logger.debug(f"Cache miss: {cache_key}")
            return None
            
        except Exception as e:
            self.logger.error(f"Cache get error for {cache_key}: {e}")
            self._stats.misses += 1
            return None
    
    async def set(self, key: str, value: Any, namespace: str = "default", 
                  ttl_seconds: Optional[int] = None) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            namespace: Cache namespace
            ttl_seconds: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._make_cache_key(key, namespace)
        ttl = ttl_seconds or self.config.ttl_seconds
        
        try:
            serialized_value = json.dumps(value)
            
            # Set in Redis (L1)
            if self._redis_cache:
                try:
                    self._redis_cache.setex(cache_key, ttl, serialized_value)
                    self.logger.debug(f"Cache set (Redis): {cache_key}")
                except Exception as e:
                    self.logger.warning(f"Redis cache set error: {e}")
            
            # Set in disk cache (L2)
            self._disk_cache.set(cache_key, value, expire=ttl)
            self.logger.debug(f"Cache set (Disk): {cache_key}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cache set error for {cache_key}: {e}")
            return False
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._make_cache_key(key, namespace)
        
        try:
            # Delete from Redis
            if self._redis_cache:
                try:
                    self._redis_cache.delete(cache_key)
                except Exception as e:
                    self.logger.warning(f"Redis cache delete error: {e}")
            
            # Delete from disk cache
            self._disk_cache.delete(cache_key)
            self.logger.debug(f"Cache delete: {cache_key}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cache delete error for {cache_key}: {e}")
            return False
    
    async def clear_namespace(self, namespace: str) -> bool:
        """Clear all keys in a namespace.
        
        Args:
            namespace: Namespace to clear
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pattern = f"aaa:{namespace}:*"
            
            # Clear from Redis
            if self._redis_cache:
                try:
                    keys = self._redis_cache.keys(pattern)
                    if keys:
                        self._redis_cache.delete(*keys)
                        self.logger.info(f"Cleared {len(keys)} Redis keys for namespace {namespace}")
                except Exception as e:
                    self.logger.warning(f"Redis namespace clear error: {e}")
            
            # Clear from disk cache (more complex due to DiskCache API)
            keys_to_delete = []
            for key in self._disk_cache:
                if key.startswith(f"aaa:{namespace}:"):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                self._disk_cache.delete(key)
            
            self.logger.info(f"Cleared {len(keys_to_delete)} disk cache keys for namespace {namespace}")
            return True
            
        except Exception as e:
            self.logger.error(f"Cache namespace clear error for {namespace}: {e}")
            return False
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        # Update size from disk cache
        try:
            self._stats.size_bytes = self._disk_cache.volume()
        except Exception:
            pass
        
        return self._stats
    
    def cache_decorator(self, namespace: str = "default", ttl_seconds: Optional[int] = None):
        """Decorator for caching function results.
        
        Args:
            namespace: Cache namespace
            ttl_seconds: Time to live in seconds
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                # Create cache key from function name and arguments
                key_data = {
                    'func': func.__name__,
                    'args': str(args),
                    'kwargs': sorted(kwargs.items())
                }
                cache_key = hashlib.sha256(str(key_data).encode()).hexdigest()
                
                # Try to get from cache
                cached_result = await self.get(cache_key, namespace)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                if hasattr(func, '__call__') and hasattr(func, '__await__'):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                await self.set(cache_key, result, namespace, ttl_seconds)
                return result
            
            return wrapper
        return decorator

# Global cache service instance
_cache_service: Optional[CacheService] = None

def get_cache_service(settings: Optional[Settings] = None) -> CacheService:
    """Get global cache service instance.
    
    Args:
        settings: Application settings
        
    Returns:
        Cache service instance
    """
    global _cache_service
    
    if _cache_service is None:
        if settings is None:
            from app.config import load_settings
            settings = load_settings()
        
        _cache_service = CacheService(settings)
    
    return _cache_service

# Convenience decorators
def cache_expensive_operation(namespace: str = "expensive", ttl_seconds: int = 3600):
    """Decorator for caching expensive operations.
    
    Args:
        namespace: Cache namespace
        ttl_seconds: Time to live in seconds (default 1 hour)
    """
    cache_service = get_cache_service()
    return cache_service.cache_decorator(namespace, ttl_seconds)

def cache_llm_response(ttl_seconds: int = 1800):
    """Decorator for caching LLM responses.
    
    Args:
        ttl_seconds: Time to live in seconds (default 30 minutes)
    """
    return cache_expensive_operation("llm_responses", ttl_seconds)

def cache_pattern_match(ttl_seconds: int = 7200):
    """Decorator for caching pattern matching results.
    
    Args:
        ttl_seconds: Time to live in seconds (default 2 hours)
    """
    return cache_expensive_operation("pattern_matches", ttl_seconds)