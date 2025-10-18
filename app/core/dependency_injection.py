"""Dependency Injection Container for AAA System.

This module provides a centralized dependency injection system for managing
service dependencies, configuration, and component lifecycle.
"""

import inspect
from typing import Dict, Any, Type, TypeVar, Callable, Optional, Union, get_type_hints
from dataclasses import dataclass
from enum import Enum
import threading
from contextlib import asynccontextmanager

from app.utils.logger import app_logger
from app.utils.error_boundaries import error_boundary

T = TypeVar("T")


class ServiceScope(Enum):
    """Service lifecycle scopes."""

    SINGLETON = "singleton"  # One instance for the entire application
    TRANSIENT = "transient"  # New instance every time
    SCOPED = "scoped"  # One instance per scope (e.g., per request)


@dataclass
class ServiceRegistration:
    """Service registration information."""

    service_type: Type
    implementation: Union[Type, Callable]
    scope: ServiceScope
    factory: Optional[Callable] = None
    dependencies: Optional[Dict[str, Type]] = None
    initialized: bool = False
    instance: Optional[Any] = None


class DependencyInjectionError(Exception):
    """Exception raised for dependency injection errors."""

    pass


class ServiceContainer:
    """Dependency injection container for managing services and their dependencies."""

    def __init__(self):
        self._services: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._lock = threading.RLock()
        self._initialization_stack = set()

    def register_singleton(
        self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]
    ) -> "ServiceContainer":
        """Register a singleton service."""
        return self._register_service(
            service_type, implementation, ServiceScope.SINGLETON
        )

    def register_transient(
        self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]
    ) -> "ServiceContainer":
        """Register a transient service."""
        return self._register_service(
            service_type, implementation, ServiceScope.TRANSIENT
        )

    def register_scoped(
        self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]
    ) -> "ServiceContainer":
        """Register a scoped service."""
        return self._register_service(service_type, implementation, ServiceScope.SCOPED)

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[[], T],
        scope: ServiceScope = ServiceScope.TRANSIENT,
    ) -> "ServiceContainer":
        """Register a service with a factory function."""
        with self._lock:
            registration = ServiceRegistration(
                service_type=service_type,
                implementation=factory,
                scope=scope,
                factory=factory,
                dependencies=self._analyze_dependencies(factory),
            )
            self._services[service_type] = registration
            app_logger.debug(
                f"Registered factory for {service_type.__name__} with scope {scope.value}"
            )
            return self

    def register_instance(
        self, service_type: Type[T], instance: T
    ) -> "ServiceContainer":
        """Register a pre-created instance as a singleton."""
        with self._lock:
            registration = ServiceRegistration(
                service_type=service_type,
                implementation=type(instance),
                scope=ServiceScope.SINGLETON,
                initialized=True,
                instance=instance,
            )
            self._services[service_type] = registration
            self._instances[service_type] = instance
            app_logger.debug(f"Registered instance for {service_type.__name__}")
            return self

    def _register_service(
        self,
        service_type: Type[T],
        implementation: Union[Type[T], Callable[[], T]],
        scope: ServiceScope,
    ) -> "ServiceContainer":
        """Internal method to register a service."""
        with self._lock:
            registration = ServiceRegistration(
                service_type=service_type,
                implementation=implementation,
                scope=scope,
                dependencies=self._analyze_dependencies(implementation),
            )
            self._services[service_type] = registration
            app_logger.debug(
                f"Registered {service_type.__name__} -> {implementation.__name__} with scope {scope.value}"
            )
            return self

    def _analyze_dependencies(
        self, implementation: Union[Type, Callable]
    ) -> Dict[str, Type]:
        """Analyze constructor/function dependencies."""
        try:
            if inspect.isclass(implementation):
                # Analyze class constructor
                init_method = implementation.__init__
                signature = inspect.signature(init_method)
                type_hints = get_type_hints(init_method)
            else:
                # Analyze function
                signature = inspect.signature(implementation)
                type_hints = get_type_hints(implementation)

            dependencies = {}
            for param_name, param in signature.parameters.items():
                if param_name == "self":
                    continue

                param_type = type_hints.get(param_name)
                if param_type:
                    dependencies[param_name] = param_type

            return dependencies

        except Exception as e:
            app_logger.warning(
                f"Failed to analyze dependencies for {implementation}: {e}"
            )
            return {}

    @error_boundary("resolve_service", reraise=True)
    def resolve(self, service_type: Type[T], scope_id: Optional[str] = None) -> T:
        """Resolve a service instance."""
        with self._lock:
            if service_type not in self._services:
                raise DependencyInjectionError(
                    f"Service {service_type.__name__} is not registered"
                )

            registration = self._services[service_type]

            # Check for circular dependencies
            if service_type in self._initialization_stack:
                raise DependencyInjectionError(
                    f"Circular dependency detected for {service_type.__name__}"
                )

            # Handle different scopes
            if registration.scope == ServiceScope.SINGLETON:
                return self._resolve_singleton(service_type, registration)
            elif registration.scope == ServiceScope.SCOPED:
                return self._resolve_scoped(
                    service_type, registration, scope_id or "default"
                )
            else:  # TRANSIENT
                return self._resolve_transient(service_type, registration)

    def _resolve_singleton(
        self, service_type: Type[T], registration: ServiceRegistration
    ) -> T:
        """Resolve a singleton service."""
        if registration.initialized and registration.instance:
            return registration.instance

        if service_type in self._instances:
            return self._instances[service_type]

        # Create new instance
        instance = self._create_instance(service_type, registration)
        self._instances[service_type] = instance
        registration.instance = instance
        registration.initialized = True

        return instance

    def _resolve_scoped(
        self, service_type: Type[T], registration: ServiceRegistration, scope_id: str
    ) -> T:
        """Resolve a scoped service."""
        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = {}

        scoped_instances = self._scoped_instances[scope_id]

        if service_type in scoped_instances:
            return scoped_instances[service_type]

        # Create new instance for this scope
        instance = self._create_instance(service_type, registration)
        scoped_instances[service_type] = instance

        return instance

    def _resolve_transient(
        self, service_type: Type[T], registration: ServiceRegistration
    ) -> T:
        """Resolve a transient service."""
        return self._create_instance(service_type, registration)

    def _create_instance(
        self, service_type: Type[T], registration: ServiceRegistration
    ) -> T:
        """Create a new service instance."""
        try:
            self._initialization_stack.add(service_type)

            if registration.factory:
                # Use factory function
                dependencies = self._resolve_dependencies(
                    registration.dependencies or {}
                )
                if dependencies:
                    return registration.factory(**dependencies)
                else:
                    return registration.factory()
            else:
                # Use constructor
                implementation = registration.implementation
                dependencies = self._resolve_dependencies(
                    registration.dependencies or {}
                )

                if inspect.isclass(implementation):
                    return implementation(**dependencies)
                else:
                    # It's a callable
                    return implementation(**dependencies)

        finally:
            self._initialization_stack.discard(service_type)

    def _resolve_dependencies(self, dependencies: Dict[str, Type]) -> Dict[str, Any]:
        """Resolve all dependencies for a service."""
        resolved = {}

        for param_name, param_type in dependencies.items():
            try:
                resolved[param_name] = self.resolve(param_type)
            except DependencyInjectionError:
                # Optional dependency - skip if not registered
                app_logger.debug(
                    f"Optional dependency {param_type.__name__} not registered, skipping"
                )
                continue

        return resolved

    def clear_scope(self, scope_id: str):
        """Clear all instances in a specific scope."""
        with self._lock:
            if scope_id in self._scoped_instances:
                del self._scoped_instances[scope_id]
                app_logger.debug(f"Cleared scope: {scope_id}")

    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        return service_type in self._services

    def get_registration_info(
        self, service_type: Type
    ) -> Optional[ServiceRegistration]:
        """Get registration information for a service type."""
        return self._services.get(service_type)

    def list_registered_services(self) -> Dict[str, Dict[str, Any]]:
        """List all registered services with their information."""
        services_info = {}

        for service_type, registration in self._services.items():
            services_info[service_type.__name__] = {
                "implementation": registration.implementation.__name__,
                "scope": registration.scope.value,
                "has_factory": registration.factory is not None,
                "dependencies": (
                    list(registration.dependencies.keys())
                    if registration.dependencies
                    else []
                ),
                "initialized": registration.initialized,
            }

        return services_info


class ServiceProvider:
    """Service provider for accessing the dependency injection container."""

    _container: Optional[ServiceContainer] = None
    _lock = threading.RLock()

    @classmethod
    def get_container(cls) -> ServiceContainer:
        """Get the global service container."""
        if cls._container is None:
            with cls._lock:
                if cls._container is None:
                    cls._container = ServiceContainer()
        return cls._container

    @classmethod
    def set_container(cls, container: ServiceContainer):
        """Set the global service container."""
        with cls._lock:
            cls._container = container

    @classmethod
    def resolve(cls, service_type: Type[T], scope_id: Optional[str] = None) -> T:
        """Resolve a service from the global container."""
        return cls.get_container().resolve(service_type, scope_id)

    @classmethod
    @asynccontextmanager
    async def scope(cls, scope_id: str):
        """Create a service scope context manager."""
        try:
            yield scope_id
        finally:
            cls.get_container().clear_scope(scope_id)


def inject(service_type: Type[T]) -> T:
    """Decorator/function for injecting services."""
    return ServiceProvider.resolve(service_type)


def configure_services() -> ServiceContainer:
    """Configure all application services."""
    container = ServiceContainer()

    # Register configuration services
    from app.services.configuration_service import ConfigurationService
    from app.config.system_config import SystemConfigurationManager

    container.register_singleton(SystemConfigurationManager, SystemConfigurationManager)
    container.register_singleton(ConfigurationService, ConfigurationService)

    # Register LLM providers
    from app.llm.fakes import FakeLLM

    # Register as factories since they need configuration
    def create_fake_llm():
        return FakeLLM({}, seed=42)

    container.register_factory(FakeLLM, create_fake_llm, ServiceScope.SINGLETON)

    # Register services

    # These will be registered as transient since they need LLM providers
    # In a real implementation, you'd create factories that inject the right LLM provider

    # Register UI components
    from app.ui.components.provider_config import ProviderConfigComponent
    from app.ui.components.session_management import SessionManagementComponent
    from app.ui.components.results_display import ResultsDisplayComponent
    from app.ui.mermaid_diagrams import MermaidDiagramGenerator
    from app.ui.api_client import AAA_APIClient, StreamlitAPIIntegration

    container.register_singleton(ProviderConfigComponent, ProviderConfigComponent)
    container.register_singleton(SessionManagementComponent, SessionManagementComponent)
    container.register_singleton(ResultsDisplayComponent, ResultsDisplayComponent)
    container.register_singleton(MermaidDiagramGenerator, MermaidDiagramGenerator)

    def create_api_client():
        return AAA_APIClient("http://localhost:8000")

    container.register_factory(AAA_APIClient, create_api_client, ServiceScope.SINGLETON)

    def create_streamlit_integration():
        api_client = container.resolve(AAA_APIClient)
        return StreamlitAPIIntegration(api_client)

    container.register_factory(
        StreamlitAPIIntegration, create_streamlit_integration, ServiceScope.SINGLETON
    )

    # Register utilities
    from app.utils.error_boundaries import AsyncOperationManager
    from app.utils.audit import AuditLogger

    container.register_singleton(AsyncOperationManager, AsyncOperationManager)

    def create_audit_logger():
        from app.services.configuration_service import get_config

        config = get_config()
        return AuditLogger(
            db_path=config.audit.db_path, redact_pii=config.audit.redact_pii
        )

    container.register_factory(AuditLogger, create_audit_logger, ServiceScope.SINGLETON)

    app_logger.info(f"Configured {len(container._services)} services in DI container")

    return container


# Global container instance
_global_container = None


def get_service_container() -> ServiceContainer:
    """Get the global service container, initializing if needed."""
    global _global_container
    if _global_container is None:
        _global_container = configure_services()
        ServiceProvider.set_container(_global_container)
    return _global_container


def reset_service_container():
    """Reset the global service container (useful for testing)."""
    global _global_container
    _global_container = None
    ServiceProvider.set_container(None)


# Convenience functions
def resolve_service(service_type: Type[T], scope_id: Optional[str] = None) -> T:
    """Resolve a service from the global container."""
    return get_service_container().resolve(service_type, scope_id)


def register_service(
    service_type: Type[T],
    implementation: Union[Type[T], Callable[[], T]],
    scope: ServiceScope = ServiceScope.TRANSIENT,
):
    """Register a service in the global container."""
    container = get_service_container()
    if scope == ServiceScope.SINGLETON:
        container.register_singleton(service_type, implementation)
    elif scope == ServiceScope.SCOPED:
        container.register_scoped(service_type, implementation)
    else:
        container.register_transient(service_type, implementation)
