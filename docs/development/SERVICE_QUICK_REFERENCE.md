# Service Registry Quick Reference

## Essential Imports

```python
from app.utils.imports import require_service, optional_service
from app.core.registry import get_registry
from app.core.service import ConfigurableService
```

## Basic Service Usage

```python
# Get required service (raises error if not available)
logger = require_service('logger', context='MyComponent')

# Get optional service (returns None if not available)
cache = optional_service('cache', context='MyComponent')
```

## Service Registration

```python
registry = get_registry()

# Singleton service
registry.register_singleton('my_service', service_instance)

# Factory service
registry.register_factory('my_service', factory_function)

# Class with auto-injection
registry.register_class('my_service', ServiceClass)
```

## Creating a Service

```python
class MyService(ConfigurableService):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "my_service")
        self._dependencies = ["logger", "config"]
    
    def _do_initialize(self) -> None:
        self.logger = require_service('logger', context=self.name)
        # Initialize service
    
    def _do_shutdown(self) -> None:
        # Clean up resources
        pass
    
    def _do_health_check(self) -> bool:
        return True  # Check if service is healthy
```

## Common Patterns

### Service with Optional Dependencies
```python
def _do_initialize(self) -> None:
    self.logger = require_service('logger', context=self.name)
    self.cache = optional_service('cache', context=self.name)
    
    if self.cache:
        self.logger.info("Cache available")
    else:
        self.logger.info("Running without cache")
```

### Factory Service
```python
def create_llm_provider():
    config = require_service('config')
    provider_type = config.get('llm.provider', 'openai')
    return LLMProviderFactory.create(provider_type)

registry.register_factory('llm_provider', create_llm_provider)
```

### Service Health Check
```python
registry = get_registry()
health_status = registry.health_check()

for service_name, is_healthy in health_status.items():
    if not is_healthy:
        print(f"⚠️ {service_name} is unhealthy")
```

## Debugging Commands

```python
# List all services
registry = get_registry()
print("Services:", registry.list_services())

# Check service info
info = registry.get_service_info('my_service')
print(f"State: {info.lifecycle}, Healthy: {info.health_status}")

# Validate dependencies
errors = registry.validate_dependencies()
if errors:
    print("Dependency errors:", errors)
```

## Testing Setup

```python
import pytest
from app.core.registry import get_registry, reset_registry

@pytest.fixture(autouse=True)
def setup_test_services():
    reset_registry()
    registry = get_registry()
    
    # Register mock services
    registry.register_singleton('logger', MockLogger())
    registry.register_singleton('config', MockConfig())
    
    yield
    reset_registry()
```

## Error Handling

```python
from app.utils.imports import ServiceRequiredError

try:
    service = require_service('critical_service')
except ServiceRequiredError as e:
    logger.error(f"Critical service not available: {e}")
    # Handle gracefully or fail fast
```

## Configuration Access

```python
class MyService(ConfigurableService):
    def _do_initialize(self):
        # Access config through service
        config = require_service('config', context=self.name)
        
        # Get config values with defaults
        timeout = config.get('my_service.timeout', 30)
        retries = config.get('my_service.retries', 3)
```

## Common Service Names

- `config` - Configuration service
- `logger` - Logging service  
- `cache` - Cache service
- `database` - Database service
- `security_validator` - Input validation
- `advanced_prompt_defender` - Prompt attack defense
- `llm_provider_factory` - LLM provider factory
- `diagram_service_factory` - Diagram generation
- `pattern_loader` - Pattern management
- `audit_logger` - Audit logging

## Troubleshooting Checklist

1. **Service not found**: Check if service is registered
2. **Circular dependency**: Review service dependencies
3. **Initialization failed**: Check service configuration and logs
4. **Health check failed**: Verify external dependencies (DB, network)
5. **Import errors**: Ensure required packages are installed

## Best Practices

- ✅ Use `require_service` for critical dependencies
- ✅ Use `optional_service` for nice-to-have features
- ✅ Always provide context when getting services
- ✅ Implement proper health checks
- ✅ Handle service failures gracefully
- ❌ Don't create services directly in components
- ❌ Don't ignore service health check failures
- ❌ Don't create circular dependencies