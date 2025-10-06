"""
Unit tests for the performance optimization system.

Tests caching, parallel processing, resource limits, and performance monitoring
to ensure the security validation system meets performance targets.
"""

import asyncio
import pytest
import time
import threading
from unittest.mock import Mock, patch

from app.security.performance_optimizer import (
    PerformanceOptimizer, LRUCache, ResourceLimiter, PerformanceMetrics,
    CacheEntry, get_performance_optimizer, performance_monitor
)
from app.security.attack_patterns import ProcessedInput, DetectionResult, SecurityAction


class TestCacheEntry:
    """Test cache entry functionality."""
    
    def test_cache_entry_creation(self):
        """Test cache entry creation and access."""
        entry = CacheEntry(result="test_result", timestamp=time.time())
        
        assert entry.result == "test_result"
        assert entry.access_count == 0
        assert not entry.is_expired(300)  # 5 minutes TTL
        
        # Test access
        result = entry.access()
        assert result == "test_result"
        assert entry.access_count == 1
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration."""
        old_time = time.time() - 400  # 400 seconds ago
        entry = CacheEntry(result="test_result", timestamp=old_time)
        
        assert entry.is_expired(300)  # 5 minutes TTL
        assert not entry.is_expired(500)  # 8+ minutes TTL


class TestLRUCache:
    """Test LRU cache functionality."""
    
    def test_cache_basic_operations(self):
        """Test basic cache put/get operations."""
        cache = LRUCache(max_size=3, ttl_seconds=300)
        
        # Test put and get
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.size() == 1
        
        # Test cache miss
        assert cache.get("nonexistent") is None
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = LRUCache(max_size=2, ttl_seconds=300)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.size() == 2
    
    def test_cache_ttl_expiration(self):
        """Test TTL-based cache expiration."""
        cache = LRUCache(max_size=10, ttl_seconds=1)  # 1 second TTL
        
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_cache_access_order_update(self):
        """Test that cache access updates LRU order."""
        cache = LRUCache(max_size=2, ttl_seconds=300)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # Access key1 to make it most recently used
        cache.get("key1")
        
        # Add key3, should evict key2 (least recently used)
        cache.put("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
    
    def test_cache_thread_safety(self):
        """Test cache thread safety."""
        cache = LRUCache(max_size=100, ttl_seconds=300)
        results = []
        
        def worker(thread_id):
            for i in range(10):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"
                cache.put(key, value)
                retrieved = cache.get(key)
                results.append(retrieved == value)
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All operations should have succeeded
        assert all(results)
        assert len(results) == 50  # 5 threads * 10 operations
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = LRUCache(max_size=10, ttl_seconds=300)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        stats = cache.get_stats()
        assert stats['size'] == 2
        assert stats['max_size'] == 10
        assert stats['ttl_seconds'] == 300
        assert 'total_accesses' in stats
        assert 'memory_usage_estimate' in stats


class TestResourceLimiter:
    """Test resource limiter functionality."""
    
    @patch('app.security.performance_optimizer.psutil')
    def test_memory_limit_check(self, mock_psutil):
        """Test memory limit checking."""
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_psutil.Process.return_value = mock_process
        
        limiter = ResourceLimiter(max_memory_mb=200)
        assert limiter.check_memory_limit() is True
        
        # Test exceeding limit
        mock_process.memory_info.return_value.rss = 300 * 1024 * 1024  # 300MB
        assert limiter.check_memory_limit() is False
    
    @patch('app.security.performance_optimizer.psutil')
    def test_cpu_limit_check(self, mock_psutil):
        """Test CPU limit checking."""
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 50.0
        mock_psutil.Process.return_value = mock_process
        
        limiter = ResourceLimiter(max_cpu_percent=80.0)
        assert limiter.check_cpu_limit() is True
        
        # Test exceeding limit
        mock_process.cpu_percent.return_value = 90.0
        assert limiter.check_cpu_limit() is False
    
    @patch('app.security.performance_optimizer.psutil')
    def test_combined_limits_check(self, mock_psutil):
        """Test combined resource limits checking."""
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_process.cpu_percent.return_value = 50.0
        mock_psutil.Process.return_value = mock_process
        
        limiter = ResourceLimiter(max_memory_mb=200, max_cpu_percent=80.0)
        within_limits, message = limiter.check_limits()
        
        assert within_limits is True
        assert "within limits" in message
    
    @patch('app.security.performance_optimizer.psutil')
    def test_resource_usage_reporting(self, mock_psutil):
        """Test resource usage reporting."""
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_process.memory_percent.return_value = 25.0
        mock_process.cpu_percent.return_value = 50.0
        mock_process.num_threads.return_value = 8
        mock_psutil.Process.return_value = mock_process
        
        limiter = ResourceLimiter()
        usage = limiter.get_resource_usage()
        
        assert usage['memory_mb'] == 100.0
        assert usage['memory_percent'] == 25.0
        assert usage['cpu_percent'] == 50.0
        assert usage['num_threads'] == 8


class TestPerformanceMetrics:
    """Test performance metrics functionality."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = PerformanceMetrics()
        
        assert metrics.total_validations == 0
        assert metrics.total_time_ms == 0.0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.avg_latency_ms == 0.0
        assert metrics.min_latency_ms == float('inf')
    
    def test_latency_updates(self):
        """Test latency metric updates."""
        metrics = PerformanceMetrics()
        
        metrics.update_latency(50.0)
        assert metrics.total_validations == 1
        assert metrics.avg_latency_ms == 50.0
        assert metrics.max_latency_ms == 50.0
        assert metrics.min_latency_ms == 50.0
        
        metrics.update_latency(30.0)
        assert metrics.total_validations == 2
        assert metrics.avg_latency_ms == 40.0  # (50 + 30) / 2
        assert metrics.max_latency_ms == 50.0
        assert metrics.min_latency_ms == 30.0
    
    def test_cache_metrics(self):
        """Test cache hit/miss tracking."""
        metrics = PerformanceMetrics()
        
        metrics.record_cache_hit()
        metrics.record_cache_hit()
        metrics.record_cache_miss()
        
        assert metrics.cache_hits == 2
        assert metrics.cache_misses == 1
        assert abs(metrics.get_cache_hit_rate() - 66.67) < 0.01  # 2/3 * 100, approximately
    
    def test_memory_usage_update(self):
        """Test memory usage tracking."""
        with patch('app.security.performance_optimizer.psutil') as mock_psutil:
            mock_process = Mock()
            mock_process.memory_info.return_value.rss = 200 * 1024 * 1024  # 200MB
            mock_psutil.Process.return_value = mock_process
            
            metrics = PerformanceMetrics()
            metrics.update_memory_usage()
            
            assert metrics.memory_usage_mb == 200.0


class TestPerformanceOptimizer:
    """Test performance optimizer functionality."""
    
    def test_optimizer_initialization(self):
        """Test optimizer initialization."""
        optimizer = PerformanceOptimizer(
            cache_size=100,
            cache_ttl=300,
            max_workers=4,
            timeout_ms=50
        )
        
        assert optimizer.cache.max_size == 100
        assert optimizer.cache.ttl_seconds == 300
        assert optimizer.timeout_ms == 50
        assert optimizer.executor is not None
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        optimizer = PerformanceOptimizer()
        
        key1 = optimizer._generate_cache_key("test input", "TestDetector", "config1")
        key2 = optimizer._generate_cache_key("test input", "TestDetector", "config1")
        key3 = optimizer._generate_cache_key("test input", "TestDetector", "config2")
        
        # Same input should generate same key
        assert key1 == key2
        # Different config should generate different key
        assert key1 != key3
        # Keys should be reasonable length
        assert len(key1) == 32
    
    def test_should_use_cache_logic(self):
        """Test cache usage decision logic."""
        optimizer = PerformanceOptimizer()
        
        # Too short - should not cache
        assert not optimizer._should_use_cache("short")
        
        # Too long - should not cache
        long_input = "x" * 15000
        assert not optimizer._should_use_cache(long_input)
        
        # Normal length - should cache
        normal_input = "This is a normal length input for testing"
        assert optimizer._should_use_cache(normal_input)
    
    @pytest.mark.asyncio
    async def test_cached_detection(self):
        """Test cached detection functionality."""
        optimizer = PerformanceOptimizer()
        
        # Mock detector function
        mock_detector = Mock()
        mock_result = DetectionResult(
            detector_name="TestDetector",
            is_attack=False,
            confidence=0.0,
            matched_patterns=[],
            evidence=[],
            suggested_action=SecurityAction.PASS
        )
        mock_detector.return_value = mock_result
        
        # Mock processed input
        processed_input = ProcessedInput(
            original_text="test input for caching",
            normalized_text="test input for caching",
            decoded_content=[],
            extracted_urls=[],
            detected_encodings=[],
            language="en",
            length_stats={"original_length": 23}
        )
        
        # First call should execute detector and cache result
        result1 = await optimizer.cached_detection(
            mock_detector, processed_input, "TestDetector"
        )
        assert result1 == mock_result
        assert mock_detector.call_count == 1
        assert optimizer.metrics.cache_misses == 1
        
        # Second call should use cache
        result2 = await optimizer.cached_detection(
            mock_detector, processed_input, "TestDetector"
        )
        assert result2 == mock_result
        assert mock_detector.call_count == 1  # Should not be called again
        assert optimizer.metrics.cache_hits == 1
    
    @pytest.mark.asyncio
    async def test_parallel_detection(self):
        """Test parallel detection execution."""
        optimizer = PerformanceOptimizer(max_workers=2)
        
        # Mock detector functions
        def mock_detector1(processed_input):
            time.sleep(0.01)  # Simulate work
            return DetectionResult(
                detector_name="Detector1",
                is_attack=False,
                confidence=0.0,
                matched_patterns=[],
                evidence=[],
                suggested_action=SecurityAction.PASS
            )
        
        def mock_detector2(processed_input):
            time.sleep(0.01)  # Simulate work
            return DetectionResult(
                detector_name="Detector2",
                is_attack=False,
                confidence=0.0,
                matched_patterns=[],
                evidence=[],
                suggested_action=SecurityAction.PASS
            )
        
        detector_funcs = [
            (mock_detector1, "Detector1"),
            (mock_detector2, "Detector2")
        ]
        
        processed_input = ProcessedInput(
            original_text="test input for parallel detection",
            normalized_text="test input for parallel detection",
            decoded_content=[],
            extracted_urls=[],
            detected_encodings=[],
            language="en",
            length_stats={"original_length": 33}
        )
        
        start_time = time.time()
        results = await optimizer.parallel_detection(detector_funcs, processed_input)
        execution_time = time.time() - start_time
        
        assert len(results) == 2
        assert execution_time < 0.05  # Should be faster than sequential (0.02s)
        assert optimizer.metrics.parallel_executions == 1
    
    @pytest.mark.asyncio
    async def test_sequential_fallback(self):
        """Test fallback to sequential execution."""
        # Create optimizer without thread pool
        optimizer = PerformanceOptimizer(max_workers=0)
        optimizer.executor = None
        
        def mock_detector(processed_input):
            return DetectionResult(
                detector_name="TestDetector",
                is_attack=False,
                confidence=0.0,
                matched_patterns=[],
                evidence=[],
                suggested_action=SecurityAction.PASS
            )
        
        detector_funcs = [(mock_detector, "TestDetector")]
        processed_input = ProcessedInput(
            original_text="test input",
            normalized_text="test input",
            decoded_content=[],
            extracted_urls=[],
            detected_encodings=[],
            language="en",
            length_stats={"original_length": 10}
        )
        
        results = await optimizer.parallel_detection(detector_funcs, processed_input)
        
        assert len(results) == 1
        assert optimizer.metrics.sequential_executions == 1
    
    def test_performance_metrics_collection(self):
        """Test performance metrics collection."""
        optimizer = PerformanceOptimizer()
        
        # Simulate some activity
        optimizer.metrics.update_latency(45.0)
        optimizer.metrics.update_latency(55.0)
        optimizer.metrics.record_cache_hit()
        optimizer.metrics.record_cache_miss()
        
        metrics = optimizer.get_performance_metrics()
        
        assert 'validation_metrics' in metrics
        assert 'cache_metrics' in metrics
        assert 'execution_metrics' in metrics
        assert 'resource_metrics' in metrics
        assert 'system_status' in metrics
        
        assert metrics['validation_metrics']['total_validations'] == 2
        assert metrics['validation_metrics']['avg_latency_ms'] == 50.0
        assert metrics['cache_metrics']['hit_rate_percent'] == 50.0
    
    def test_cache_optimization(self):
        """Test cache optimization functionality."""
        optimizer = PerformanceOptimizer()
        
        # Add some entries to cache
        optimizer.cache.put("key1", "value1")
        optimizer.cache.put("key2", "value2")
        
        initial_size = optimizer.cache.size()
        optimizer.optimize_cache()
        
        # Cache should still contain entries (not expired)
        assert optimizer.cache.size() == initial_size
    
    def test_performance_monitoring(self):
        """Test performance monitoring and alerting."""
        optimizer = PerformanceOptimizer()
        alerts_triggered = []
        
        def alert_callback(alert_type, alert_data):
            alerts_triggered.append((alert_type, alert_data))
        
        optimizer.register_alert_callback(alert_callback)
        
        # Simulate high latency
        optimizer.metrics.avg_latency_ms = 75.0
        optimizer.monitor_performance()
        
        # Should have at least one alert (high latency)
        assert len(alerts_triggered) >= 1
        alert_types = [alert[0] for alert in alerts_triggered]
        assert 'high_latency' in alert_types
    
    def test_resource_cleanup(self):
        """Test resource cleanup on shutdown."""
        optimizer = PerformanceOptimizer()
        
        # Add some data
        optimizer.cache.put("key1", "value1")
        assert optimizer.cache.size() == 1
        
        # Shutdown should clean up
        optimizer.shutdown()
        assert optimizer.cache.size() == 0
        assert not optimizer._monitoring_enabled


class TestPerformanceMonitorDecorator:
    """Test performance monitoring decorator."""
    
    @pytest.mark.asyncio
    async def test_async_function_monitoring(self):
        """Test monitoring of async functions."""
        
        @performance_monitor
        async def test_async_function():
            await asyncio.sleep(0.01)
            return "test_result"
        
        result = await test_async_function()
        assert result == "test_result"
        
        # Check that metrics were updated
        optimizer = get_performance_optimizer()
        assert optimizer.metrics.total_validations > 0
    
    def test_sync_function_monitoring(self):
        """Test monitoring of sync functions."""
        
        @performance_monitor
        def test_sync_function():
            time.sleep(0.01)
            return "test_result"
        
        result = test_sync_function()
        assert result == "test_result"
        
        # Check that metrics were updated
        optimizer = get_performance_optimizer()
        assert optimizer.metrics.total_validations > 0
    
    @pytest.mark.asyncio
    async def test_exception_handling_in_decorator(self):
        """Test that decorator handles exceptions properly."""
        
        @performance_monitor
        async def test_failing_function():
            await asyncio.sleep(0.01)
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            await test_failing_function()
        
        # Metrics should still be updated even on exception
        optimizer = get_performance_optimizer()
        assert optimizer.metrics.total_validations > 0


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""
    
    @pytest.mark.asyncio
    async def test_high_concurrency_scenario(self):
        """Test performance under high concurrency."""
        optimizer = PerformanceOptimizer(max_workers=4)
        
        def mock_detector(processed_input):
            time.sleep(0.001)  # Very fast detector
            return DetectionResult(
                detector_name="FastDetector",
                is_attack=False,
                confidence=0.0,
                matched_patterns=[],
                evidence=[],
                suggested_action=SecurityAction.PASS
            )
        
        processed_input = ProcessedInput(
            original_text="concurrent test input",
            normalized_text="concurrent test input",
            decoded_content=[],
            extracted_urls=[],
            detected_encodings=[],
            language="en",
            length_stats={"original_length": 21}
        )
        
        # Run many concurrent detections
        tasks = []
        for i in range(20):
            task = optimizer.cached_detection(
                mock_detector, processed_input, f"Detector{i}"
            )
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time
        
        assert len(results) == 20
        assert execution_time < 1.0  # Should complete quickly
        assert optimizer.metrics.total_validations >= 20
    
    def test_memory_pressure_scenario(self):
        """Test behavior under memory pressure."""
        # Create optimizer with small cache
        optimizer = PerformanceOptimizer(cache_size=5, max_memory_mb=1)  # Very low limit
        
        # Fill cache beyond capacity
        for i in range(10):
            optimizer.cache.put(f"key{i}", f"value{i}")
        
        # Cache should have evicted old entries
        assert optimizer.cache.size() <= 5
        
        # Should still function correctly
        assert optimizer.cache.get("key9") == "value9"  # Most recent should be present
        assert optimizer.cache.get("key0") is None  # Oldest should be evicted
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling in parallel execution."""
        optimizer = PerformanceOptimizer(timeout_ms=10)  # Very short timeout
        
        def slow_detector(processed_input):
            time.sleep(0.1)  # Longer than timeout
            return DetectionResult(
                detector_name="SlowDetector",
                is_attack=False,
                confidence=0.0,
                matched_patterns=[],
                evidence=[],
                suggested_action=SecurityAction.PASS
            )
        
        detector_funcs = [(slow_detector, "SlowDetector")]
        processed_input = ProcessedInput(
            original_text="timeout test",
            normalized_text="timeout test",
            decoded_content=[],
            extracted_urls=[],
            detected_encodings=[],
            language="en",
            length_stats={"original_length": 12}
        )
        
        results = await optimizer.parallel_detection(detector_funcs, processed_input)
        
        # Should get timeout result
        assert len(results) == 1
        if results[0].evidence:
            assert "timeout" in results[0].evidence[0].lower()
        else:
            # Alternative check - detector should have failed due to timeout
            assert results[0].detector_name == "SlowDetector"
        assert optimizer.metrics.timeout_errors > 0
    
    def test_configuration_changes(self):
        """Test handling of configuration changes."""
        optimizer = PerformanceOptimizer()
        
        # Generate cache key with initial config
        key1 = optimizer._generate_cache_key("test", "Detector", "config1")
        key2 = optimizer._generate_cache_key("test", "Detector", "config2")
        
        # Different configs should generate different keys
        assert key1 != key2
        
        # This ensures cache invalidation when config changes
        optimizer.cache.put(key1, "result1")
        optimizer.cache.put(key2, "result2")
        
        assert optimizer.cache.get(key1) == "result1"
        assert optimizer.cache.get(key2) == "result2"


if __name__ == "__main__":
    pytest.main([__file__])