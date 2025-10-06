"""
Performance optimization and caching system for advanced prompt defense.

This module provides caching, parallel processing, resource limits, and performance monitoring
to ensure the security validation system meets the <50ms latency target while maintaining
comprehensive protection.
"""

import asyncio
import time
import hashlib
import threading
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from functools import wraps
import weakref
import gc

# psutil is handled through service registry - no fallback imports needed

from app.security.attack_patterns import ProcessedInput, DetectionResult
from app.utils.logger import app_logger


@dataclass
class PerformanceMetrics:
    """Performance metrics for security validation."""
    total_validations: int = 0
    total_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    parallel_executions: int = 0
    sequential_executions: int = 0
    timeout_errors: int = 0
    memory_usage_mb: float = 0.0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    
    def update_latency(self, latency_ms: float) -> None:
        """Update latency statistics."""
        self.total_validations += 1
        self.total_time_ms += latency_ms
        self.avg_latency_ms = self.total_time_ms / self.total_validations
        self.max_latency_ms = max(self.max_latency_ms, latency_ms)
        self.min_latency_ms = min(self.min_latency_ms, latency_ms)
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.cache_misses += 1
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate as percentage."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0
    
    def update_memory_usage(self) -> None:
        """Update current memory usage."""
        # Memory monitoring handled through service registry
        pass


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    result: Any
    timestamp: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.timestamp > ttl_seconds
    
    def access(self) -> Any:
        """Access the cached result and update metadata."""
        self.access_count += 1
        self.last_access = time.time()
        return self.result


class LRUCache:
    """Thread-safe LRU cache with TTL and memory management."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.lock = threading.RLock()
        self._cleanup_counter = 0
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry.timestamp > self.ttl_seconds
        ]
        
        for key in expired_keys:
            self.cache.pop(key, None)
            if key in self.access_order:
                self.access_order.remove(key)
    
    def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        while len(self.cache) >= self.max_size and self.access_order:
            lru_key = self.access_order.pop(0)
            self.cache.pop(lru_key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            # Periodic cleanup
            self._cleanup_counter += 1
            if self._cleanup_counter % 100 == 0:
                self._cleanup_expired()
            
            entry = self.cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired(self.ttl_seconds):
                self.cache.pop(key, None)
                if key in self.access_order:
                    self.access_order.remove(key)
                return None
            
            # Update access order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            
            return entry.access()
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache."""
        with self.lock:
            # Remove existing entry if present
            if key in self.cache:
                self.access_order.remove(key)
            
            # Evict if necessary
            self._evict_lru()
            
            # Add new entry
            self.cache[key] = CacheEntry(
                result=value,
                timestamp=time.time()
            )
            self.access_order.append(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        with self.lock:
            return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_accesses = sum(entry.access_count for entry in self.cache.values())
            avg_access_count = total_accesses / len(self.cache) if self.cache else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds,
                'total_accesses': total_accesses,
                'avg_access_count': avg_access_count,
                'memory_usage_estimate': len(self.cache) * 1024  # Rough estimate
            }


class ResourceLimiter:
    """Resource limits and timeouts for validation processes."""
    
    def __init__(self, max_memory_mb: int = 512, max_cpu_percent: float = 80.0):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        # Resource monitoring handled through service registry
        self.process = None
    
    def check_memory_limit(self) -> bool:
        """Check if memory usage is within limits."""
        try:
            if self.process:
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                return memory_mb <= self.max_memory_mb
        except Exception:
            pass
        return True  # Assume OK if can't check
    
    def check_cpu_limit(self) -> bool:
        """Check if CPU usage is within limits."""
        try:
            if self.process:
                cpu_percent = self.process.cpu_percent()
                return cpu_percent <= self.max_cpu_percent
        except Exception:
            pass
        return True  # Assume OK if can't check
    
    def check_limits(self) -> Tuple[bool, str]:
        """Check all resource limits."""
        if not self.check_memory_limit():
            return False, f"Memory usage exceeds {self.max_memory_mb}MB limit"
        
        if not self.check_cpu_limit():
            return False, f"CPU usage exceeds {self.max_cpu_percent}% limit"
        
        return True, "Resource usage within limits"
    
    def get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage."""
        try:
            if self.process:
                memory_info = self.process.memory_info()
                return {
                    'memory_mb': memory_info.rss / 1024 / 1024,
                    'memory_percent': self.process.memory_percent(),
                    'cpu_percent': self.process.cpu_percent(),
                    'num_threads': self.process.num_threads()
                }
        except Exception as e:
            app_logger.warning(f"Failed to get resource usage: {e}")
        return {}


class PerformanceOptimizer:
    """Main performance optimization coordinator."""
    
    def __init__(self, 
                 cache_size: int = 1000,
                 cache_ttl: int = 300,
                 max_workers: int = 8,
                 timeout_ms: int = 100,
                 max_memory_mb: int = 512):
        
        self.cache = LRUCache(cache_size, cache_ttl)
        self.metrics = PerformanceMetrics()
        self.resource_limiter = ResourceLimiter(max_memory_mb)
        self.timeout_ms = timeout_ms
        
        # Thread pool for parallel processing
        self.executor = None
        try:
            self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="security-detector")
            app_logger.info(f"Created thread pool with {max_workers} workers")
        except Exception as e:
            app_logger.warning(f"Failed to create thread pool: {e}")
        
        # Performance monitoring
        self._monitoring_enabled = True
        self._alert_callbacks: List[Callable] = []
        
        # Weak references to avoid circular dependencies
        self._detector_refs: List[weakref.ref] = []
    
    def register_detector(self, detector) -> None:
        """Register a detector for performance monitoring."""
        self._detector_refs.append(weakref.ref(detector))
    
    def register_alert_callback(self, callback: Callable[[str, Dict], None]) -> None:
        """Register callback for performance alerts."""
        self._alert_callbacks.append(callback)
    
    def _generate_cache_key(self, input_text: str, detector_name: str, 
                          config_hash: str = "") -> str:
        """Generate stable cache key for input and detector combination."""
        # Create deterministic hash from input and detector
        content = f"{detector_name}:{input_text}:{config_hash}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:32]
    
    def _should_use_cache(self, input_text: str) -> bool:
        """Determine if caching should be used for this input."""
        # Don't cache very short inputs (likely test cases)
        if len(input_text) < 10:
            return False
        
        # Don't cache very long inputs (memory concerns)
        if len(input_text) > 10000:
            return False
        
        return True
    
    async def cached_detection(self, 
                             detector_func: Callable,
                             processed_input: ProcessedInput,
                             detector_name: str,
                             config_hash: str = "") -> DetectionResult:
        """Run detection with caching."""
        
        if not self._should_use_cache(processed_input.original_text):
            # Run without caching
            start_time = time.time()
            try:
                result = detector_func(processed_input)
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.update_latency(latency_ms)
                return result
            except Exception as e:
                app_logger.error(f"Detection error in {detector_name}: {e}")
                raise
        
        # Generate cache key
        cache_key = self._generate_cache_key(
            processed_input.original_text, 
            detector_name, 
            config_hash
        )
        
        # Try cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            self.metrics.record_cache_hit()
            app_logger.debug(f"Cache hit for {detector_name}")
            return cached_result
        
        # Cache miss - run detection
        self.metrics.record_cache_miss()
        start_time = time.time()
        
        try:
            result = detector_func(processed_input)
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.update_latency(latency_ms)
            
            # Cache the result
            self.cache.put(cache_key, result)
            
            app_logger.debug(f"Cache miss for {detector_name}, cached result")
            return result
            
        except Exception as e:
            app_logger.error(f"Detection error in {detector_name}: {e}")
            raise
    
    async def parallel_detection(self, 
                               detector_funcs: List[Tuple[Callable, str]],
                               processed_input: ProcessedInput,
                               config_hash: str = "") -> List[DetectionResult]:
        """Run multiple detectors in parallel with timeout and resource limits."""
        
        if not self.executor or len(detector_funcs) <= 1:
            # Fall back to sequential execution
            return await self._sequential_detection(detector_funcs, processed_input, config_hash)
        
        # Check resource limits before parallel execution
        within_limits, limit_msg = self.resource_limiter.check_limits()
        if not within_limits:
            app_logger.warning(f"Resource limits exceeded: {limit_msg}, falling back to sequential")
            return await self._sequential_detection(detector_funcs, processed_input, config_hash)
        
        self.metrics.parallel_executions += 1
        start_time = time.time()
        results = []
        
        # Submit all detection tasks
        future_to_detector = {}
        for detector_func, detector_name in detector_funcs:
            future = self.executor.submit(
                self._run_cached_detection_sync,
                detector_func,
                processed_input,
                detector_name,
                config_hash
            )
            future_to_detector[future] = detector_name
        
        # Collect results with timeout
        timeout_seconds = self.timeout_ms / 1000.0
        
        try:
            for future in as_completed(future_to_detector, timeout=timeout_seconds):
                detector_name = future_to_detector[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    app_logger.error(f"Parallel detection error in {detector_name}: {e}")
                    # Add error result
                    results.append(DetectionResult(
                        detector_name=detector_name,
                        is_attack=False,
                        confidence=0.0,
                        matched_patterns=[],
                        evidence=[f"Detector error: {str(e)}"],
                        suggested_action=None
                    ))
        
        except TimeoutError:
            self.metrics.timeout_errors += 1
            app_logger.warning(f"Parallel detection timeout after {timeout_seconds}s")
            
            # Cancel remaining futures
            for future in future_to_detector:
                future.cancel()
            
            # Add timeout results for missing detectors
            completed_detectors = {future_to_detector[f] for f in future_to_detector if f.done()}
            for _, detector_name in detector_funcs:
                if detector_name not in completed_detectors:
                    results.append(DetectionResult(
                        detector_name=detector_name,
                        is_attack=False,
                        confidence=0.0,
                        matched_patterns=[],
                        evidence=["Detection timeout"],
                        suggested_action=None
                    ))
        
        total_time_ms = (time.time() - start_time) * 1000
        app_logger.debug(f"Parallel detection completed in {total_time_ms:.2f}ms")
        
        return results
    
    async def _sequential_detection(self, 
                                  detector_funcs: List[Tuple[Callable, str]],
                                  processed_input: ProcessedInput,
                                  config_hash: str = "") -> List[DetectionResult]:
        """Run detectors sequentially as fallback."""
        self.metrics.sequential_executions += 1
        results = []
        
        for detector_func, detector_name in detector_funcs:
            try:
                result = await self.cached_detection(
                    detector_func, processed_input, detector_name, config_hash
                )
                results.append(result)
            except Exception as e:
                app_logger.error(f"Sequential detection error in {detector_name}: {e}")
                results.append(DetectionResult(
                    detector_name=detector_name,
                    is_attack=False,
                    confidence=0.0,
                    matched_patterns=[],
                    evidence=[f"Detector error: {str(e)}"],
                    suggested_action=None
                ))
        
        return results
    
    def _run_cached_detection_sync(self, 
                                 detector_func: Callable,
                                 processed_input: ProcessedInput,
                                 detector_name: str,
                                 config_hash: str = "") -> DetectionResult:
        """Synchronous wrapper for cached detection (for thread pool)."""
        
        if not self._should_use_cache(processed_input.original_text):
            return detector_func(processed_input)
        
        # Generate cache key
        cache_key = self._generate_cache_key(
            processed_input.original_text, 
            detector_name, 
            config_hash
        )
        
        # Try cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            self.metrics.record_cache_hit()
            return cached_result
        
        # Cache miss - run detection
        self.metrics.record_cache_miss()
        result = detector_func(processed_input)
        
        # Cache the result
        self.cache.put(cache_key, result)
        
        return result
    
    def monitor_performance(self) -> None:
        """Monitor performance and trigger alerts if needed."""
        if not self._monitoring_enabled:
            return
        
        # Update memory usage
        self.metrics.update_memory_usage()
        
        # Check for performance issues
        alerts = []
        
        if self.metrics.avg_latency_ms > 50:
            alerts.append({
                'type': 'high_latency',
                'message': f'Average latency {self.metrics.avg_latency_ms:.2f}ms exceeds 50ms target',
                'value': self.metrics.avg_latency_ms
            })
        
        if self.metrics.get_cache_hit_rate() < 30:
            alerts.append({
                'type': 'low_cache_hit_rate',
                'message': f'Cache hit rate {self.metrics.get_cache_hit_rate():.1f}% is low',
                'value': self.metrics.get_cache_hit_rate()
            })
        
        if self.metrics.timeout_errors > 0:
            alerts.append({
                'type': 'timeout_errors',
                'message': f'{self.metrics.timeout_errors} timeout errors detected',
                'value': self.metrics.timeout_errors
            })
        
        if self.metrics.memory_usage_mb > 400:  # 80% of 512MB limit
            alerts.append({
                'type': 'high_memory_usage',
                'message': f'Memory usage {self.metrics.memory_usage_mb:.1f}MB approaching limit',
                'value': self.metrics.memory_usage_mb
            })
        
        # Trigger alert callbacks
        for alert in alerts:
            for callback in self._alert_callbacks:
                try:
                    callback(alert['type'], alert)
                except Exception as e:
                    app_logger.error(f"Error in performance alert callback: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        cache_stats = self.cache.get_stats()
        resource_usage = self.resource_limiter.get_resource_usage()
        
        return {
            'validation_metrics': {
                'total_validations': self.metrics.total_validations,
                'avg_latency_ms': self.metrics.avg_latency_ms,
                'max_latency_ms': self.metrics.max_latency_ms,
                'min_latency_ms': self.metrics.min_latency_ms if self.metrics.min_latency_ms != float('inf') else 0,
                'timeout_errors': self.metrics.timeout_errors
            },
            'cache_metrics': {
                'hit_rate_percent': self.metrics.get_cache_hit_rate(),
                'total_hits': self.metrics.cache_hits,
                'total_misses': self.metrics.cache_misses,
                **cache_stats
            },
            'execution_metrics': {
                'parallel_executions': self.metrics.parallel_executions,
                'sequential_executions': self.metrics.sequential_executions,
                'parallel_ratio': (
                    self.metrics.parallel_executions / 
                    (self.metrics.parallel_executions + self.metrics.sequential_executions)
                    if (self.metrics.parallel_executions + self.metrics.sequential_executions) > 0 
                    else 0
                )
            },
            'resource_metrics': {
                'current_memory_mb': self.metrics.memory_usage_mb,
                **resource_usage
            },
            'system_status': {
                'thread_pool_active': self.executor is not None,
                'monitoring_enabled': self._monitoring_enabled,
                'cache_enabled': True,
                'timeout_ms': self.timeout_ms
            }
        }
    
    def optimize_cache(self) -> None:
        """Optimize cache performance by cleaning up and adjusting parameters."""
        try:
            # Force cleanup of expired entries
            with self.cache.lock:
                self.cache._cleanup_expired()
            
            # Trigger garbage collection if memory usage is high
            if self.metrics.memory_usage_mb > 300:
                gc.collect()
                app_logger.info("Triggered garbage collection for memory optimization")
            
            # Log optimization results
            cache_stats = self.cache.get_stats()
            app_logger.info(f"Cache optimization completed: {cache_stats['size']} entries")
            
        except Exception as e:
            app_logger.error(f"Error during cache optimization: {e}")
    
    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics = PerformanceMetrics()
        app_logger.info("Performance metrics reset")
    
    def clear_cache(self) -> None:
        """Clear all cached results."""
        self.cache.clear()
        app_logger.info("Performance cache cleared")
    
    def shutdown(self) -> None:
        """Shutdown the performance optimizer."""
        self._monitoring_enabled = False
        
        if self.executor:
            try:
                self.executor.shutdown(wait=True, timeout=5.0)
                app_logger.info("Thread pool executor shutdown completed")
            except Exception as e:
                app_logger.warning(f"Error during executor shutdown: {e}")
        
        self.cache.clear()


# Global performance optimizer instance
_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get the global performance optimizer instance."""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        optimizer = get_performance_optimizer()
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            optimizer.metrics.update_latency(latency_ms)
            
            # Monitor performance periodically
            if optimizer.metrics.total_validations % 100 == 0:
                optimizer.monitor_performance()
            
            return result
            
        except Exception:
            latency_ms = (time.time() - start_time) * 1000
            optimizer.metrics.update_latency(latency_ms)
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        optimizer = get_performance_optimizer()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            optimizer.metrics.update_latency(latency_ms)
            return result
            
        except Exception:
            latency_ms = (time.time() - start_time) * 1000
            optimizer.metrics.update_latency(latency_ms)
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper