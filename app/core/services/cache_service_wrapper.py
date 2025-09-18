"""
Cache Service Wrapper

Wraps the existing CacheService to implement the Service interface
and integrate with the service registry.
"""

from typing import Dict, Any, List, Optional

from app.core.service import ConfigurableService
from app.services.cache_service import CacheService as OriginalCacheService, CacheConfig


class CacheService(ConfigurableService):
    """
    Cache service wrapper that implements the Service interface.
    
    This service wraps the existing CacheService implementation to provide
    integration with the service registry and dependency injection system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the cache service.
        
        Args:
            config: Cache service configuration
        """
        super().__init__(config, "cache")
        self._dependencies = ["config", "logger"]
        
        # Configuration with defaults
        self.backend = self.get_config("backend", "memory")
        self.default_ttl_seconds = self.get_config("default_ttl_seconds", 3600)
        self.max_size_mb = self.get_config("max_size_mb", 100)
        self.cleanup_interval_seconds = self.get_config("cleanup_interval_seconds", 300)
        self.redis_config = self.get_config("redis_config", {})
        
        # Internal state
        self._cache_service: Optional[OriginalCacheService] = None
        self._cache_config: Optional[CacheConfig] = None
    
    def _do_initialize(self) -> None:
        """Initialize the cache service."""
        # Create cache configuration
        self._cache_config = CacheConfig(
            ttl_seconds=self.default_ttl_seconds,
            max_size_mb=self.max_size_mb,
            eviction_policy="least-recently-used",
            enable_compression=True,
            enable_stats=True
        )
        
        # Get settings from config service (if available)
        try:
            from app.core.registry import get_registry
            registry = get_registry()
            
            if registry.has("config"):
                config_service = registry.get("config")
                settings = config_service.get_settings()
            else:
                # Fallback to loading settings directly
                from app.config import load_settings
                settings = load_settings()
        except Exception as e:
            self._logger.warning(f"Could not get settings from config service: {e}")
            from app.config import load_settings
            settings = load_settings()
        
        # Initialize the original cache service
        self._cache_service = OriginalCacheService(settings, self._cache_config)
        
        self._logger.info(f"Cache service initialized with backend: {self.backend}")
    
    def _do_shutdown(self) -> None:
        """Shutdown the cache service."""
        if self._cache_service:
            # The original cache service doesn't have explicit shutdown,
            # but we can clear the cache
            try:
                # Clear all namespaces (this is async, so we'll skip for now)
                pass
            except Exception as e:
                self._logger.warning(f"Error during cache shutdown: {e}")
        
        self._logger.info("Cache service shut down")
    
    def _do_health_check(self) -> bool:
        """Check if the cache service is healthy."""
        if not self._cache_service:
            return False
        
        try:
            # Try to get cache stats as a health check
            stats = self._cache_service.get_stats()
            return stats is not None
        except Exception:
            return False
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            Cached value or None if not found
        """
        if not self._cache_service:
            return None
        
        return await self._cache_service.get(key, namespace)
    
    async def set(self, key: str, value: Any, namespace: str = "default", 
                  ttl_seconds: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            namespace: Cache namespace
            ttl_seconds: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self._cache_service:
            return False
        
        return await self._cache_service.set(key, value, namespace, ttl_seconds)
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            True if successful, False otherwise
        """
        if not self._cache_service:
            return False
        
        return await self._cache_service.delete(key, namespace)
    
    def exists(self, key: str, namespace: str = "default") -> bool:
        """
        Check if key exists in cache (synchronous approximation).
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            True if key likely exists, False otherwise
        """
        # This is a synchronous approximation - in practice you'd want to
        # implement proper async support throughout the service registry
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't use run_until_complete in running loop
                return False
            else:
                result = loop.run_until_complete(self.get(key, namespace))
                return result is not None
        except Exception:
            return False
    
    async def clear(self, namespace: str = "default") -> bool:
        """
        Clear all cache entries in a namespace.
        
        Args:
            namespace: Namespace to clear
            
        Returns:
            True if successful, False otherwise
        """
        if not self._cache_service:
            return False
        
        return await self._cache_service.clear_namespace(namespace)
    
    def keys(self, pattern: Optional[str] = None, namespace: str = "default") -> List[str]:
        """
        Get all keys matching pattern (placeholder implementation).
        
        Args:
            pattern: Pattern to match (not implemented in original service)
            namespace: Cache namespace
            
        Returns:
            List of keys (empty for now)
        """
        # The original cache service doesn't expose key listing
        # This would need to be implemented in the underlying cache
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self._cache_service:
            return {
                "initialized": False,
                "backend": self.backend,
                "max_size_mb": self.max_size_mb
            }
        
        try:
            original_stats = self._cache_service.get_stats()
            return {
                "initialized": True,
                "backend": self.backend,
                "max_size_mb": self.max_size_mb,
                "default_ttl_seconds": self.default_ttl_seconds,
                "hits": original_stats.hits,
                "misses": original_stats.misses,
                "hit_rate": original_stats.hit_rate,
                "size_bytes": original_stats.size_bytes,
                "evictions": original_stats.evictions
            }
        except Exception as e:
            self._logger.warning(f"Failed to get cache stats: {e}")
            return {
                "initialized": True,
                "backend": self.backend,
                "error": str(e)
            }
    
    def cache_decorator(self, namespace: str = "default", ttl_seconds: Optional[int] = None):
        """
        Get cache decorator for function results.
        
        Args:
            namespace: Cache namespace
            ttl_seconds: Time to live in seconds
            
        Returns:
            Decorator function
        """
        if not self._cache_service:
            # Return a no-op decorator if cache service not available
            def no_op_decorator(func):
                return func
            return no_op_decorator
        
        return self._cache_service.cache_decorator(namespace, ttl_seconds)