"""
Service Interfaces and Protocols

This module defines the base interfaces and protocols for all services in the system.
It provides:
- Base Service interface with lifecycle management
- ConfigurableService base class for services requiring configuration
- Common service protocols (Logger, Config, Cache)
- Service lifecycle management (initialize, shutdown, health_check)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol, runtime_checkable
from enum import Enum
import logging


class ServiceState(Enum):
    """Service state enumeration."""
    CREATED = "created"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class Service(ABC):
    """
    Base interface for all services.
    
    All services must implement this interface to ensure consistent
    lifecycle management and health monitoring.
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the service.
        
        This method should set up any required resources, connections,
        or state needed for the service to operate.
        
        Raises:
            ServiceInitializationError: If initialization fails
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """
        Shutdown the service gracefully.
        
        This method should clean up resources, close connections,
        and perform any necessary cleanup operations.
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if service is healthy and operational.
        
        Returns:
            True if service is healthy, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """
        List of service dependencies.
        
        Returns:
            List of service names this service depends on
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Service name for identification.
        
        Returns:
            Unique service name
        """
        pass


class ConfigurableService(Service):
    """
    Base class for services that require configuration.
    
    Provides common functionality for services that need configuration
    and state management.
    """
    
    def __init__(self, config: Dict[str, Any], name: Optional[str] = None):
        """
        Initialize configurable service.
        
        Args:
            config: Service configuration dictionary
            name: Service name (defaults to class name)
        """
        self.config = config
        self._name = name or self.__class__.__name__
        self._state = ServiceState.CREATED
        self._initialized = False
        self._logger = logging.getLogger(f"{__name__}.{self._name}")
        self._dependencies: List[str] = []
    
    @property
    def name(self) -> str:
        """Service name."""
        return self._name
    
    @property
    def state(self) -> ServiceState:
        """Current service state."""
        return self._state
    
    @property
    def dependencies(self) -> List[str]:
        """Service dependencies."""
        return self._dependencies.copy()
    
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized
    
    def is_healthy(self) -> bool:
        """Check if service is in a healthy state."""
        return self._state in [ServiceState.INITIALIZED, ServiceState.RUNNING]
    
    def initialize(self) -> None:
        """
        Initialize the service with error handling and state management.
        
        Raises:
            ServiceInitializationError: If initialization fails
        """
        if self._initialized:
            self._logger.warning(f"Service {self._name} already initialized")
            return
        
        try:
            self._state = ServiceState.INITIALIZING
            self._logger.info(f"Initializing service: {self._name}")
            
            # Call the actual initialization logic
            self._do_initialize()
            
            self._initialized = True
            self._state = ServiceState.INITIALIZED
            self._logger.info(f"Service {self._name} initialized successfully")
            
        except Exception as e:
            self._state = ServiceState.ERROR
            self._logger.error(f"Failed to initialize service {self._name}: {e}")
            raise ServiceInitializationError(f"Failed to initialize {self._name}: {e}") from e
    
    def shutdown(self) -> None:
        """Shutdown the service with error handling and state management."""
        if not self._initialized:
            self._logger.warning(f"Service {self._name} not initialized, skipping shutdown")
            return
        
        try:
            self._state = ServiceState.STOPPING
            self._logger.info(f"Shutting down service: {self._name}")
            
            # Call the actual shutdown logic
            self._do_shutdown()
            
            self._initialized = False
            self._state = ServiceState.STOPPED
            self._logger.info(f"Service {self._name} shutdown successfully")
            
        except Exception as e:
            self._state = ServiceState.ERROR
            self._logger.error(f"Error during shutdown of service {self._name}: {e}")
            # Don't re-raise shutdown errors to allow other services to shutdown
    
    def health_check(self) -> bool:
        """
        Perform health check with error handling.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            if not self._initialized:
                return False
            
            # Call the actual health check logic
            return self._do_health_check()
            
        except Exception as e:
            self._logger.error(f"Health check failed for service {self._name}: {e}")
            return False
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final value
        config[keys[-1]] = value
    
    @abstractmethod
    def _do_initialize(self) -> None:
        """
        Actual initialization logic to be implemented by subclasses.
        
        Raises:
            Exception: Any initialization error
        """
        pass
    
    @abstractmethod
    def _do_shutdown(self) -> None:
        """
        Actual shutdown logic to be implemented by subclasses.
        
        Raises:
            Exception: Any shutdown error
        """
        pass
    
    def _do_health_check(self) -> bool:
        """
        Actual health check logic to be implemented by subclasses.
        
        Default implementation returns True if initialized.
        
        Returns:
            True if service is healthy, False otherwise
        """
        return self._initialized


# Service Protocols

@runtime_checkable
class LoggerProtocol(Protocol):
    """Protocol for logger services."""
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        ...
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        ...
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        ...
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        ...
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        ...
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        ...


@runtime_checkable
class ConfigProtocol(Protocol):
    """Protocol for configuration services."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        ...
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        ...
    
    def has(self, key: str) -> bool:
        """Check if configuration key exists."""
        ...
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        ...
    
    def reload(self) -> None:
        """Reload configuration from source."""
        ...


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for cache services."""
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        ...
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        ...
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        ...
    
    def clear(self) -> None:
        """Clear all cache entries."""
        ...
    
    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern."""
        ...


@runtime_checkable
class DatabaseProtocol(Protocol):
    """Protocol for database services."""
    
    def connect(self) -> None:
        """Establish database connection."""
        ...
    
    def disconnect(self) -> None:
        """Close database connection."""
        ...
    
    def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute database query."""
        ...
    
    def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch single row from database."""
        ...
    
    def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all rows from database."""
        ...
    
    def begin_transaction(self) -> None:
        """Begin database transaction."""
        ...
    
    def commit(self) -> None:
        """Commit database transaction."""
        ...
    
    def rollback(self) -> None:
        """Rollback database transaction."""
        ...


@runtime_checkable
class SecurityProtocol(Protocol):
    """Protocol for security services."""
    
    def validate_input(self, input_data: str) -> bool:
        """Validate input for security threats."""
        ...
    
    def sanitize_input(self, input_data: str) -> str:
        """Sanitize input data."""
        ...
    
    def check_permissions(self, user_id: str, resource: str, action: str) -> bool:
        """Check user permissions for resource action."""
        ...
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        ...
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted data."""
        ...


@runtime_checkable
class MonitoringProtocol(Protocol):
    """Protocol for monitoring services."""
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric value."""
        ...
    
    def increment_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        ...
    
    def record_timing(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record timing information."""
        ...
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set gauge metric value."""
        ...
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        ...


# Service Exceptions

class ServiceError(Exception):
    """Base exception for service-related errors."""
    pass


class ServiceInitializationError(ServiceError):
    """Raised when service initialization fails."""
    pass


class ServiceShutdownError(ServiceError):
    """Raised when service shutdown fails."""
    pass


class ServiceNotAvailableError(ServiceError):
    """Raised when a required service is not available."""
    pass


class ServiceConfigurationError(ServiceError):
    """Raised when service configuration is invalid."""
    pass


class ServiceHealthCheckError(ServiceError):
    """Raised when service health check fails."""
    pass


# Service Lifecycle Manager

class ServiceLifecycleManager:
    """
    Manages the lifecycle of multiple services.
    
    Provides coordinated initialization, shutdown, and health monitoring
    for a collection of services.
    """
    
    def __init__(self):
        self._services: List[Service] = []
        self._logger = logging.getLogger(__name__)
    
    def add_service(self, service: Service) -> None:
        """
        Add a service to lifecycle management.
        
        Args:
            service: Service to add
        """
        self._services.append(service)
        self._logger.debug(f"Added service to lifecycle management: {service.name}")
    
    def initialize_all(self) -> None:
        """
        Initialize all managed services in dependency order.
        
        Raises:
            ServiceInitializationError: If any service fails to initialize
        """
        # Sort services by dependencies (simple topological sort)
        sorted_services = self._sort_by_dependencies()
        
        initialized = []
        try:
            for service in sorted_services:
                self._logger.info(f"Initializing service: {service.name}")
                service.initialize()
                initialized.append(service)
                
        except Exception:
            # Shutdown any services that were successfully initialized
            self._logger.error("Service initialization failed, shutting down initialized services")
            for service in reversed(initialized):
                try:
                    service.shutdown()
                except Exception as shutdown_error:
                    self._logger.error(f"Error shutting down {service.name}: {shutdown_error}")
            raise
    
    def shutdown_all(self) -> None:
        """Shutdown all managed services in reverse dependency order."""
        # Shutdown in reverse order
        sorted_services = self._sort_by_dependencies()
        
        for service in reversed(sorted_services):
            try:
                self._logger.info(f"Shutting down service: {service.name}")
                service.shutdown()
            except Exception as e:
                self._logger.error(f"Error shutting down {service.name}: {e}")
    
    def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all managed services.
        
        Returns:
            Dictionary mapping service names to health status
        """
        health_status = {}
        for service in self._services:
            try:
                health_status[service.name] = service.health_check()
            except Exception as e:
                self._logger.error(f"Health check failed for {service.name}: {e}")
                health_status[service.name] = False
        
        return health_status
    
    def get_service_states(self) -> Dict[str, str]:
        """
        Get current state of all managed services.
        
        Returns:
            Dictionary mapping service names to their states
        """
        states = {}
        for service in self._services:
            if isinstance(service, ConfigurableService):
                states[service.name] = service.state.value
            else:
                # For services not extending ConfigurableService, infer state
                try:
                    if service.health_check():
                        states[service.name] = ServiceState.RUNNING.value
                    else:
                        states[service.name] = ServiceState.ERROR.value
                except Exception:
                    states[service.name] = ServiceState.ERROR.value
        
        return states
    
    def _sort_by_dependencies(self) -> List[Service]:
        """
        Sort services by their dependencies using topological sort.
        
        Returns:
            List of services sorted by dependency order
        """
        # Simple dependency sorting - in a real implementation,
        # this would use a proper topological sort algorithm
        service_map = {service.name: service for service in self._services}
        sorted_services = []
        visited = set()
        
        def visit(service: Service):
            if service.name in visited:
                return
            
            # Visit dependencies first
            for dep_name in service.dependencies:
                if dep_name in service_map:
                    visit(service_map[dep_name])
            
            visited.add(service.name)
            sorted_services.append(service)
        
        for service in self._services:
            visit(service)
        
        return sorted_services