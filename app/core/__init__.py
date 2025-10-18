"""Core application infrastructure."""

from .dependency_injection import (
    ServiceContainer,
    ServiceProvider,
    ServiceScope,
    get_service_container,
    resolve_service,
    register_service,
    inject,
    configure_services,
)

from .registry import (
    ServiceRegistry,
    ServiceInfo,
    ServiceLifecycle,
    ServiceNotFoundError,
    CircularDependencyError,
    ServiceInitializationError,
    get_registry,
    reset_registry,
)

from .service import (
    Service,
    ConfigurableService,
    ServiceState,
    ServiceLifecycleManager,
    LoggerProtocol,
    ConfigProtocol,
    CacheProtocol,
    DatabaseProtocol,
    SecurityProtocol,
    MonitoringProtocol,
    ServiceError,
    ServiceInitializationError as ServiceInitError,
    ServiceShutdownError,
    ServiceNotAvailableError,
    ServiceConfigurationError,
    ServiceHealthCheckError,
)

__all__ = [
    # Dependency injection
    "ServiceContainer",
    "ServiceProvider",
    "ServiceScope",
    "get_service_container",
    "resolve_service",
    "register_service",
    "inject",
    "configure_services",
    # Service registry
    "ServiceRegistry",
    "ServiceInfo",
    "ServiceLifecycle",
    "ServiceNotFoundError",
    "CircularDependencyError",
    "ServiceInitializationError",
    "get_registry",
    "reset_registry",
    # Service interfaces and protocols
    "Service",
    "ConfigurableService",
    "ServiceState",
    "ServiceLifecycleManager",
    "LoggerProtocol",
    "ConfigProtocol",
    "CacheProtocol",
    "DatabaseProtocol",
    "SecurityProtocol",
    "MonitoringProtocol",
    # Service exceptions
    "ServiceError",
    "ServiceInitError",
    "ServiceShutdownError",
    "ServiceNotAvailableError",
    "ServiceConfigurationError",
    "ServiceHealthCheckError",
]
