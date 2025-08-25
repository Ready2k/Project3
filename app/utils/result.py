"""
Result type pattern for error handling.

This module provides a Result type pattern for handling operations that can
succeed or fail, promoting explicit error handling throughout the application.
"""

from typing import TypeVar, Generic, Union, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum


T = TypeVar('T')
E = TypeVar('E')


class ResultType(Enum):
    """Enumeration of result types."""
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class Result(Generic[T, E]):
    """
    A Result type that can represent either success or failure.
    
    This pattern encourages explicit error handling and makes it clear
    when operations can fail.
    """
    
    def __init__(self, value: Union[T, E], is_success: bool):
        self._value = value
        self._is_success = is_success
    
    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        """
        Create a successful result.
        
        Args:
            value: The success value
            
        Returns:
            A Result representing success
        """
        return cls(value, True)
    
    @classmethod
    def error(cls, error: E) -> 'Result[T, E]':
        """
        Create an error result.
        
        Args:
            error: The error value
            
        Returns:
            A Result representing an error
        """
        return cls(error, False)
    
    @property
    def is_success(self) -> bool:
        """Check if this result represents success."""
        return self._is_success
    
    @property
    def is_error(self) -> bool:
        """Check if this result represents an error."""
        return not self._is_success
    
    @property
    def value(self) -> T:
        """
        Get the success value.
        
        Returns:
            The success value
            
        Raises:
            ValueError: If this result represents an error
        """
        if not self._is_success:
            raise ValueError("Cannot get value from error result")
        return self._value
    
    @property
    def error(self) -> E:
        """
        Get the error value.
        
        Returns:
            The error value
            
        Raises:
            ValueError: If this result represents success
        """
        if self._is_success:
            raise ValueError("Cannot get error from success result")
        return self._value
    
    def unwrap(self) -> T:
        """
        Unwrap the result, returning the value or raising an exception.
        
        Returns:
            The success value
            
        Raises:
            Exception: The error value if this is an error result
        """
        if self._is_success:
            return self._value
        
        # If the error is an exception, raise it
        if isinstance(self._value, Exception):
            raise self._value
        
        # Otherwise, create a generic exception
        raise Exception(f"Result error: {self._value}")
    
    def unwrap_or(self, default: T) -> T:
        """
        Unwrap the result, returning the value or a default.
        
        Args:
            default: Default value to return on error
            
        Returns:
            The success value or the default
        """
        return self._value if self._is_success else default
    
    def map(self, func: Callable[[T], Any]) -> 'Result[Any, E]':
        """
        Map a function over the success value.
        
        Args:
            func: Function to apply to the success value
            
        Returns:
            A new Result with the mapped value, or the original error
        """
        if self._is_success:
            try:
                return Result.success(func(self._value))
            except Exception as e:
                return Result.error(e)
        return Result.error(self._value)
    
    def map_error(self, func: Callable[[E], Any]) -> 'Result[T, Any]':
        """
        Map a function over the error value.
        
        Args:
            func: Function to apply to the error value
            
        Returns:
            A new Result with the mapped error, or the original success
        """
        if not self._is_success:
            try:
                return Result.error(func(self._value))
            except Exception as e:
                return Result.error(e)
        return Result.success(self._value)
    
    def and_then(self, func: Callable[[T], 'Result[Any, E]']) -> 'Result[Any, E]':
        """
        Chain operations that return Results.
        
        Args:
            func: Function that takes the success value and returns a Result
            
        Returns:
            The result of the function, or the original error
        """
        if self._is_success:
            try:
                return func(self._value)
            except Exception as e:
                return Result.error(e)
        return Result.error(self._value)
    
    def __str__(self) -> str:
        """String representation of the result."""
        if self._is_success:
            return f"Success({self._value})"
        return f"Error({self._value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the result."""
        return self.__str__()


# Convenience type aliases
Success = Result.success
Error = Result.error


# Helper functions for common patterns
def try_operation(func: Callable[[], T], error_type: type = Exception) -> Result[T, Exception]:
    """
    Execute a function and wrap the result in a Result type.
    
    Args:
        func: Function to execute
        error_type: Type of exception to catch (default: Exception)
        
    Returns:
        Result containing the function result or caught exception
    """
    try:
        return Result.success(func())
    except error_type as e:
        return Result.error(e)


def combine_results(*results: Result[Any, Any]) -> Result[list, Any]:
    """
    Combine multiple results into a single result.
    
    Args:
        *results: Variable number of Result objects
        
    Returns:
        Success with list of all values if all succeed, or first error
    """
    values = []
    for result in results:
        if result.is_error:
            return Result.error(result.error)
        values.append(result.value)
    return Result.success(values)