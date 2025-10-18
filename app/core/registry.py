"""
Service Registry for Dependency Injection and Management

This module provides a centralized service registry that supports:
- Singleton and factory registration patterns
- Automatic dependency resolution and injection
- Service validation and health checking
- Circular dependency detection
"""

from typing import Any, Dict, Type, TypeVar, Optional, Callable, List, Set
import inspect
import logging
from dataclasses import dataclass
from enum import Enum

T = TypeVar("T")


class ServiceLifecycle(Enum):
    """Service lifecycle states."""

    REGISTERED = "registered"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


@dataclass
class ServiceInfo:
    """Information about a registered service."""

    name: str
    service_type: str  # 'singleton', 'factory', 'class'
    dependencies: List[str]
    lifecycle: ServiceLifecycle
    instance: Optional[Any] = None
    factory: Optional[Callable] = None
    service_class: Optional[Type] = None
    health_status: bool = True
    error_message: Optional[str] = None


class ServiceNotFoundError(Exception):
    """Raised when a requested service is not found in the registry."""

    pass


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected."""

    pass


class ServiceInitializationError(Exception):
    """Raised when service initialization fails."""

    pass


class ServiceRegistry:
    """
    Centralized service registry for dependency injection.

    Supports singleton and factory patterns with automatic dependency resolution,
    service validation, health checking, and circular dependency detection.
    """

    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}
        self._logger = logging.getLogger(__name__)
        self._initialization_stack: Set[str] = set()

    def register_singleton(
        self, name: str, service: Any, dependencies: Optional[List[str]] = None
    ) -> None:
        """
        Register a singleton service instance.

        Args:
            name: Service name for registry lookup
            service: Service instance to register
            dependencies: List of dependency service names
        """
        dependencies = dependencies or []

        service_info = ServiceInfo(
            name=name,
            service_type="singleton",
            dependencies=dependencies,
            lifecycle=ServiceLifecycle.INITIALIZED,
            instance=service,
        )

        self._services[name] = service_info
        self._logger.debug(f"Registered singleton service: {name}")

        # Validate health if service supports it
        self._check_service_health(service_info)

    def register_factory(
        self,
        name: str,
        factory: Callable[[], T],
        dependencies: Optional[List[str]] = None,
    ) -> None:
        """
        Register a service factory for on-demand creation.

        Args:
            name: Service name for registry lookup
            factory: Factory function that creates service instances
            dependencies: List of dependency service names
        """
        dependencies = dependencies or []

        service_info = ServiceInfo(
            name=name,
            service_type="factory",
            dependencies=dependencies,
            lifecycle=ServiceLifecycle.REGISTERED,
            factory=factory,
        )

        self._services[name] = service_info
        self._logger.debug(f"Registered factory service: {name}")

    def register_class(
        self, name: str, cls: Type[T], dependencies: Optional[List[str]] = None
    ) -> None:
        """
        Register a class with automatic dependency injection.

        Args:
            name: Service name for registry lookup
            cls: Service class to register
            dependencies: List of dependency service names (auto-detected if None)
        """
        # Auto-detect dependencies from constructor if not provided
        if dependencies is None:
            dependencies = self._extract_dependencies(cls)

        def factory():
            return self._create_instance_with_dependencies(cls, dependencies)

        service_info = ServiceInfo(
            name=name,
            service_type="class",
            dependencies=dependencies,
            lifecycle=ServiceLifecycle.REGISTERED,
            factory=factory,
            service_class=cls,
        )

        self._services[name] = service_info
        self._logger.debug(
            f"Registered class service: {name} with dependencies: {dependencies}"
        )

    def get(self, name: str) -> Any:
        """
        Get service instance, creating if necessary.

        Args:
            name: Service name to retrieve

        Returns:
            Service instance

        Raises:
            ServiceNotFoundError: If service is not registered
            CircularDependencyError: If circular dependency detected
            ServiceInitializationError: If service initialization fails
        """
        if name not in self._services:
            raise ServiceNotFoundError(f"Service '{name}' not registered")

        service_info = self._services[name]

        # Return existing instance for singletons
        if (
            service_info.service_type == "singleton"
            and service_info.instance is not None
        ):
            return service_info.instance

        # Check for circular dependencies
        if name in self._initialization_stack:
            cycle = list(self._initialization_stack) + [name]
            raise CircularDependencyError(
                f"Circular dependency detected: {' -> '.join(cycle)}"
            )

        # Create instance if needed
        if service_info.instance is None and service_info.factory is not None:
            try:
                self._initialization_stack.add(name)
                service_info.lifecycle = ServiceLifecycle.INITIALIZING

                # Create instance using factory
                instance = service_info.factory()

                # Store instance for singletons and classes
                if service_info.service_type in ["singleton", "class"]:
                    service_info.instance = instance

                service_info.lifecycle = ServiceLifecycle.INITIALIZED
                self._check_service_health(service_info)

                self._logger.debug(f"Created service instance: {name}")
                return instance

            except Exception as e:
                service_info.lifecycle = ServiceLifecycle.FAILED
                service_info.error_message = str(e)
                self._logger.error(f"Failed to create service '{name}': {e}")
                raise ServiceInitializationError(
                    f"Failed to initialize service '{name}': {e}"
                ) from e
            finally:
                self._initialization_stack.discard(name)

        # For factory services, create new instance each time
        if service_info.service_type == "factory" and service_info.factory is not None:
            try:
                return service_info.factory()
            except Exception as e:
                self._logger.error(f"Failed to create factory instance '{name}': {e}")
                raise ServiceInitializationError(
                    f"Failed to create factory instance '{name}': {e}"
                ) from e

        return service_info.instance

    def has(self, name: str) -> bool:
        """
        Check if service is registered.

        Args:
            name: Service name to check

        Returns:
            True if service is registered, False otherwise
        """
        return name in self._services

    def validate_dependencies(self) -> List[str]:
        """
        Validate all registered dependencies can be resolved.

        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []

        # Check for missing dependencies
        for service_name, service_info in self._services.items():
            for dep_name in service_info.dependencies:
                if not self.has(dep_name):
                    errors.append(
                        f"Service '{service_name}' depends on unregistered service '{dep_name}'"
                    )

        # Check for circular dependencies
        try:
            self._detect_circular_dependencies()
        except CircularDependencyError as e:
            errors.append(str(e))

        return errors

    def get_service_info(self, name: str) -> Optional[ServiceInfo]:
        """
        Get information about a registered service.

        Args:
            name: Service name

        Returns:
            ServiceInfo if service exists, None otherwise
        """
        return self._services.get(name)

    def list_services(self) -> List[str]:
        """
        Get list of all registered service names.

        Returns:
            List of service names
        """
        return list(self._services.keys())

    def health_check(self, name: Optional[str] = None) -> Dict[str, bool]:
        """
        Perform health check on services.

        Args:
            name: Specific service name to check (all services if None)

        Returns:
            Dictionary mapping service names to health status
        """
        if name is not None:
            if name not in self._services:
                return {name: False}
            service_info = self._services[name]
            self._check_service_health(service_info)
            return {name: service_info.health_status}

        # Check all services
        health_status = {}
        for service_name, service_info in self._services.items():
            self._check_service_health(service_info)
            health_status[service_name] = service_info.health_status

        return health_status

    def shutdown_all(self) -> None:
        """Shutdown all services gracefully."""
        for service_name, service_info in self._services.items():
            try:
                if service_info.instance and hasattr(service_info.instance, "shutdown"):
                    service_info.instance.shutdown()
                    service_info.lifecycle = ServiceLifecycle.SHUTDOWN
                    self._logger.debug(f"Shutdown service: {service_name}")
            except Exception as e:
                self._logger.error(f"Error shutting down service '{service_name}': {e}")

    def _extract_dependencies(self, cls: Type) -> List[str]:
        """
        Extract dependency names from class constructor.

        Args:
            cls: Class to analyze

        Returns:
            List of parameter names that could be dependencies
        """
        try:
            signature = inspect.signature(cls.__init__)
            # Skip 'self' parameter
            params = [
                param.name
                for param in signature.parameters.values()
                if param.name != "self" and param.default == inspect.Parameter.empty
            ]
            return params
        except Exception as e:
            self._logger.warning(
                f"Could not extract dependencies from {cls.__name__}: {e}"
            )
            return []

    def _create_instance_with_dependencies(
        self, cls: Type[T], dependencies: List[str]
    ) -> T:
        """
        Create class instance with resolved dependencies.

        Args:
            cls: Class to instantiate
            dependencies: List of dependency names to resolve

        Returns:
            Class instance with injected dependencies
        """
        kwargs = {}
        for dep_name in dependencies:
            kwargs[dep_name] = self.get(dep_name)

        return cls(**kwargs)

    def _detect_circular_dependencies(self) -> None:
        """
        Detect circular dependencies using depth-first search.

        Raises:
            CircularDependencyError: If circular dependency is found
        """
        visited = set()
        rec_stack = set()

        def dfs(service_name: str, path: List[str]) -> None:
            if service_name in rec_stack:
                cycle_start = path.index(service_name)
                cycle = path[cycle_start:] + [service_name]
                raise CircularDependencyError(
                    f"Circular dependency detected: {' -> '.join(cycle)}"
                )

            if service_name in visited:
                return

            visited.add(service_name)
            rec_stack.add(service_name)

            if service_name in self._services:
                service_info = self._services[service_name]
                for dep_name in service_info.dependencies:
                    dfs(dep_name, path + [service_name])

            rec_stack.remove(service_name)

        # Check all services
        for service_name in self._services:
            if service_name not in visited:
                dfs(service_name, [])

    def _check_service_health(self, service_info: ServiceInfo) -> None:
        """
        Check health of a service instance.

        Args:
            service_info: Service information to check
        """
        try:
            if service_info.instance and hasattr(service_info.instance, "health_check"):
                service_info.health_status = service_info.instance.health_check()
            else:
                # If no health check method, consider healthy if initialized
                service_info.health_status = (
                    service_info.lifecycle == ServiceLifecycle.INITIALIZED
                )
        except Exception as e:
            service_info.health_status = False
            service_info.error_message = f"Health check failed: {e}"
            self._logger.warning(
                f"Health check failed for service '{service_info.name}': {e}"
            )


# Global registry instance
_registry: Optional[ServiceRegistry] = None


def get_registry() -> ServiceRegistry:
    """
    Get the global service registry instance.

    Returns:
        Global ServiceRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry


def reset_registry() -> None:
    """Reset the global registry (primarily for testing)."""
    global _registry
    if _registry is not None:
        _registry.shutdown_all()
    _registry = None
