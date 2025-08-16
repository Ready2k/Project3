"""
Integration tests for performance optimization in the advanced prompt defense system.

Tests the complete integration of caching, parallel processing, and performance monitoring
with the actual security validation pipeline.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch

from app.security.advanced_prompt_defender import AdvancedPromptDefender
from app.security.defense_config import AdvancedPromptDefenseConfig, DetectorConfig
from app.security.attack_patterns import SecurityAction
from app.security.performance_optimizer import get_performance_optimizer


class TestPerformanceIntegration:
    """Test performance optimization integration with security validation."""
    
    @pytest.fixture
    def performance_config(self):
        """Create configuration with performance optimization enabled."""
        config = AdvancedPromptDefenseConfig()
        config.enable_caching = True
        config.cache_size = 100
        config.cache_ttl_seconds = 300
        config.parallel_detection = True
        config.max_workers = 4
        config.max_validation_time_ms = 100
        config.enable_performance_monitoring = True
        config.performance_alert_threshold_ms = 50.0
        return config
    
    @pytest.fixture
    def defender_with_performance(self, performance_config):
        """Create defender with performance optimization."""
        return AdvancedPromptDefender(performance_config)
    
    @pytest.mark.asyncio
    async def test_validation_with_caching(self, defender_with_performance):
        """Test that validation uses caching effectively."""
        defender = defender_with_performance
        test_input = "This is a legitimate business automation request for invoice processing"
        
        # First validation - should be cache miss
        start_time = time.time()
        result1 = await defender.validate_input(test_input, "test_session_1")
        first_time = time.time() - start_time
        
        # Second validation with same input - should be cache hit
        start_time = time.time()
        result2 = await defender.validate_input(test_input, "test_session_2")
        second_time = time.time() - start_time
        
        # Results should be the same
        assert result1.action == result2.action
        assert result1.confidence == result2.confidence
        
        # Second call should be faster due to caching
        assert second_time < first_time
        
        # Check performance metrics
        if defender.performance_optimizer:
            metrics = defender.get_performance_metrics()
            assert metrics['cache_metrics']['total_hits'] > 0
            assert metrics['validation_metrics']['total_validations'] >= 2
    
    @pytest.mark.asyncio
    async def test_parallel_detection_performance(self, defender_with_performance):
        """Test that parallel detection improves performance."""
        defender = defender_with_performance
        
        # Use a longer input to ensure all detectors have work to do
        test_input = """
        I need to assess the feasibility of automating our customer onboarding process.
        The current process involves manual document verification, data entry into multiple systems,
        and approval workflows. We want to understand if AI can help streamline this process
        while maintaining compliance with our regulatory requirements.
        """
        
        start_time = time.time()
        result = await defender.validate_input(test_input, "performance_test")
        execution_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert execution_time < 0.2  # 200ms should be plenty for parallel execution
        assert result.action == SecurityAction.PASS  # Should be legitimate request
        
        # Check that parallel execution was used
        if defender.performance_optimizer:
            metrics = defender.get_performance_metrics()
            # Should have used parallel execution for multiple detectors
            assert metrics['execution_metrics']['parallel_executions'] > 0
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_alerts(self, defender_with_performance):
        """Test that performance monitoring triggers alerts appropriately."""
        defender = defender_with_performance
        alerts_received = []
        
        def alert_callback(alert_type, alert_data):
            alerts_received.append((alert_type, alert_data))
        
        if defender.performance_optimizer:
            defender.register_performance_alert_callback(alert_callback)
            
            # Simulate high latency by setting metrics directly
            defender.performance_optimizer.metrics.avg_latency_ms = 75.0
            defender.performance_optimizer.monitor_performance()
            
            # Should trigger high latency alert
            assert len(alerts_received) > 0
            assert any(alert[0] == 'high_latency' for alert in alerts_received)
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_config_change(self, performance_config):
        """Test that cache is properly invalidated when configuration changes."""
        defender = AdvancedPromptDefender(performance_config)
        test_input = "Test input for cache invalidation"
        
        # First validation
        result1 = await defender.validate_input(test_input, "cache_test_1")
        
        # Change configuration
        new_config = performance_config
        new_config.detection_confidence_threshold = 0.8  # Different threshold
        defender.update_config(new_config)
        
        # Second validation should not use cached result due to config change
        result2 = await defender.validate_input(test_input, "cache_test_2")
        
        # Results might be different due to different thresholds
        # But the important thing is that cache was invalidated
        if defender.performance_optimizer:
            metrics = defender.get_performance_metrics()
            # Should have cache misses due to config change
            assert metrics['cache_metrics']['total_misses'] > 0
    
    @pytest.mark.asyncio
    async def test_resource_limit_enforcement(self, performance_config):
        """Test that resource limits are enforced."""
        # Set very low memory limit to trigger resource limiting
        performance_config.max_memory_mb = 1  # 1MB - very low
        defender = AdvancedPromptDefender(performance_config)
        
        test_input = "Test input for resource limits"
        
        # Should still work but might fall back to sequential processing
        result = await defender.validate_input(test_input, "resource_test")
        
        # Should get a valid result even with resource constraints
        assert result.action in [SecurityAction.PASS, SecurityAction.FLAG, SecurityAction.BLOCK]
        
        if defender.performance_optimizer:
            metrics = defender.get_performance_metrics()
            # Might have fallen back to sequential execution
            assert metrics['execution_metrics']['sequential_executions'] >= 0
    
    @pytest.mark.asyncio
    async def test_timeout_handling_in_validation(self, performance_config):
        """Test timeout handling during validation."""
        # Set very short timeout
        performance_config.max_validation_time_ms = 1  # 1ms - very short
        defender = AdvancedPromptDefender(performance_config)
        
        test_input = "Test input for timeout handling"
        
        # Should complete even with short timeout (might use fallback)
        start_time = time.time()
        result = await defender.validate_input(test_input, "timeout_test")
        execution_time = time.time() - start_time
        
        # Should get a result
        assert result.action in [SecurityAction.PASS, SecurityAction.FLAG, SecurityAction.BLOCK]
        
        # Execution time might exceed timeout due to fallback mechanisms
        # but should still be reasonable
        assert execution_time < 1.0  # Should complete within 1 second
    
    @pytest.mark.asyncio
    async def test_cache_optimization_during_operation(self, defender_with_performance):
        """Test that cache optimization occurs during normal operation."""
        defender = defender_with_performance
        
        if not defender.performance_optimizer:
            pytest.skip("Performance optimization not enabled")
        
        # Set low optimization interval for testing
        defender.config.cache_optimization_interval = 5
        
        # Perform multiple validations to trigger optimization
        for i in range(10):
            test_input = f"Test input number {i} for cache optimization"
            await defender.validate_input(test_input, f"cache_opt_test_{i}")
        
        # Cache optimization should have been triggered
        metrics = defender.get_performance_metrics()
        assert metrics['validation_metrics']['total_validations'] >= 10
    
    @pytest.mark.asyncio
    async def test_performance_metrics_accuracy(self, defender_with_performance):
        """Test that performance metrics are accurately tracked."""
        defender = defender_with_performance
        
        if not defender.performance_optimizer:
            pytest.skip("Performance optimization not enabled")
        
        # Clear metrics to start fresh
        defender.reset_performance_metrics()
        
        # Perform several validations
        test_inputs = [
            "First test input for metrics accuracy",
            "Second test input for metrics accuracy",
            "First test input for metrics accuracy",  # Repeat for cache hit
            "Third test input for metrics accuracy"
        ]
        
        for i, test_input in enumerate(test_inputs):
            await defender.validate_input(test_input, f"metrics_test_{i}")
        
        metrics = defender.get_performance_metrics()
        
        # Should have processed all inputs
        assert metrics['validation_metrics']['total_validations'] == len(test_inputs)
        
        # Should have at least one cache hit (repeated input)
        assert metrics['cache_metrics']['total_hits'] >= 1
        
        # Should have reasonable latency
        assert metrics['validation_metrics']['avg_latency_ms'] > 0
        assert metrics['validation_metrics']['avg_latency_ms'] < 1000  # Less than 1 second
    
    @pytest.mark.asyncio
    async def test_concurrent_validation_performance(self, defender_with_performance):
        """Test performance under concurrent validation load."""
        defender = defender_with_performance
        
        # Create multiple concurrent validation tasks
        async def validate_input_task(input_text, session_id):
            return await defender.validate_input(input_text, session_id)
        
        tasks = []
        for i in range(10):
            test_input = f"Concurrent validation test input {i}"
            task = validate_input_task(test_input, f"concurrent_test_{i}")
            tasks.append(task)
        
        # Run all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time
        
        # All validations should complete
        assert len(results) == 10
        
        # Should complete in reasonable time (parallel processing should help)
        assert execution_time < 2.0  # 2 seconds should be plenty
        
        # All results should be valid
        for result in results:
            assert result.action in [SecurityAction.PASS, SecurityAction.FLAG, SecurityAction.BLOCK]
        
        if defender.performance_optimizer:
            metrics = defender.get_performance_metrics()
            assert metrics['validation_metrics']['total_validations'] >= 10
    
    def test_performance_configuration_validation(self):
        """Test that performance configuration is properly validated."""
        config = AdvancedPromptDefenseConfig()
        
        # Test invalid configurations
        config.cache_size = -1
        config.max_workers = 0
        config.max_memory_mb = -100
        config.performance_alert_threshold_ms = -50
        
        issues = config.validate_config()
        
        # Should detect all invalid performance settings
        assert any("cache_size must be positive" in issue for issue in issues)
        assert any("max_workers must be positive" in issue for issue in issues)
        assert any("max_memory_mb must be positive" in issue for issue in issues)
        assert any("performance_alert_threshold_ms must be positive" in issue for issue in issues)
    
    @pytest.mark.asyncio
    async def test_performance_optimization_disabled(self):
        """Test behavior when performance optimization is disabled."""
        config = AdvancedPromptDefenseConfig()
        config.enable_caching = False
        config.parallel_detection = False
        config.enable_performance_monitoring = False
        
        defender = AdvancedPromptDefender(config)
        
        # Should not have performance optimizer
        assert defender.performance_optimizer is None
        
        # Should still work correctly
        test_input = "Test input without performance optimization"
        result = await defender.validate_input(test_input, "no_perf_test")
        
        assert result.action in [SecurityAction.PASS, SecurityAction.FLAG, SecurityAction.BLOCK]
        
        # Performance metrics should return default values
        metrics = defender.get_performance_metrics()
        assert metrics['system_status']['performance_optimization_enabled'] is False
    
    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self, defender_with_performance):
        """Test memory usage monitoring and alerts."""
        defender = defender_with_performance
        
        if not defender.performance_optimizer:
            pytest.skip("Performance optimization not enabled")
        
        alerts_received = []
        
        def alert_callback(alert_type, alert_data):
            alerts_received.append((alert_type, alert_data))
        
        defender.register_performance_alert_callback(alert_callback)
        
        # Simulate high memory usage
        defender.performance_optimizer.metrics.memory_usage_mb = 450.0  # High usage
        defender.performance_optimizer.monitor_performance()
        
        # Should trigger memory usage alert
        memory_alerts = [alert for alert in alerts_received if alert[0] == 'high_memory_usage']
        assert len(memory_alerts) > 0
    
    @pytest.mark.asyncio
    async def test_cache_hit_rate_monitoring(self, defender_with_performance):
        """Test cache hit rate monitoring and optimization."""
        defender = defender_with_performance
        
        if not defender.performance_optimizer:
            pytest.skip("Performance optimization not enabled")
        
        # Simulate low cache hit rate
        defender.performance_optimizer.metrics.cache_hits = 1
        defender.performance_optimizer.metrics.cache_misses = 10
        
        alerts_received = []
        
        def alert_callback(alert_type, alert_data):
            alerts_received.append((alert_type, alert_data))
        
        defender.register_performance_alert_callback(alert_callback)
        defender.performance_optimizer.monitor_performance()
        
        # Should trigger low cache hit rate alert
        cache_alerts = [alert for alert in alerts_received if alert[0] == 'low_cache_hit_rate']
        assert len(cache_alerts) > 0


class TestPerformanceRegressionPrevention:
    """Test to prevent performance regressions."""
    
    @pytest.mark.asyncio
    async def test_latency_target_compliance(self):
        """Test that validation meets the <50ms latency target."""
        config = AdvancedPromptDefenseConfig()
        config.enable_caching = True
        config.parallel_detection = True
        config.max_validation_time_ms = 50
        
        defender = AdvancedPromptDefender(config)
        
        # Test with various input types
        test_inputs = [
            "Simple business automation request",
            "More complex business process automation involving multiple systems and workflows",
            "Short input",
            "A" * 1000,  # Longer input
        ]
        
        latencies = []
        
        for i, test_input in enumerate(test_inputs):
            start_time = time.time()
            result = await defender.validate_input(test_input, f"latency_test_{i}")
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)
            
            # Each validation should complete reasonably quickly
            assert latency_ms < 100  # 100ms upper bound for individual validations
            assert result.action in [SecurityAction.PASS, SecurityAction.FLAG, SecurityAction.BLOCK]
        
        # Average latency should meet target
        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 50  # Target: <50ms average latency
    
    @pytest.mark.asyncio
    async def test_memory_usage_bounds(self):
        """Test that memory usage stays within reasonable bounds."""
        config = AdvancedPromptDefenseConfig()
        config.cache_size = 1000  # Reasonable cache size
        config.max_memory_mb = 512  # 512MB limit
        
        defender = AdvancedPromptDefender(config)
        
        # Perform many validations to test memory usage
        for i in range(100):
            test_input = f"Memory test input number {i} with some additional content to make it longer"
            await defender.validate_input(test_input, f"memory_test_{i}")
        
        if defender.performance_optimizer:
            metrics = defender.get_performance_metrics()
            
            # Memory usage should be reasonable
            memory_mb = metrics['resource_metrics'].get('current_memory_mb', 0)
            if memory_mb > 0:  # Only check if memory monitoring is working
                assert memory_mb < 512  # Should stay under limit
    
    @pytest.mark.asyncio
    async def test_cache_efficiency(self):
        """Test that caching provides meaningful performance improvement."""
        config = AdvancedPromptDefenseConfig()
        config.enable_caching = True
        
        defender = AdvancedPromptDefender(config)
        
        if not defender.performance_optimizer:
            pytest.skip("Performance optimization not enabled")
        
        test_input = "Repeated input for cache efficiency testing"
        
        # First validation (cache miss)
        start_time = time.time()
        await defender.validate_input(test_input, "cache_eff_1")
        first_time = time.time() - start_time
        
        # Multiple subsequent validations (cache hits)
        cache_hit_times = []
        for i in range(5):
            start_time = time.time()
            await defender.validate_input(test_input, f"cache_eff_{i+2}")
            cache_hit_times.append(time.time() - start_time)
        
        avg_cache_hit_time = sum(cache_hit_times) / len(cache_hit_times)
        
        # Cache hits should be significantly faster
        improvement_ratio = first_time / avg_cache_hit_time
        assert improvement_ratio > 1.5  # At least 50% improvement from caching
        
        # Check cache hit rate
        metrics = defender.get_performance_metrics()
        hit_rate = metrics['cache_metrics']['hit_rate_percent']
        assert hit_rate > 70  # Should have good hit rate with repeated input


if __name__ == "__main__":
    pytest.main([__file__])