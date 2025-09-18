"""Retry and timeout handling for Jira Data Center integration."""

import asyncio
import time
from typing import Optional, Dict, Any, List, Callable, TypeVar, Awaitable
from dataclasses import dataclass
from enum import Enum

import httpx
from pydantic import BaseModel

from app.utils.imports import require_service

T = TypeVar('T')


class RetryStrategy(str, Enum):
    """Enumeration of retry strategies."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    timeout_per_attempt: int = 30
    total_timeout: Optional[int] = None
    retry_on_status_codes: List[int] = None
    retry_on_exceptions: List[type] = None
    
    def __post_init__(self):
        """Initialize default values after creation."""
        if self.retry_on_status_codes is None:
            self.retry_on_status_codes = [429, 502, 503, 504]  # Rate limit and server errors
        
        if self.retry_on_exceptions is None:
            self.retry_on_exceptions = [
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.NetworkError
            ]


class RetryAttempt(BaseModel):
    """Information about a retry attempt."""
    attempt_number: int
    delay_before_attempt: float
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    status_code: Optional[int] = None


class RetryResult(BaseModel):
    """Result of retry operation."""
    success: bool
    result: Any = None
    total_attempts: int
    total_duration: float
    attempts: List[RetryAttempt] = []
    final_error: Optional[str] = None
    timeout_exceeded: bool = False
    troubleshooting_steps: List[str] = []


class RetryHandler:
    """Handles retry logic with configurable strategies and timeouts."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize retry handler.
        
        Args:
            config: Retry configuration, uses defaults if None
        # Get logger from service registry
        self.logger = require_service('logger', context='from')
        """
        self.config = config or RetryConfig()
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay before next attempt based on strategy.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds before next attempt
        """
        if self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.initial_delay * (self.config.backoff_multiplier ** attempt)
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.initial_delay + (attempt * self.config.initial_delay)
        else:  # FIXED_DELAY
            delay = self.config.initial_delay
        
        # Cap at max delay
        return min(delay, self.config.max_delay)
    
    def should_retry(self, attempt: int, exception: Optional[Exception] = None, status_code: Optional[int] = None) -> bool:
        """Determine if operation should be retried.
        
        Args:
            attempt: Current attempt number (0-based)
            exception: Exception that occurred, if any
            status_code: HTTP status code, if applicable
            
        Returns:
            True if operation should be retried
        """
        # Check if we've exceeded max attempts
        if attempt >= self.config.max_attempts:
            return False
        
        # Check if we should retry based on status code
        if status_code is not None:
            return status_code in self.config.retry_on_status_codes
        
        # Check if we should retry based on exception type
        if exception is not None:
            return any(isinstance(exception, exc_type) for exc_type in self.config.retry_on_exceptions)
        
        return False
    
    async def execute_with_retry(
        self, 
        operation: Callable[[], Awaitable[T]], 
        operation_name: str = "operation"
    ) -> RetryResult:
        """Execute an async operation with retry logic.
        
        Args:
            operation: Async function to execute
            operation_name: Name of operation for logging
            
        Returns:
            RetryResult with operation outcome and retry information
        """
        attempts = []
        start_time = time.time()
        last_exception = None
        last_status_code = None
        
        for attempt in range(self.config.max_attempts):
            # Check total timeout
            if self.config.total_timeout:
                elapsed = time.time() - start_time
                if elapsed >= self.config.total_timeout:
                    self.logger.warning(f"{operation_name} total timeout exceeded after {elapsed:.2f}s")
                    return RetryResult(
                        success=False,
                        total_attempts=attempt + 1,
                        total_duration=elapsed,
                        attempts=attempts,
                        final_error=f"Total timeout of {self.config.total_timeout}s exceeded",
                        timeout_exceeded=True,
                        troubleshooting_steps=self._get_timeout_troubleshooting_steps()
                    )
            
            # Calculate delay for this attempt (0 for first attempt)
            delay = 0.0 if attempt == 0 else self.calculate_delay(attempt - 1)
            
            # Wait before retry (except for first attempt)
            if delay > 0:
                self.logger.info(f"{operation_name} attempt {attempt + 1}/{self.config.max_attempts} "
                              f"after {delay:.2f}s delay")
                await asyncio.sleep(delay)
            
            attempt_start = time.time()
            retry_attempt = RetryAttempt(
                attempt_number=attempt + 1,
                delay_before_attempt=delay,
                start_time=attempt_start
            )
            
            try:
                # Execute operation with per-attempt timeout
                result = await asyncio.wait_for(
                    operation(),
                    timeout=self.config.timeout_per_attempt
                )
                
                # Success!
                attempt_end = time.time()
                retry_attempt.end_time = attempt_end
                retry_attempt.success = True
                attempts.append(retry_attempt)
                
                total_duration = attempt_end - start_time
                self.logger.info(f"{operation_name} succeeded on attempt {attempt + 1} "
                              f"after {total_duration:.2f}s")
                
                return RetryResult(
                    success=True,
                    result=result,
                    total_attempts=attempt + 1,
                    total_duration=total_duration,
                    attempts=attempts
                )
                
            except asyncio.TimeoutError:
                # Per-attempt timeout
                attempt_end = time.time()
                retry_attempt.end_time = attempt_end
                retry_attempt.error_message = f"Timeout after {self.config.timeout_per_attempt}s"
                attempts.append(retry_attempt)
                
                last_exception = httpx.TimeoutException(f"Request timeout after {self.config.timeout_per_attempt}s")
                self.logger.warning(f"{operation_name} attempt {attempt + 1} timed out after {self.config.timeout_per_attempt}s")
                
            except httpx.HTTPStatusError as e:
                # HTTP error with status code
                attempt_end = time.time()
                retry_attempt.end_time = attempt_end
                retry_attempt.status_code = e.response.status_code
                retry_attempt.error_message = f"HTTP {e.response.status_code}: {str(e)}"
                attempts.append(retry_attempt)
                
                last_exception = e
                last_status_code = e.response.status_code
                self.logger.warning(f"{operation_name} attempt {attempt + 1} failed with HTTP {e.response.status_code}")
                
            except Exception as e:
                # Other exceptions
                attempt_end = time.time()
                retry_attempt.end_time = attempt_end
                retry_attempt.error_message = str(e)
                attempts.append(retry_attempt)
                
                last_exception = e
                self.logger.warning(f"{operation_name} attempt {attempt + 1} failed: {str(e)}")
            
            # Check if we should retry
            if not self.should_retry(attempt, last_exception, last_status_code):
                break
        
        # All attempts failed
        total_duration = time.time() - start_time
        final_error = str(last_exception) if last_exception else "Unknown error"
        
        self.logger.error(f"{operation_name} failed after {len(attempts)} attempts in {total_duration:.2f}s: {final_error}")
        
        return RetryResult(
            success=False,
            total_attempts=len(attempts),
            total_duration=total_duration,
            attempts=attempts,
            final_error=final_error,
            troubleshooting_steps=self._get_failure_troubleshooting_steps(last_exception, last_status_code)
        )
    
    def _get_timeout_troubleshooting_steps(self) -> List[str]:
        """Get troubleshooting steps for timeout issues.
        
        Returns:
            List of troubleshooting steps
        """
        return [
            f"Increase total timeout (currently {self.config.total_timeout}s)",
            f"Increase per-attempt timeout (currently {self.config.timeout_per_attempt}s)",
            "Check network connectivity and latency",
            "Verify server is responsive and not overloaded",
            "Consider using a proxy if behind corporate firewall",
            "Check if DNS resolution is slow"
        ]
    
    def _get_failure_troubleshooting_steps(self, exception: Optional[Exception], status_code: Optional[int]) -> List[str]:
        """Get troubleshooting steps based on failure type.
        
        Args:
            exception: Last exception that occurred
            status_code: Last HTTP status code
            
        Returns:
            List of troubleshooting steps
        """
        steps = []
        
        if status_code == 429:
            steps.extend([
                "Rate limit exceeded - reduce request frequency",
                "Implement longer delays between requests",
                "Check if API usage is within limits",
                "Consider using different authentication method"
            ])
        elif status_code in [502, 503, 504]:
            steps.extend([
                "Server is temporarily unavailable",
                "Wait and retry later",
                "Check server status and maintenance schedules",
                "Contact system administrator if problem persists"
            ])
        elif isinstance(exception, httpx.TimeoutException):
            steps.extend([
                f"Increase timeout values (current: {self.config.timeout_per_attempt}s per attempt)",
                "Check network connectivity and latency",
                "Verify server is responsive",
                "Consider using a proxy if behind corporate firewall"
            ])
        elif isinstance(exception, (httpx.ConnectError, httpx.NetworkError)):
            steps.extend([
                "Check network connectivity",
                "Verify server address and port",
                "Check firewall and proxy settings",
                "Ensure DNS resolution is working"
            ])
        
        # General troubleshooting steps
        steps.extend([
            f"Consider increasing max attempts (current: {self.config.max_attempts})",
            f"Consider increasing delays (current strategy: {self.config.strategy.value})",
            "Check server logs for more details",
            "Contact system administrator if problem persists"
        ])
        
        return steps
    
    def get_retry_config_for_environment(self, environment: str) -> RetryConfig:
        """Get recommended retry configuration for different environments.
        
        Args:
            environment: Environment type (e.g., 'enterprise', 'cloud', 'local')
            
        Returns:
            Recommended retry configuration
        """
        if environment.lower() == 'enterprise':
            # Enterprise networks may be slower but more stable
            return RetryConfig(
                max_attempts=5,
                initial_delay=2.0,
                max_delay=120.0,
                backoff_multiplier=2.0,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                timeout_per_attempt=60,
                total_timeout=300  # 5 minutes total
            )
        elif environment.lower() == 'cloud':
            # Cloud environments are usually faster but may have rate limits
            return RetryConfig(
                max_attempts=3,
                initial_delay=1.0,
                max_delay=30.0,
                backoff_multiplier=2.0,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                timeout_per_attempt=30,
                total_timeout=120  # 2 minutes total
            )
        elif environment.lower() == 'local':
            # Local development - fast retries, short timeouts
            return RetryConfig(
                max_attempts=2,
                initial_delay=0.5,
                max_delay=5.0,
                backoff_multiplier=2.0,
                strategy=RetryStrategy.FIXED_DELAY,
                timeout_per_attempt=10,
                total_timeout=30
            )
        else:
            # Default configuration
            return RetryConfig()
    
    def create_http_client_with_retry(self, base_config: Dict[str, Any] = None) -> httpx.AsyncClient:
        """Create httpx client with retry-friendly configuration.
        
        Args:
            base_config: Base configuration for httpx client
            
        Returns:
            Configured httpx AsyncClient
        """
        config = base_config or {}
        
        # Set timeout configuration
        timeout_config = httpx.Timeout(
            connect=min(10.0, self.config.timeout_per_attempt / 3),  # Connection timeout
            read=self.config.timeout_per_attempt,  # Read timeout
            write=min(30.0, self.config.timeout_per_attempt),  # Write timeout
            pool=self.config.timeout_per_attempt  # Pool timeout
        )
        
        # Set retry-friendly limits
        limits = httpx.Limits(
            max_keepalive_connections=5,
            max_connections=10,
            keepalive_expiry=30.0
        )
        
        # Extract proxies separately as it's a special parameter
        proxies = config.pop('proxies', None)
        
        client_kwargs = {
            "timeout": timeout_config,
            "limits": limits,
            **config
        }
        
        if proxies is not None:
            client_kwargs["proxies"] = proxies
        
        return httpx.AsyncClient(**client_kwargs)
    
    def get_retry_statistics(self, result: RetryResult) -> Dict[str, Any]:
        """Get detailed statistics from retry result.
        
        Args:
            result: Retry result to analyze
            
        Returns:
            Dictionary with retry statistics
        """
        if not result.attempts:
            return {"no_attempts": True}
        
        attempt_durations = []
        for attempt in result.attempts:
            if attempt.end_time:
                duration = attempt.end_time - attempt.start_time
                attempt_durations.append(duration)
        
        stats = {
            "total_attempts": result.total_attempts,
            "total_duration": result.total_duration,
            "success": result.success,
            "timeout_exceeded": result.timeout_exceeded,
            "average_attempt_duration": sum(attempt_durations) / len(attempt_durations) if attempt_durations else 0,
            "min_attempt_duration": min(attempt_durations) if attempt_durations else 0,
            "max_attempt_duration": max(attempt_durations) if attempt_durations else 0,
            "successful_attempts": sum(1 for a in result.attempts if a.success),
            "failed_attempts": sum(1 for a in result.attempts if not a.success),
            "timeout_attempts": sum(1 for a in result.attempts if "timeout" in (a.error_message or "").lower()),
            "http_error_attempts": sum(1 for a in result.attempts if a.status_code is not None),
            "network_error_attempts": sum(1 for a in result.attempts if a.status_code is None and not a.success and "timeout" not in (a.error_message or "").lower())
        }
        
        return stats