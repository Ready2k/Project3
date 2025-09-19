# Service Registry API Documentation

Generated on: 2025-09-19 14:19:12

## Overview

This document provides comprehensive API documentation for the Service Registry system,
including all classes, methods, and protocols.

## Core Classes

### ServiceRegistry

The main service registry class that manages service registration and dependency injection.

#### Methods

##### `register_singleton(name: str, service: Any, dependencies: Optional[List[str]] = None) -> None`

Register a singleton service instance.

**Parameters:**
- `name`: Service name for registry lookup
- `service`: Service instance to register
- `dependencies`: List of dependency service names

**Raises:**
- No exceptions raised directly

##### `register_factory(name: str, factory: Callable[[], T], dependencies: Optional[List[str]] = None) -> None`

Register a service factory for on-demand creation.

**Parameters:**
- `name`: Service name for registry lookup
- `factory`: Factory function that creates service instances
- `dependencies`: List of dependency service names

##### `register_class(name: str, cls: Type[T], dependencies: Optional[List[str]] = None) -> None`

Register a class with automatic dependency injection.

**Parameters:**
- `name`: Service name for registry lookup
- `cls`: Service class to register
- `dependencies`: List of dependency service names (auto-detected if None)

##### `get(name: str) -> Any`

Get service instance, creating if necessary.

**Parameters:**
- `name`: Service name to retrieve

**Returns:**
- Service instance

**Raises:**
- `ServiceNotFoundError`: If service is not registered
- `CircularDependencyError`: If circular dependency detected
- `ServiceInitializationError`: If service initialization fails

##### `has(name: str) -> bool`

Check if service is registered.

**Parameters:**
- `name`: Service name to check

**Returns:**
- `True` if service is registered, `False` otherwise

##### `validate_dependencies() -> List[str]`

Validate all registered dependencies can be resolved.

**Returns:**
- List of validation error messages (empty if all valid)

##### `health_check(name: Optional[str] = None) -> Dict[str, bool]`

Perform health check on services.

**Parameters:**
- `name`: Specific service name to check (all services if None)

**Returns:**
- Dictionary mapping service names to health status

### Service Protocols

#### LoggerProtocol

Protocol for logger services with standard logging methods.

#### ConfigProtocol

Protocol for configuration services with get/set operations.

#### CacheProtocol

Protocol for cache services with standard cache operations.

#### DatabaseProtocol

Protocol for database services with connection and query methods.

#### SecurityProtocol

Protocol for security services with validation and encryption methods.

#### MonitoringProtocol

Protocol for monitoring services with metrics recording methods.

## Usage Examples

### Basic Service Registration

```python
from app.core.registry import get_registry

# Get the global registry
registry = get_registry()

# Register a singleton service
registry.register_singleton('logger', logger_instance)

# Register a factory
registry.register_factory('cache', lambda: CacheService())

# Register a class with auto-dependency injection
registry.register_class('analyzer', AnalyzerService)
```

### Service Retrieval

```python
# Get a service (creates if needed)
logger = registry.get('logger')

# Check if service exists
if registry.has('cache'):
    cache = registry.get('cache')
```

### Health Monitoring

```python
# Check all services
health_status = registry.health_check()

# Check specific service
logger_health = registry.health_check('logger')
```

### Dependency Validation

```python
# Validate all dependencies
errors = registry.validate_dependencies()
if errors:
    print('Dependency errors:', errors)
```
