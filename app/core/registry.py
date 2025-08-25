"""
Service registry for dependency injection.

This module provides a centralized service registry for managing dependencies
and enabling loose coupling between components.
"""

from typing import Any, Dict, Type, TypeVar, Callable, Optional, List
from abc import ABC, abstractmethod
import threading
from dataclasses import dataclass
from enum import Enum

from app.utils.result import Result


T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime management options."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """Describes how a service should be created and managed."""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable[[], Any]] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    dependencies: List[Type] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class IServiceRegistry(ABC):
    """Interface for service registry implementations."""
    
    @abstractmethod
    def register(self, service_type: Type[T], implementation_type: Type[T] = None, 
                lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """Register a service type with its implementation."""
        pass
    
    @abstractmethod
    def register_factory(self, service_type: Type[T], factory: Callable[[], T],
                        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """Register a service with a factory function."""
        pass
    
    @abstractmethod
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register a service instance (singleton)."""
        pass
    
    @abstractmethod
    def resolve(self, service_type: Type[T]) -> Result[T, Exception]:
        """Resolve a service instance."""
        pass
    
    @abstractmethod
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        pass


class ServiceRegistry(IServiceRegistry):
    """
    Default implementation of the service registry.
    
    Provides dependency injection capabilities with support for different
    service lifetimes and automatic dependency resolution.
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()
    
    def register(self, service_type: Type[T], implementation_type: Type[T] = None,
                lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """
        Register a service type with its implementation.
        
        Args:
            service_type: The service interface or base type
            implementation_type: The concrete implementation type
            lifetime: Service lifetime management
        """
        with self._lock:
            impl_type = implementation_type or service_type
            descriptor = ServiceDescriptor(
                service_type=service_type,
                implementation_type=impl_type,
                lifetime=lifetime
            )
            self._services[service_type] = descriptor
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T],
                        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """
        Register a service with a factory function.
        
        Args:
            service_type: The service type
            factory: Factory function that creates the service
            lifetime: Service lifetime management
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                service_type=service_type,
                factory=factory,
                lifetime=lifetime
            )
            self._services[service_type] = descriptor
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """
        Register a service instance (singleton).
        
        Args:
            service_type: The service type
            instance: The service instance
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                service_type=service_type,
                instance=instance,
                lifetime=ServiceLifetime.SINGLETON
            )
            self._services[service_type] = descriptor
            self._singletons[service_type] = instance
    
    def resolve(self, service_type: Type[T]) -> Result[T, Exception]:
        """
        Resolve a service instance.
        
        Args:
            service_type: The service type to resolve
            
        Returns:
            Result containing the service instance or error
        """
        try:
            with self._lock:
                if service_type not in self._services:
                    return Result.error(
                        ValueError(f"Service type {service_type.__name__} is not registered")
                    )
                
                descriptor = self._services[service_type]
                
                # Handle singleton lifetime
                if descriptor.lifetime == ServiceLifetime.SINGLETON:
                    if service_type in self._singletons:
                        return Result.success(self._singletons[service_type])
                    
                    instance_result = self._create_instance(descriptor)
                    if instance_result.is_error:
                        return instance_result
                    
                    self._singletons[service_type] = instance_result.value
                    return instance_result
                
                # Handle scoped lifetime
                elif descriptor.lifetime == ServiceLifetime.SCOPED:
                    if service_type in self._scoped_instances:
                        return Result.success(self._scoped_instances[service_type])
                    
                    instance_result = self._create_instance(descriptor)
                    if instance_result.is_error:
                        return instance_result
                    
                    self._scoped_instances[service_type] = instance_result.value
                    return instance_result
                
                # Handle transient lifetime
                else:
                    return self._create_instance(descriptor)
                    
        except Exception as e:
            return Result.error(e)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Result[Any, Exception]:
        """
        Create a service instance from a descriptor.
        
        Args:
            descriptor: Service descriptor
            
        Returns:
            Result containing the created instance or error
        """
        try:
            # Use existing instance if available
            if descriptor.instance is not None:
                return Result.success(descriptor.instance)
            
            # Use factory if available
            if descriptor.factory is not None:
                return Result.success(descriptor.factory())
            
            # Create instance from implementation type
            if descriptor.implementation_type is not None:
                # Resolve dependencies first
                dependencies = []
                for dep_type in descriptor.dependencies:
                    dep_result = self.resolve(dep_type)
                    if dep_result.is_error:
                        return dep_result
                    dependencies.append(dep_result.value)
                
                # Create instance with dependencies
                if dependencies:
                    return Result.success(descriptor.implementation_type(*dependencies))
                else:
                    return Result.success(descriptor.implementation_type())
            
            return Result.error(
                ValueError(f"No way to create instance for {descriptor.service_type.__name__}")
            )
            
        except Exception as e:
            return Result.error(e)
    
    def is_registered(self, service_type: Type) -> bool:
        """
        Check if a service type is registered.
        
        Args:
            service_type: The service type to check
            
        Returns:
            True if registered, False otherwise
        """
        with self._lock:
            return service_type in self._services
    
    def clear_scoped(self) -> None:
        """Clear all scoped service instances."""
        with self._lock:
            self._scoped_instances.clear()
    
    def get_registered_services(self) -> List[Type]:
        """
        Get a list of all registered service types.
        
        Returns:
            List of registered service types
        """
        with self._lock:
            return list(self._services.keys())
    
    def get_service_info(self, service_type: Type) -> Optional[Dict[str, Any]]:
        """
        Get information about a registered service.
        
        Args:
            service_type: The service type
            
        Returns:
            Dictionary with service information or None if not registered
        """
        with self._lock:
            if service_type not in self._services:
                return None
            
            descriptor = self._services[service_type]
            return {
                "service_type": descriptor.service_type.__name__,
                "implementation_type": descriptor.implementation_type.__name__ if descriptor.implementation_type else None,
                "has_factory": descriptor.factory is not None,
                "has_instance": descriptor.instance is not None,
                "lifetime": descriptor.lifetime.value,
                "dependencies": [dep.__name__ for dep in descriptor.dependencies]
            }


# Global service registry instance
_global_registry: Optional[ServiceRegistry] = None
_registry_lock = threading.Lock()


def get_service_registry() -> ServiceRegistry:
    """
    Get the global service registry instance.
    
    Returns:
        The global service registry
    """
    global _global_registry
    
    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = ServiceRegistry()
    
    return _global_registry


def register_service(service_type: Type[T], implementation_type: Type[T] = None,
                    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
    """
    Register a service in the global registry.
    
    Args:
        service_type: The service interface or base type
        implementation_type: The concrete implementation type
        lifetime: Service lifetime management
    """
    registry = get_service_registry()
    registry.register(service_type, implementation_type, lifetime)


def resolve_service(service_type: Type[T]) -> Result[T, Exception]:
    """
    Resolve a service from the global registry.
    
    Args:
        service_type: The service type to resolve
        
    Returns:
        Result containing the service instance or error
    """
    registry = get_service_registry()
    return registry.resolve(service_type)