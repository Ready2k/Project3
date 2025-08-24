"""Core application infrastructure."""

from .dependency_injection import (
    ServiceContainer,
    ServiceProvider,
    ServiceScope,
    get_service_container,
    resolve_service,
    register_service,
    inject,
    configure_services
)

__all__ = [
    'ServiceContainer',
    'ServiceProvider', 
    'ServiceScope',
    'get_service_container',
    'resolve_service',
    'register_service',
    'inject',
    'configure_services'
]