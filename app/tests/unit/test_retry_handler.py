"""Unit tests for retry handling."""

import pytest
import asyncio
from unittest.mock import Mock

import httpx

from app.services.retry_handler import (
    RetryHandler, 
    RetryConfig, 
    RetryStrategy,
    RetryResult,
    RetryAttempt
)


class TestRetryConfig:
    """Test cases for retry configuration."""
    
    def test_retry_config_defaults(self):
        """Test retry configuration with default values."""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_multiplier == 2.0
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.timeout_per_attempt == 30
        assert config.total_timeout is None
        assert config.retry_on_status_codes == [429, 502, 503, 504]
        assert httpx.TimeoutException in config.retry_on_exceptions
        assert httpx.ConnectError in config.retry_on_exceptions
        assert httpx.NetworkError in config.retry_on_exceptions
    
    def test_retry_config_custom(self):
        """Test retry configuration with custom values."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=2.0,
            max_delay=120.0,
            backoff_multiplier=3.0,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            timeout_per_attempt=60,
            total_timeout=300,
            retry_on_status_codes=[500, 502],
            retry_on_exceptions=[httpx.TimeoutException]
        )
        
        assert config.max_attempts == 5
        assert config.initial_delay == 2.0
        assert config.max_delay == 120.0
        assert config.backoff_multiplier == 3.0
        assert config.strategy == RetryStrategy.LINEAR_BACKOFF
        assert config.timeout_per_attempt == 60
        assert config.total_timeout == 300
        assert config.retry_on_status_codes == [500, 502]
        assert config.retry_on_exceptions == [httpx.TimeoutException]


class TestRetryHandler:
    """Test cases for retry handler."""
    
    def test_init_default_config(self):
        """Test retry handler initialization with default configuration."""
        handler = RetryHandler()
        
        assert handler.config is not None
        assert handler.config.max_attempts == 3
    
    def test_init_custom_config(self):
        """Test retry handler initialization with custom configuration."""
        config = RetryConfig(max_attempts=5)
        handler = RetryHandler(config)
        
        assert handler.config == config
        assert handler.config.max_attempts == 5
    
    def test_calculate_delay_exponential_backoff(self):
        """Test delay calculation with exponential backoff."""
        config = RetryConfig(
            initial_delay=1.0,
            backoff_multiplier=2.0,
            max_delay=60.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
        handler = RetryHandler(config)
        
        assert handler.calculate_delay(0) == 1.0  # 1.0 * 2^0
        assert handler.calculate_delay(1) == 2.0  # 1.0 * 2^1
        assert handler.calculate_delay(2) == 4.0  # 1.0 * 2^2
        assert handler.calculate_delay(3) == 8.0  # 1.0 * 2^3
    
    def test_calculate_delay_linear_backoff(self):
        """Test delay calculation with linear backoff."""
        config = RetryConfig(
            initial_delay=2.0,
            strategy=RetryStrategy.LINEAR_BACKOFF
        )
        handler = RetryHandler(config)
        
        assert handler.calculate_delay(0) == 2.0  # 2.0 + (0 * 2.0)
        assert handler.calculate_delay(1) == 4.0  # 2.0 + (1 * 2.0)
        assert handler.calculate_delay(2) == 6.0  # 2.0 + (2 * 2.0)
    
    def test_calculate_delay_fixed_delay(self):
        """Test delay calculation with fixed delay."""
        config = RetryConfig(
            initial_delay=3.0,
            strategy=RetryStrategy.FIXED_DELAY
        )
        handler = RetryHandler(config)
        
        assert handler.calculate_delay(0) == 3.0
        assert handler.calculate_delay(1) == 3.0
        assert handler.calculate_delay(2) == 3.0
    
    def test_calculate_delay_max_delay_cap(self):
        """Test delay calculation respects max delay cap."""
        config = RetryConfig(
            initial_delay=10.0,
            backoff_multiplier=10.0,
            max_delay=30.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
        handler = RetryHandler(config)
        
        assert handler.calculate_delay(0) == 10.0  # 10.0 * 10^0 = 10.0
        assert handler.calculate_delay(1) == 30.0  # 10.0 * 10^1 = 100.0, capped at 30.0
        assert handler.calculate_delay(2) == 30.0  # Capped at 30.0
    
    def test_should_retry_max_attempts(self):
        """Test retry decision based on max attempts."""
        config = RetryConfig(max_attempts=3)
        handler = RetryHandler(config)
        
        assert handler.should_retry(0) is False  # No exception or status code
        assert handler.should_retry(2) is False  # At max attempts
        assert handler.should_retry(3) is False  # Exceeded max attempts
    
    def test_should_retry_status_codes(self):
        """Test retry decision based on status codes."""
        config = RetryConfig(max_attempts=3, retry_on_status_codes=[429, 502])
        handler = RetryHandler(config)
        
        assert handler.should_retry(0, status_code=429) is True
        assert handler.should_retry(0, status_code=502) is True
        assert handler.should_retry(0, status_code=404) is False
        assert handler.should_retry(0, status_code=200) is False
    
    def test_should_retry_exceptions(self):
        """Test retry decision based on exception types."""
        config = RetryConfig(max_attempts=3)
        handler = RetryHandler(config)
        
        assert handler.should_retry(0, exception=httpx.TimeoutException("timeout")) is True
        assert handler.should_retry(0, exception=httpx.ConnectError("connect error")) is True
        assert handler.should_retry(0, exception=ValueError("value error")) is False
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self):
        """Test successful operation on first attempt."""
        handler = RetryHandler()
        
        async def successful_operation():
            return "success"
        
        result = await handler.execute_with_retry(successful_operation, "test_op")
        
        assert result.success is True
        assert result.result == "success"
        assert result.total_attempts == 1
        assert len(result.attempts) == 1
        assert result.attempts[0].success is True
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_retries(self):
        """Test successful operation after retries."""
        config = RetryConfig(max_attempts=3, initial_delay=0.01)  # Fast for testing
        handler = RetryHandler(config)
        
        call_count = 0
        
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("timeout")
            return "success"
        
        result = await handler.execute_with_retry(flaky_operation, "test_op")
        
        assert result.success is True
        assert result.result == "success"
        assert result.total_attempts == 3
        assert len(result.attempts) == 3
        assert result.attempts[0].success is False
        assert result.attempts[1].success is False
        assert result.attempts[2].success is True
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_failure_max_attempts(self):
        """Test operation failure after max attempts."""
        config = RetryConfig(max_attempts=2, initial_delay=0.01)
        handler = RetryHandler(config)
        
        async def failing_operation():
            raise httpx.TimeoutException("timeout")
        
        result = await handler.execute_with_retry(failing_operation, "test_op")
        
        assert result.success is False
        assert result.total_attempts == 2
        assert len(result.attempts) == 2
        assert all(not attempt.success for attempt in result.attempts)
        assert "timeout" in result.final_error
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_non_retryable_exception(self):
        """Test operation with non-retryable exception."""
        handler = RetryHandler()
        
        async def failing_operation():
            raise ValueError("not retryable")
        
        result = await handler.execute_with_retry(failing_operation, "test_op")
        
        assert result.success is False
        assert result.total_attempts == 1
        assert len(result.attempts) == 1
        assert "not retryable" in result.final_error
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_timeout_per_attempt(self):
        """Test per-attempt timeout."""
        config = RetryConfig(timeout_per_attempt=0.1, max_attempts=2)
        handler = RetryHandler(config)
        
        async def slow_operation():
            await asyncio.sleep(0.2)  # Longer than timeout
            return "success"
        
        result = await handler.execute_with_retry(slow_operation, "test_op")
        
        assert result.success is False
        assert result.total_attempts == 2
        assert all("Timeout" in attempt.error_message for attempt in result.attempts)
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_total_timeout(self):
        """Test total timeout."""
        config = RetryConfig(
            max_attempts=10,
            initial_delay=0.1,
            total_timeout=0.2,
            timeout_per_attempt=1.0
        )
        handler = RetryHandler(config)
        
        async def failing_operation():
            raise httpx.TimeoutException("timeout")
        
        result = await handler.execute_with_retry(failing_operation, "test_op")
        
        assert result.success is False
        assert result.timeout_exceeded is True
        assert "Total timeout" in result.final_error
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_http_status_error(self):
        """Test retry with HTTP status errors."""
        config = RetryConfig(max_attempts=3, initial_delay=0.01)
        handler = RetryHandler(config)
        
        call_count = 0
        
        async def http_error_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                response = Mock()
                response.status_code = 429
                raise httpx.HTTPStatusError("Rate limited", request=Mock(), response=response)
            return "success"
        
        result = await handler.execute_with_retry(http_error_operation, "test_op")
        
        assert result.success is True
        assert result.result == "success"
        assert result.total_attempts == 3
        assert result.attempts[0].status_code == 429
        assert result.attempts[1].status_code == 429
    
    def test_get_timeout_troubleshooting_steps(self):
        """Test timeout troubleshooting steps."""
        config = RetryConfig(total_timeout=300, timeout_per_attempt=60)
        handler = RetryHandler(config)
        
        steps = handler._get_timeout_troubleshooting_steps()
        
        assert any("300s" in step for step in steps)  # Total timeout
        assert any("60s" in step for step in steps)   # Per-attempt timeout
        assert any("network connectivity" in step.lower() for step in steps)
    
    def test_get_failure_troubleshooting_steps_rate_limit(self):
        """Test troubleshooting steps for rate limit errors."""
        handler = RetryHandler()
        
        steps = handler._get_failure_troubleshooting_steps(None, 429)
        
        assert any("rate limit" in step.lower() for step in steps)
        assert any("reduce request frequency" in step.lower() for step in steps)
    
    def test_get_failure_troubleshooting_steps_server_error(self):
        """Test troubleshooting steps for server errors."""
        handler = RetryHandler()
        
        steps = handler._get_failure_troubleshooting_steps(None, 503)
        
        assert any("temporarily unavailable" in step.lower() for step in steps)
        assert any("retry later" in step.lower() for step in steps)
    
    def test_get_failure_troubleshooting_steps_timeout(self):
        """Test troubleshooting steps for timeout errors."""
        handler = RetryHandler()
        
        steps = handler._get_failure_troubleshooting_steps(httpx.TimeoutException("timeout"), None)
        
        assert any("timeout" in step.lower() for step in steps)
        assert any("network connectivity" in step.lower() for step in steps)
    
    def test_get_failure_troubleshooting_steps_connection_error(self):
        """Test troubleshooting steps for connection errors."""
        handler = RetryHandler()
        
        steps = handler._get_failure_troubleshooting_steps(httpx.ConnectError("connect failed"), None)
        
        assert any("network connectivity" in step.lower() for step in steps)
        assert any("server address" in step.lower() for step in steps)
    
    def test_get_retry_config_for_environment_enterprise(self):
        """Test retry configuration for enterprise environment."""
        handler = RetryHandler()
        
        config = handler.get_retry_config_for_environment("enterprise")
        
        assert config.max_attempts == 5
        assert config.timeout_per_attempt == 60
        assert config.total_timeout == 300
        assert config.max_delay == 120.0
    
    def test_get_retry_config_for_environment_cloud(self):
        """Test retry configuration for cloud environment."""
        handler = RetryHandler()
        
        config = handler.get_retry_config_for_environment("cloud")
        
        assert config.max_attempts == 3
        assert config.timeout_per_attempt == 30
        assert config.total_timeout == 120
        assert config.max_delay == 30.0
    
    def test_get_retry_config_for_environment_local(self):
        """Test retry configuration for local environment."""
        handler = RetryHandler()
        
        config = handler.get_retry_config_for_environment("local")
        
        assert config.max_attempts == 2
        assert config.timeout_per_attempt == 10
        assert config.total_timeout == 30
        assert config.strategy == RetryStrategy.FIXED_DELAY
    
    def test_get_retry_config_for_environment_default(self):
        """Test retry configuration for unknown environment."""
        handler = RetryHandler()
        
        config = handler.get_retry_config_for_environment("unknown")
        
        # Should return default configuration
        assert config.max_attempts == 3
        assert config.timeout_per_attempt == 30
    
    def test_create_http_client_with_retry(self):
        """Test HTTP client creation with retry-friendly configuration."""
        config = RetryConfig(timeout_per_attempt=45)
        handler = RetryHandler(config)
        
        client = handler.create_http_client_with_retry()
        
        assert isinstance(client, httpx.AsyncClient)
        assert client.timeout.read == 45.0
        assert client.timeout.pool == 45.0
    
    def test_create_http_client_with_retry_custom_config(self):
        """Test HTTP client creation with custom base configuration."""
        handler = RetryHandler()
        
        base_config = {
            "verify": False
        }
        
        client = handler.create_http_client_with_retry(base_config)
        
        assert isinstance(client, httpx.AsyncClient)
        # Just verify the client was created successfully with custom config
    
    def test_get_retry_statistics(self):
        """Test retry statistics calculation."""
        handler = RetryHandler()
        
        # Create mock retry result
        attempts = [
            RetryAttempt(
                attempt_number=1,
                delay_before_attempt=0.0,
                start_time=1000.0,
                end_time=1001.0,
                success=False,
                error_message="timeout"
            ),
            RetryAttempt(
                attempt_number=2,
                delay_before_attempt=1.0,
                start_time=1002.0,
                end_time=1003.5,
                success=True
            )
        ]
        
        result = RetryResult(
            success=True,
            result="success",
            total_attempts=2,
            total_duration=3.5,
            attempts=attempts
        )
        
        stats = handler.get_retry_statistics(result)
        
        assert stats["total_attempts"] == 2
        assert stats["total_duration"] == 3.5
        assert stats["success"] is True
        assert stats["successful_attempts"] == 1
        assert stats["failed_attempts"] == 1
        assert stats["timeout_attempts"] == 1
        assert stats["average_attempt_duration"] == 1.25  # (1.0 + 1.5) / 2
    
    def test_get_retry_statistics_no_attempts(self):
        """Test retry statistics with no attempts."""
        handler = RetryHandler()
        
        result = RetryResult(
            success=False,
            total_attempts=0,
            total_duration=0.0,
            attempts=[]
        )
        
        stats = handler.get_retry_statistics(result)
        
        assert stats["no_attempts"] is True


class TestRetryAttempt:
    """Test cases for retry attempt model."""
    
    def test_retry_attempt_creation(self):
        """Test retry attempt model creation."""
        attempt = RetryAttempt(
            attempt_number=1,
            delay_before_attempt=0.0,
            start_time=1000.0,
            end_time=1001.0,
            success=True
        )
        
        assert attempt.attempt_number == 1
        assert attempt.delay_before_attempt == 0.0
        assert attempt.start_time == 1000.0
        assert attempt.end_time == 1001.0
        assert attempt.success is True
        assert attempt.error_message is None
        assert attempt.status_code is None


class TestRetryResult:
    """Test cases for retry result model."""
    
    def test_retry_result_success(self):
        """Test retry result for successful operation."""
        result = RetryResult(
            success=True,
            result="success",
            total_attempts=2,
            total_duration=3.5,
            attempts=[]
        )
        
        assert result.success is True
        assert result.result == "success"
        assert result.total_attempts == 2
        assert result.total_duration == 3.5
        assert result.final_error is None
        assert result.timeout_exceeded is False
    
    def test_retry_result_failure(self):
        """Test retry result for failed operation."""
        result = RetryResult(
            success=False,
            total_attempts=3,
            total_duration=10.0,
            attempts=[],
            final_error="Connection failed",
            timeout_exceeded=True,
            troubleshooting_steps=["Check network"]
        )
        
        assert result.success is False
        assert result.result is None
        assert result.total_attempts == 3
        assert result.total_duration == 10.0
        assert result.final_error == "Connection failed"
        assert result.timeout_exceeded is True
        assert len(result.troubleshooting_steps) == 1