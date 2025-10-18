"""
Common types and protocols for the dependency management system.

This module defines:
- Result type pattern for error handling
- Service protocols for type safety
- Common error types for dependency management
- ServiceConfig dataclass for service configuration
"""

from typing import TypeVar, Generic, Union, Dict, Any, List, Optional, Protocol
from dataclasses import dataclass
from enum import Enum

# Result type for error handling
T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Success(Generic[T]):
    """Successful result containing a value."""

    value: T

    def is_success(self) -> bool:
        return True

    def is_error(self) -> bool:
        return False


@dataclass
class Error(Generic[E]):
    """Error result containing error information."""

    error: E

    def is_success(self) -> bool:
        return False

    def is_error(self) -> bool:
        return True


Result = Union[Success[T], Error[E]]


# Service protocols for type safety
class LoggerProtocol(Protocol):
    """Protocol for logger services."""

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        ...

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        ...


class ConfigProtocol(Protocol):
    """Protocol for configuration services."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        ...

    def has(self, key: str) -> bool:
        """Check if a configuration key exists."""
        ...


class CacheProtocol(Protocol):
    """Protocol for cache services."""

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        ...

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        ...

    def clear(self) -> None:
        """Clear all cache entries."""
        ...


# Configuration types
@dataclass
class ServiceConfig:
    """Configuration for a service."""

    name: str
    class_path: str
    dependencies: List[str]
    config: Dict[str, Any]
    singleton: bool = True


# Common error types for dependency management
class DependencyError(Exception):
    """Base class for dependency-related errors."""

    pass


class ServiceNotAvailableError(DependencyError):
    """Raised when a required service is not available."""

    pass


class CircularDependencyError(DependencyError):
    """Raised when circular dependencies are detected."""

    pass


class ServiceRegistrationError(DependencyError):
    """Raised when service registration fails."""

    pass


class ServiceInitializationError(DependencyError):
    """Raised when service initialization fails."""

    pass


# Additional utility types
class ServiceStatus(Enum):
    """Status of a service."""

    NOT_REGISTERED = "not_registered"
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class ServiceInfo:
    """Information about a registered service."""

    name: str
    status: ServiceStatus
    dependencies: List[str]
    is_singleton: bool
    class_path: Optional[str] = None
    error_message: Optional[str] = None
