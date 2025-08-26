"""Error boundaries for critical operations.

This module provides decorators and context managers for handling errors
in critical system operations with proper logging and fallback mechanisms.
"""

import asyncio
import functools
import time
from typing import Any, Callable, Optional, TypeVar, Union, Dict
from contextlib import asynccontextmanager

from app.utils.logger import app_logger

T = TypeVar('T')


class ErrorBoundaryError(Exception):
    """Base exception for error boundary failures."""
    def __init__(self, message: str, original_error: Exception, context: Dict[str, Any] = None):
        self.message = message
        self.original_error = original_error
        self.context = context or {}
        super().__init__(message)


def error_boundary(
    operation_name: str,
    fallback_value: Any = None,
    reraise: bool = False,
    timeout_seconds: Optional[float] = None,
    max_retries: int = 0,
    retry_delay: float = 1.0
):
    """Decorator that provides error boundary protection for functions.
    
    Args:
        operation_name: Name of the operation for logging
        fallback_value: Value to return if operation fails
        reraise: Whether to reraise the exception after logging
        timeout_seconds: Optional timeout for the operation
        max_retries: Number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Union[T, Any]:
                last_error = None
                
                for attempt in range(max_retries + 1):
                    try:
                        start_time = time.time()
                        
                        if timeout_seconds:
                            result = await asyncio.wait_for(
                                func(*args, **kwargs), 
                                timeout=timeout_seconds
                            )
                        else:
                            result = await func(*args, **kwargs)
                        
                        duration = time.time() - start_time
                        
                        if attempt > 0:
                            app_logger.info(
                                f"Operation '{operation_name}' succeeded on attempt {attempt + 1} "
                                f"after {duration:.2f}s"
                            )
                        
                        return result
                        
                    except asyncio.TimeoutError as e:
                        last_error = e
                        app_logger.error(
                            f"Operation '{operation_name}' timed out after {timeout_seconds}s "
                            f"(attempt {attempt + 1}/{max_retries + 1})"
                        )
                        
                    except Exception as e:
                        last_error = e
                        app_logger.error(
                            f"Operation '{operation_name}' failed on attempt {attempt + 1}/{max_retries + 1}: "
                            f"{type(e).__name__}: {str(e)}"
                        )
                    
                    # Wait before retry (except on last attempt)
                    if attempt < max_retries:
                        await asyncio.sleep(retry_delay)
                
                # All attempts failed
                context = {
                    'operation_name': operation_name,
                    'attempts': max_retries + 1,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                }
                
                app_logger.error(
                    f"Operation '{operation_name}' failed after {max_retries + 1} attempts. "
                    f"Returning fallback value: {fallback_value}"
                )
                
                if reraise:
                    raise ErrorBoundaryError(
                        f"Operation '{operation_name}' failed after all retry attempts",
                        last_error,
                        context
                    )
                
                return fallback_value
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Union[T, Any]:
                last_error = None
                
                for attempt in range(max_retries + 1):
                    try:
                        start_time = time.time()
                        result = func(*args, **kwargs)
                        duration = time.time() - start_time
                        
                        if attempt > 0:
                            app_logger.info(
                                f"Operation '{operation_name}' succeeded on attempt {attempt + 1} "
                                f"after {duration:.2f}s"
                            )
                        
                        return result
                        
                    except Exception as e:
                        last_error = e
                        app_logger.error(
                            f"Operation '{operation_name}' failed on attempt {attempt + 1}/{max_retries + 1}: "
                            f"{type(e).__name__}: {str(e)}"
                        )
                    
                    # Wait before retry (except on last attempt)
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                
                # All attempts failed
                context = {
                    'operation_name': operation_name,
                    'attempts': max_retries + 1,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                }
                
                app_logger.error(
                    f"Operation '{operation_name}' failed after {max_retries + 1} attempts. "
                    f"Returning fallback value: {fallback_value}"
                )
                
                if reraise:
                    raise ErrorBoundaryError(
                        f"Operation '{operation_name}' failed after all retry attempts",
                        last_error,
                        context
                    )
                
                return fallback_value
            
            return sync_wrapper
    
    return decorator


@asynccontextmanager
async def critical_operation(operation_name: str, timeout_seconds: Optional[float] = None):
    """Async context manager for critical operations with timeout and logging.
    
    Args:
        operation_name: Name of the operation for logging
        timeout_seconds: Optional timeout for the operation
    """
    start_time = time.time()
    app_logger.info(f"Starting critical operation: {operation_name}")
    
    try:
        if timeout_seconds:
            async with asyncio.timeout(timeout_seconds):
                yield
        else:
            yield
        
        duration = time.time() - start_time
        app_logger.info(f"Critical operation '{operation_name}' completed successfully in {duration:.2f}s")
        
    except asyncio.TimeoutError:
        duration = time.time() - start_time
        app_logger.error(f"Critical operation '{operation_name}' timed out after {duration:.2f}s")
        raise
        
    except Exception as e:
        duration = time.time() - start_time
        app_logger.error(
            f"Critical operation '{operation_name}' failed after {duration:.2f}s: "
            f"{type(e).__name__}: {str(e)}"
        )
        raise


def safe_async_call(coro, fallback_value=None, operation_name="async_operation"):
    """Safely execute an async coroutine with error handling.
    
    Args:
        coro: Coroutine to execute
        fallback_value: Value to return if operation fails
        operation_name: Name for logging
    
    Returns:
        Result of coroutine or fallback_value
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a task
            task = asyncio.create_task(coro)
            return task
        else:
            # If not in async context, run the coroutine
            return loop.run_until_complete(coro)
    except Exception as e:
        app_logger.error(f"Safe async call '{operation_name}' failed: {type(e).__name__}: {str(e)}")
        return fallback_value


class AsyncOperationManager:
    """Manager for handling multiple async operations with proper error boundaries."""
    
    def __init__(self, max_concurrent: int = 10, timeout_seconds: float = 30.0):
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        self._semaphore = None
    
    @property
    def semaphore(self):
        """Lazy initialization of semaphore to avoid event loop issues at import time."""
        if self._semaphore is None:
            try:
                # Try to create semaphore in current context
                self._semaphore = asyncio.Semaphore(self.max_concurrent)
            except RuntimeError as e:
                if "no current event loop" in str(e).lower():
                    # If no event loop, we'll create the semaphore when actually needed
                    # For now, create a placeholder that will be replaced when used in async context
                    app_logger.warning("No event loop available for semaphore creation, will create when needed")
                    self._semaphore = None
                    return None
                else:
                    raise
        
        return self._semaphore
    
    @error_boundary("batch_async_operations", fallback_value=[], timeout_seconds=60.0)
    async def execute_batch(self, operations: list, operation_name: str = "batch_operation") -> list:
        """Execute a batch of async operations with concurrency control.
        
        Args:
            operations: List of coroutines to execute
            operation_name: Name for logging
        
        Returns:
            List of results (None for failed operations)
        """
        # Ensure semaphore is created in async context if it wasn't created earlier
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def bounded_operation(coro):
            async with self.semaphore:
                try:
                    return await asyncio.wait_for(coro, timeout=self.timeout_seconds)
                except Exception as e:
                    app_logger.error(f"Batch operation failed: {type(e).__name__}: {str(e)}")
                    return None
        
        app_logger.info(f"Executing batch of {len(operations)} operations: {operation_name}")
        
        tasks = [bounded_operation(op) for op in operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and failures
        successes = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        failures = len(results) - successes
        
        app_logger.info(f"Batch operation '{operation_name}' completed: {successes} successes, {failures} failures")
        
        return results


# Global instance for convenience - lazy initialization to avoid event loop issues
_async_manager = None

def get_async_manager() -> AsyncOperationManager:
    """Get the global async manager instance with lazy initialization."""
    global _async_manager
    if _async_manager is None:
        _async_manager = AsyncOperationManager()
    return _async_manager