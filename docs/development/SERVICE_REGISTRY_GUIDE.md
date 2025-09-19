# Service Registry Usage Guide

## Overview

The Service Registry is a centralized dependency injection system that manages service lifecycle, resolves dependencies, and provides a consistent interface for accessing services throughout the application. This guide covers how to register services, use dependency injection patterns, manage service lifecycle, and troubleshoot common issues.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Service Registration Patterns](#service-registration-patterns)
3. [Dependency Injection](#dependency-injection)
4. [Service Lifecycle Management](#service-lifecycle-management)
5. [Best Practices](#best-practices)
6. [Testing with Services](#testing-with-services)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [Advanced Usage](#advanced-usage)

## Quick Start

### Basic Service Usage

```python
from app.utils.imports import require_service, optional_service

# Get a required service (raises error if not available)
logger = require_service('logger', context='MyComponent')
logger.info("Service obtained successfully")

# Get an optional service (returns None if not available)
cache = optional_service('cache', context='MyComponent')
if cache:
    cache.set('key', 'value')
```

### Registering a Simple Service

```python
from app.core.registry import get_registry

# Get the global registry
registry = get_registry()

# Register a singleton service
my_service = MyService()
registry.register_singleton('my_service', my_service)

# Register a factory service
def create_worker():
    return WorkerService()

registry.register_factory('worker', create_worker)
```

## Service Registration Patterns

### 1. Singleton Registration

Use singletons for services that should have only one instance throughout the application lifecycle.

```python
from app.core.registry import get_registry
from app.core.services.logger_service import LoggerService

registry = get_registry()

# Create and register a singleton service
logger_config = {
    "level": "INFO",
    "format": "structured",
    "redact_pii": True
}
logger_service = LoggerService(logger_config)
registry.register_singleton('logger', logger_service, dependencies=['config'])
```

**When to use:**
- Configuration services
- Logger services
- Database connections
- Cache services
- Security validators

### 2. Factory Registration

Use factories for services that need to be created on-demand or have different instances for different contexts.

```python
from app.core.registry import get_registry

registry = get_registry()

def create_llm_provider():
    """Factory function that creates LLM provider instances."""
    config = registry.get('config')
    provider_type = config.get('llm.default_provider', 'openai')
    
    if provider_type == 'openai':
        return OpenAIProvider(config.get('llm.openai', {}))
    elif provider_type == 'anthropic':
        return AnthropicProvider(config.get('llm.anthropic', {}))
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")

registry.register_factory('llm_provider', create_llm_provider, 
                         dependencies=['config'])
```

**When to use:**
- LLM providers (different instances per request)
- Database transactions
- Request-scoped services
- Services with expensive initialization

### 3. Class Registration with Auto-Dependency Injection

Register classes that will be automatically instantiated with their dependencies injected.

```python
from app.core.registry import get_registry
from app.core.service import ConfigurableService

class RecommendationService(ConfigurableService):
    def __init__(self, config, logger, cache):
        super().__init__(config, "recommendation")
        self.logger = logger
        self.cache = cache
    
    def _do_initialize(self):
        self.logger.info("Recommendation service initialized")
    
    def _do_shutdown(self):
        self.logger.info("Recommendation service shutdown")
    
    def _do_health_check(self):
        return True

registry = get_registry()

# Register class with automatic dependency detection
registry.register_class('recommendation', RecommendationService)

# Or specify dependencies explicitly
registry.register_class('recommendation', RecommendationService, 
                       dependencies=['config', 'logger', 'cache'])
```

## Dependency Injection

### Using the Import Manager

The recommended way to access services is through the import manager utilities:

```python
from app.utils.imports import require_service, optional_service

class MyComponent:
    def __init__(self):
        # Required services - will raise ServiceRequiredError if not available
        self.logger = require_service('logger', context='MyComponent')
        self.config = require_service('config', context='MyComponent')
        
        # Optional services - will return None if not available
        self.cache = optional_service('cache', context='MyComponent')
        self.metrics = optional_service('metrics', context='MyComponent')
    
    def process_data(self, data):
        self.logger.info(f"Processing data: {len(data)} items")
        
        # Use cache if available
        if self.cache:
            cached_result = self.cache.get(f"processed_{hash(str(data))}")
            if cached_result:
                self.logger.debug("Using cached result")
                return cached_result
        
        # Process data
        result = self._do_processing(data)
        
        # Cache result if cache is available
        if self.cache:
            self.cache.set(f"processed_{hash(str(data))}", result, ttl=3600)
        
        return result
```

### Direct Registry Access

For advanced use cases, you can access the registry directly:

```python
from app.core.registry import get_registry

class AdvancedComponent:
    def __init__(self):
        self.registry = get_registry()
    
    def get_dynamic_service(self, service_type):
        """Get service based on runtime configuration."""
        service_name = f"{service_type}_service"
        
        if self.registry.has(service_name):
            return self.registry.get(service_name)
        else:
            # Fallback to default service
            return self.registry.get('default_service')
    
    def check_service_health(self):
        """Check health of all services."""
        health_status = self.registry.health_check()
        unhealthy_services = [name for name, healthy in health_status.items() if not healthy]
        
        if unhealthy_services:
            self.logger.warning(f"Unhealthy services detected: {unhealthy_services}")
        
        return len(unhealthy_services) == 0
```

## Service Lifecycle Management

### Implementing the Service Interface

All services should implement the `Service` interface or extend `ConfigurableService`:

```python
from app.core.service import ConfigurableService
from typing import Dict, Any, List

class MyCustomService(ConfigurableService):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "my_custom_service")
        self._dependencies = ["logger", "config"]  # Declare dependencies
        
        # Initialize service-specific attributes
        self.connection = None
        self.is_connected = False
    
    def _do_initialize(self) -> None:
        """Initialize the service - called during startup."""
        try:
            # Get dependencies
            self.logger = require_service('logger', context=self.name)
            
            # Initialize service resources
            connection_string = self.get_config('connection_string')
            self.connection = self._create_connection(connection_string)
            self.is_connected = True
            
            self.logger.info(f"{self.name} service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name}: {e}")
            raise
    
    def _do_shutdown(self) -> None:
        """Shutdown the service - called during application shutdown."""
        try:
            if self.connection:
                self.connection.close()
                self.is_connected = False
            
            self.logger.info(f"{self.name} service shutdown successfully")
            
        except Exception as e:
            self.logger.error(f"Error during {self.name} shutdown: {e}")
    
    def _do_health_check(self) -> bool:
        """Check if service is healthy."""
        try:
            if not self.is_connected:
                return False
            
            # Perform actual health check
            return self.connection.ping()
            
        except Exception as e:
            self.logger.error(f"Health check failed for {self.name}: {e}")
            return False
    
    def _create_connection(self, connection_string):
        """Create connection - implement based on your service needs."""
        # Implementation specific to your service
        pass
```

### Service Lifecycle Events

Services go through several lifecycle states:

1. **REGISTERED** - Service is registered but not yet initialized
2. **INITIALIZING** - Service initialization is in progress
3. **INITIALIZED** - Service is initialized and ready to use
4. **FAILED** - Service initialization or operation failed
5. **SHUTDOWN** - Service has been shut down

```python
from app.core.registry import ServiceLifecycle

# Check service lifecycle state
registry = get_registry()
service_info = registry.get_service_info('my_service')

if service_info:
    print(f"Service state: {service_info.lifecycle}")
    print(f"Health status: {service_info.health_status}")
    if service_info.error_message:
        print(f"Error: {service_info.error_message}")
```

### Coordinated Service Management

Use the `ServiceLifecycleManager` for coordinated initialization and shutdown:

```python
from app.core.service import ServiceLifecycleManager

# Create lifecycle manager
lifecycle_manager = ServiceLifecycleManager()

# Add services to management
lifecycle_manager.add_service(config_service)
lifecycle_manager.add_service(logger_service)
lifecycle_manager.add_service(cache_service)

try:
    # Initialize all services in dependency order
    lifecycle_manager.initialize_all()
    
    # Your application logic here
    
finally:
    # Shutdown all services in reverse order
    lifecycle_manager.shutdown_all()
```

## Best Practices

### 1. Service Design Principles

**Single Responsibility**: Each service should have a single, well-defined responsibility.

```python
# Good: Focused service
class EmailService(ConfigurableService):
    def send_email(self, to, subject, body):
        pass
    
    def validate_email(self, email):
        pass

# Avoid: Service with multiple responsibilities
class CommunicationService(ConfigurableService):
    def send_email(self, to, subject, body):
        pass
    
    def send_sms(self, phone, message):
        pass
    
    def push_notification(self, user_id, message):
        pass
```

**Interface Segregation**: Define specific protocols for different service capabilities.

```python
from typing import Protocol

class EmailSender(Protocol):
    def send_email(self, to: str, subject: str, body: str) -> bool:
        ...

class SMSSender(Protocol):
    def send_sms(self, phone: str, message: str) -> bool:
        ...

# Services can implement multiple protocols
class NotificationService(ConfigurableService, EmailSender, SMSSender):
    def send_email(self, to: str, subject: str, body: str) -> bool:
        # Implementation
        pass
    
    def send_sms(self, phone: str, message: str) -> bool:
        # Implementation
        pass
```

### 2. Dependency Management

**Explicit Dependencies**: Always declare service dependencies explicitly.

```python
class AnalyticsService(ConfigurableService):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "analytics")
        # Explicitly declare dependencies
        self._dependencies = ["logger", "database", "cache"]
```

**Avoid Circular Dependencies**: Design services to avoid circular dependency chains.

```python
# Good: Clear dependency hierarchy
# Config -> Logger -> Database -> Analytics

# Avoid: Circular dependencies
# Service A depends on Service B
# Service B depends on Service C  
# Service C depends on Service A
```

**Use Dependency Injection**: Don't create dependencies directly; inject them.

```python
# Good: Dependencies injected
class ReportService(ConfigurableService):
    def __init__(self, config, logger, database):
        super().__init__(config, "report")
        self.logger = logger
        self.database = database

# Avoid: Creating dependencies directly
class ReportService(ConfigurableService):
    def __init__(self, config):
        super().__init__(config, "report")
        self.logger = LoggerService(config.get('logger', {}))  # Don't do this
        self.database = DatabaseService(config.get('db', {}))  # Don't do this
```

### 3. Error Handling

**Fail Fast**: Fail quickly with clear error messages for missing required services.

```python
def process_request(request_data):
    try:
        # Required services
        validator = require_service('validator', context='RequestProcessor')
        processor = require_service('processor', context='RequestProcessor')
        
        # Process with required services
        validated_data = validator.validate(request_data)
        return processor.process(validated_data)
        
    except ServiceRequiredError as e:
        # Log and re-raise with context
        logger.error(f"Required service not available: {e}")
        raise ProcessingError(f"Cannot process request: {e}") from e
```

**Graceful Degradation**: Handle optional services gracefully.

```python
def enhanced_processing(data):
    # Required service
    processor = require_service('processor', context='EnhancedProcessor')
    
    # Optional enhancement services
    cache = optional_service('cache', context='EnhancedProcessor')
    metrics = optional_service('metrics', context='EnhancedProcessor')
    
    # Check cache if available
    if cache:
        cached_result = cache.get(f"processed_{hash(str(data))}")
        if cached_result:
            if metrics:
                metrics.increment_counter('cache_hits')
            return cached_result
    
    # Process data
    result = processor.process(data)
    
    # Cache result if cache available
    if cache:
        cache.set(f"processed_{hash(str(data))}", result)
    
    # Record metrics if available
    if metrics:
        metrics.increment_counter('processing_completed')
    
    return result
```

### 4. Configuration Management

**Use Configuration Service**: Access configuration through the config service.

```python
class MyService(ConfigurableService):
    def _do_initialize(self):
        # Get configuration through service
        config_service = require_service('config', context=self.name)
        
        # Use hierarchical configuration keys
        self.timeout = config_service.get('services.my_service.timeout', 30)
        self.max_retries = config_service.get('services.my_service.max_retries', 3)
        self.enable_caching = config_service.get('services.my_service.enable_caching', True)
```

## Testing with Services

### 1. Service Mocking

Create mock services for testing:

```python
import pytest
from unittest.mock import Mock
from app.core.registry import get_registry, reset_registry

class MockLoggerService:
    def __init__(self):
        self.messages = []
    
    def info(self, message, **kwargs):
        self.messages.append(('INFO', message, kwargs))
    
    def error(self, message, **kwargs):
        self.messages.append(('ERROR', message, kwargs))
    
    def health_check(self):
        return True

@pytest.fixture
def mock_services():
    """Set up mock services for testing."""
    # Reset registry to clean state
    reset_registry()
    registry = get_registry()
    
    # Register mock services
    mock_logger = MockLoggerService()
    registry.register_singleton('logger', mock_logger)
    
    mock_config = Mock()
    mock_config.get.return_value = 'test_value'
    registry.register_singleton('config', mock_config)
    
    yield {
        'logger': mock_logger,
        'config': mock_config
    }
    
    # Clean up after test
    reset_registry()

def test_my_component(mock_services):
    """Test component with mocked services."""
    from myapp.components import MyComponent
    
    component = MyComponent()
    result = component.process_data(['test', 'data'])
    
    # Verify service interactions
    assert len(mock_services['logger'].messages) > 0
    assert mock_services['config'].get.called
```

### 2. Integration Testing

Test service integration:

```python
def test_service_integration():
    """Test that services work together correctly."""
    from app.core.service_registration import register_core_services, initialize_core_services
    
    # Register and initialize services
    registered = register_core_services()
    init_results = initialize_core_services()
    
    # Verify all services initialized successfully
    assert all(init_results.values()), f"Service initialization failed: {init_results}"
    
    # Test service interactions
    registry = get_registry()
    logger = registry.get('logger')
    config = registry.get('config')
    
    # Test that services can interact
    logger.info("Test message")
    config_value = config.get('test.key', 'default')
    
    # Verify health checks
    health_status = registry.health_check()
    assert all(health_status.values()), f"Unhealthy services: {health_status}"
```

### 3. Test Service Lifecycle

Test service initialization and shutdown:

```python
def test_service_lifecycle():
    """Test service lifecycle management."""
    from app.core.service import ServiceLifecycleManager
    
    # Create test service
    test_service = TestService({'test_config': 'value'})
    
    # Test lifecycle
    lifecycle_manager = ServiceLifecycleManager()
    lifecycle_manager.add_service(test_service)
    
    # Test initialization
    lifecycle_manager.initialize_all()
    assert test_service.is_initialized()
    assert test_service.health_check()
    
    # Test shutdown
    lifecycle_manager.shutdown_all()
    assert not test_service.is_initialized()
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. ServiceNotFoundError

**Problem**: Service is not registered in the registry.

```
ServiceNotFoundError: Service 'my_service' not registered
```

**Solutions**:
- Verify service is registered before use
- Check service registration code
- Ensure registration happens during application startup

```python
# Check if service is registered
registry = get_registry()
if not registry.has('my_service'):
    print("Service not registered!")
    print(f"Available services: {registry.list_services()}")

# Register the missing service
registry.register_singleton('my_service', MyService())
```

#### 2. CircularDependencyError

**Problem**: Services have circular dependencies.

```
CircularDependencyError: Circular dependency detected: service_a -> service_b -> service_a
```

**Solutions**:
- Redesign service dependencies to avoid cycles
- Use dependency inversion principle
- Consider splitting services into smaller components

```python
# Bad: Circular dependency
class ServiceA(ConfigurableService):
    def _do_initialize(self):
        self.service_b = require_service('service_b')  # Depends on B

class ServiceB(ConfigurableService):
    def _do_initialize(self):
        self.service_a = require_service('service_a')  # Depends on A

# Good: Remove circular dependency
class ServiceA(ConfigurableService):
    def _do_initialize(self):
        self.shared_service = require_service('shared_service')

class ServiceB(ConfigurableService):
    def _do_initialize(self):
        self.shared_service = require_service('shared_service')

class SharedService(ConfigurableService):
    def _do_initialize(self):
        pass  # No dependencies on A or B
```

#### 3. ServiceInitializationError

**Problem**: Service fails to initialize.

```
ServiceInitializationError: Failed to initialize service 'database': Connection refused
```

**Solutions**:
- Check service configuration
- Verify external dependencies (databases, APIs, etc.)
- Review service initialization code
- Check logs for detailed error information

```python
# Debug service initialization
registry = get_registry()
service_info = registry.get_service_info('database')

if service_info:
    print(f"Service state: {service_info.lifecycle}")
    print(f"Error message: {service_info.error_message}")
    
    # Try to get more details
    if service_info.service_class:
        print(f"Service class: {service_info.service_class}")
    if service_info.dependencies:
        print(f"Dependencies: {service_info.dependencies}")
```

#### 4. Import Errors

**Problem**: Cannot import service modules.

```
ImportError: Failed to import 'my_service_module': No module named 'my_service_module'
```

**Solutions**:
- Verify module path is correct
- Check that module is installed
- Ensure PYTHONPATH includes necessary directories

```python
from app.utils.imports import is_available, get_import_manager

# Check if module is available
if not is_available('my_service_module'):
    print("Module not available for import")
    
    # Get import status
    import_manager = get_import_manager()
    status = import_manager.get_import_status()
    print(f"Failed imports: {status['failed_imports']}")
```

#### 5. Service Health Check Failures

**Problem**: Services report as unhealthy.

```
Service 'cache' health check failed
```

**Solutions**:
- Check service dependencies (network, database, etc.)
- Review service configuration
- Examine service logs for errors
- Verify external services are running

```python
# Debug service health
registry = get_registry()
health_status = registry.health_check()

for service_name, is_healthy in health_status.items():
    if not is_healthy:
        service_info = registry.get_service_info(service_name)
        print(f"Unhealthy service: {service_name}")
        print(f"Error: {service_info.error_message}")
        
        # Try to get the service and check manually
        try:
            service = registry.get(service_name)
            if hasattr(service, 'get_stats'):
                print(f"Service stats: {service.get_stats()}")
        except Exception as e:
            print(f"Cannot get service: {e}")
```

### Debugging Tools

#### 1. Service Registry Inspector

```python
def inspect_registry():
    """Inspect the current state of the service registry."""
    registry = get_registry()
    
    print("=== Service Registry Inspection ===")
    print(f"Registered services: {len(registry.list_services())}")
    
    for service_name in registry.list_services():
        service_info = registry.get_service_info(service_name)
        print(f"\nService: {service_name}")
        print(f"  Type: {service_info.service_type}")
        print(f"  State: {service_info.lifecycle}")
        print(f"  Dependencies: {service_info.dependencies}")
        print(f"  Healthy: {service_info.health_status}")
        if service_info.error_message:
            print(f"  Error: {service_info.error_message}")

# Usage
inspect_registry()
```

#### 2. Dependency Validator

```python
def validate_all_dependencies():
    """Validate all service dependencies."""
    registry = get_registry()
    errors = registry.validate_dependencies()
    
    if errors:
        print("=== Dependency Validation Errors ===")
        for error in errors:
            print(f"❌ {error}")
    else:
        print("✅ All dependencies are valid")
    
    return len(errors) == 0

# Usage
validate_all_dependencies()
```

#### 3. Service Performance Monitor

```python
import time
from contextlib import contextmanager

@contextmanager
def monitor_service_performance(service_name):
    """Monitor service operation performance."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        print(f"Service '{service_name}' operation took {duration:.3f} seconds")

# Usage
with monitor_service_performance('database'):
    database = require_service('database')
    result = database.query("SELECT * FROM users")
```

## Advanced Usage

### 1. Dynamic Service Registration

Register services based on runtime configuration:

```python
def register_dynamic_services(config):
    """Register services based on configuration."""
    registry = get_registry()
    
    # Register different cache backends based on config
    cache_backend = config.get('cache.backend', 'memory')
    
    if cache_backend == 'redis':
        from app.services.redis_cache import RedisCacheService
        cache_service = RedisCacheService(config.get('cache.redis', {}))
    elif cache_backend == 'memcached':
        from app.services.memcached_cache import MemcachedCacheService
        cache_service = MemcachedCacheService(config.get('cache.memcached', {}))
    else:
        from app.services.memory_cache import MemoryCacheService
        cache_service = MemoryCacheService(config.get('cache.memory', {}))
    
    registry.register_singleton('cache', cache_service, dependencies=['config', 'logger'])
```

### 2. Service Decorators

Create decorators for common service patterns:

```python
from functools import wraps

def with_service(service_name, context=None):
    """Decorator to inject service into function."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            service = require_service(service_name, context=context or func.__name__)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator

# Usage
@with_service('logger', context='DataProcessor')
def process_data(logger, data):
    logger.info(f"Processing {len(data)} items")
    # Process data
    return processed_data
```

### 3. Service Proxies

Create proxies for lazy service loading:

```python
class ServiceProxy:
    """Lazy proxy for service access."""
    
    def __init__(self, service_name, context=None):
        self._service_name = service_name
        self._context = context
        self._service = None
    
    def _get_service(self):
        if self._service is None:
            self._service = require_service(self._service_name, context=self._context)
        return self._service
    
    def __getattr__(self, name):
        service = self._get_service()
        return getattr(service, name)

# Usage
class MyComponent:
    def __init__(self):
        # Services are loaded lazily when first accessed
        self.logger = ServiceProxy('logger', context='MyComponent')
        self.cache = ServiceProxy('cache', context='MyComponent')
    
    def do_work(self):
        self.logger.info("Starting work")  # Service loaded here
        # Work implementation
```

### 4. Service Factories with Parameters

Create parameterized service factories:

```python
def create_database_service_factory(connection_pool_size=10):
    """Create a database service factory with custom parameters."""
    
    def factory():
        config = require_service('config', context='DatabaseFactory')
        logger = require_service('logger', context='DatabaseFactory')
        
        db_config = config.get('database', {})
        db_config['pool_size'] = connection_pool_size
        
        return DatabaseService(db_config, logger)
    
    return factory

# Register with custom parameters
registry = get_registry()
db_factory = create_database_service_factory(connection_pool_size=20)
registry.register_factory('database', db_factory, dependencies=['config', 'logger'])
```

This comprehensive guide covers all aspects of using the service registry system. For additional examples and patterns, refer to the existing service implementations in `app/core/services/` and the integration examples in `app/core/integration_example.py`.