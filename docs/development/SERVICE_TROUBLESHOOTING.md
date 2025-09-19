# Service Registry Troubleshooting Guide

## Quick Diagnostic Commands

### Check Service Status
```python
from app.core.registry import get_registry

registry = get_registry()

# List all registered services
print("Registered services:", registry.list_services())

# Check health of all services
health_status = registry.health_check()
print("Health status:", health_status)

# Get detailed service information
for service_name in registry.list_services():
    info = registry.get_service_info(service_name)
    print(f"{service_name}: {info.lifecycle.value} - Healthy: {info.health_status}")
```

### Validate Dependencies
```python
from app.core.registry import get_registry

registry = get_registry()
errors = registry.validate_dependencies()

if errors:
    print("Dependency errors found:")
    for error in errors:
        print(f"  ❌ {error}")
else:
    print("✅ All dependencies are valid")
```

## Common Error Patterns

### 1. ServiceNotFoundError

**Error Message:**
```
ServiceNotFoundError: Service 'cache' not registered
```

**Cause:** The requested service hasn't been registered in the service registry.

**Diagnostic Steps:**
1. Check if service is registered:
   ```python
   registry = get_registry()
   print("Available services:", registry.list_services())
   ```

2. Verify service registration code:
   ```python
   # Check if registration code is being called
   from app.core.service_registration import register_core_services
   registered = register_core_services()
   print("Registered services:", registered)
   ```

**Solutions:**
- Ensure service registration happens during application startup
- Check that the service registration code is being executed
- Verify the service name matches exactly (case-sensitive)

**Example Fix:**
```python
# Add missing service registration
from app.core.registry import get_registry
from app.services.cache_service import CacheService

registry = get_registry()
cache_service = CacheService({'backend': 'memory'})
registry.register_singleton('cache', cache_service)
```

### 2. CircularDependencyError

**Error Message:**
```
CircularDependencyError: Circular dependency detected: service_a -> service_b -> service_c -> service_a
```

**Cause:** Services have circular dependencies that prevent proper initialization order.

**Diagnostic Steps:**
1. Map out service dependencies:
   ```python
   registry = get_registry()
   for service_name in registry.list_services():
       info = registry.get_service_info(service_name)
       print(f"{service_name} depends on: {info.dependencies}")
   ```

2. Visualize dependency graph:
   ```python
   def print_dependency_tree():
       registry = get_registry()
       for service_name in registry.list_services():
           info = registry.get_service_info(service_name)
           print(f"{service_name}")
           for dep in info.dependencies:
               print(f"  └── {dep}")
   ```

**Solutions:**
- Redesign services to remove circular dependencies
- Extract shared functionality into a separate service
- Use dependency inversion principle

**Example Fix:**
```python
# Before: Circular dependency
class ServiceA(ConfigurableService):
    def _do_initialize(self):
        self.service_b = require_service('service_b')

class ServiceB(ConfigurableService):
    def _do_initialize(self):
        self.service_a = require_service('service_a')

# After: Remove circular dependency
class ServiceA(ConfigurableService):
    def _do_initialize(self):
        self.shared = require_service('shared_service')

class ServiceB(ConfigurableService):
    def _do_initialize(self):
        self.shared = require_service('shared_service')

class SharedService(ConfigurableService):
    def _do_initialize(self):
        pass  # No circular dependencies
```

### 3. ServiceInitializationError

**Error Message:**
```
ServiceInitializationError: Failed to initialize service 'database': Connection refused
```

**Cause:** Service initialization failed due to configuration, network, or dependency issues.

**Diagnostic Steps:**
1. Check service configuration:
   ```python
   config = require_service('config')
   db_config = config.get('database', {})
   print("Database config:", db_config)
   ```

2. Verify external dependencies:
   ```python
   # Test database connection manually
   import psycopg2
   try:
       conn = psycopg2.connect(
           host=db_config['host'],
           port=db_config['port'],
           database=db_config['database'],
           user=db_config['user'],
           password=db_config['password']
       )
       print("✅ Database connection successful")
       conn.close()
   except Exception as e:
       print(f"❌ Database connection failed: {e}")
   ```

3. Check service logs:
   ```python
   registry = get_registry()
   service_info = registry.get_service_info('database')
   if service_info.error_message:
       print(f"Service error: {service_info.error_message}")
   ```

**Solutions:**
- Verify configuration values are correct
- Check that external services (databases, APIs) are running
- Ensure network connectivity
- Review service initialization code for bugs

### 4. ServiceRequiredError

**Error Message:**
```
ServiceRequiredError: Required service 'llm_provider' is not available (Context: RecommendationEngine)
```

**Cause:** A component tried to access a required service that isn't available.

**Diagnostic Steps:**
1. Check if service is registered:
   ```python
   registry = get_registry()
   if registry.has('llm_provider'):
       print("Service is registered")
       try:
           service = registry.get('llm_provider')
           print("Service can be retrieved")
       except Exception as e:
           print(f"Service retrieval failed: {e}")
   else:
       print("Service is not registered")
   ```

2. Check service health:
   ```python
   health = registry.health_check('llm_provider')
   print(f"Service health: {health}")
   ```

**Solutions:**
- Register the missing service
- Check service initialization order
- Verify service dependencies are met
- Consider making the service optional if appropriate

**Example Fix:**
```python
# Make service optional if it's not critical
from app.utils.imports import optional_service

class RecommendationEngine:
    def __init__(self):
        # Use optional_service instead of require_service
        self.llm_provider = optional_service('llm_provider', context='RecommendationEngine')
    
    def generate_recommendation(self, data):
        if self.llm_provider:
            return self.llm_provider.generate(data)
        else:
            # Fallback to rule-based recommendations
            return self._rule_based_recommendation(data)
```

### 5. Import Errors

**Error Message:**
```
ImportError: Failed to import 'redis': No module named 'redis'
```

**Cause:** Required Python packages are not installed.

**Diagnostic Steps:**
1. Check import availability:
   ```python
   from app.utils.imports import is_available
   
   if is_available('redis'):
       print("Redis module is available")
   else:
       print("Redis module is not available")
   ```

2. Check import manager status:
   ```python
   from app.utils.imports import get_import_manager
   
   manager = get_import_manager()
   status = manager.get_import_status()
   print("Failed imports:", status['failed_imports'])
   ```

**Solutions:**
- Install missing packages: `pip install redis`
- Update requirements.txt
- Use optional imports for non-critical dependencies

**Example Fix:**
```python
# Use try_import_service for optional dependencies
from app.utils.imports import try_import_service

# Try to register Redis cache service
if try_import_service('redis', 'redis_cache', 'Redis'):
    print("Redis cache service registered")
else:
    print("Redis not available, using memory cache")
    # Register fallback service
    registry.register_singleton('cache', MemoryCacheService())
```

## Performance Issues

### 1. Slow Service Resolution

**Symptoms:**
- Application startup is slow
- Service access takes too long

**Diagnostic Steps:**
```python
import time
from app.utils.imports import require_service

# Measure service resolution time
start_time = time.time()
service = require_service('slow_service')
resolution_time = time.time() - start_time
print(f"Service resolution took {resolution_time:.3f} seconds")
```

**Solutions:**
- Use singleton pattern for expensive services
- Implement lazy initialization
- Cache service instances
- Optimize service initialization code

### 2. Memory Usage Issues

**Symptoms:**
- High memory usage
- Memory leaks

**Diagnostic Steps:**
```python
import psutil
import gc

# Check memory usage
process = psutil.Process()
memory_info = process.memory_info()
print(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")

# Check service instances
registry = get_registry()
for service_name in registry.list_services():
    info = registry.get_service_info(service_name)
    if info.instance:
        print(f"{service_name}: {type(info.instance).__name__}")
```

**Solutions:**
- Use factory pattern for short-lived services
- Implement proper cleanup in service shutdown
- Monitor service lifecycle
- Use weak references where appropriate

## Configuration Issues

### 1. Missing Configuration

**Error Message:**
```
KeyError: 'database'
```

**Diagnostic Steps:**
```python
config = require_service('config')

# Check available configuration keys
print("Available config sections:", list(config.get_all().keys()))

# Check specific configuration
db_config = config.get('database', None)
if db_config is None:
    print("Database configuration is missing")
else:
    print("Database config:", db_config)
```

**Solutions:**
- Add missing configuration to config files
- Provide default values
- Validate configuration at startup

### 2. Invalid Configuration Values

**Diagnostic Steps:**
```python
def validate_service_config(service_name, required_keys):
    """Validate service configuration."""
    config = require_service('config')
    service_config = config.get(service_name, {})
    
    missing_keys = []
    for key in required_keys:
        if key not in service_config:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"Missing config keys for {service_name}: {missing_keys}")
    else:
        print(f"Configuration for {service_name} is complete")

# Usage
validate_service_config('database', ['host', 'port', 'database', 'user'])
```

## Health Check Issues

### 1. Services Reporting Unhealthy

**Diagnostic Steps:**
```python
def diagnose_unhealthy_services():
    """Diagnose why services are reporting as unhealthy."""
    registry = get_registry()
    health_status = registry.health_check()
    
    for service_name, is_healthy in health_status.items():
        if not is_healthy:
            print(f"\n❌ Unhealthy service: {service_name}")
            
            service_info = registry.get_service_info(service_name)
            print(f"   State: {service_info.lifecycle.value}")
            print(f"   Error: {service_info.error_message}")
            
            # Try to get more details
            try:
                service = registry.get(service_name)
                if hasattr(service, 'get_stats'):
                    stats = service.get_stats()
                    print(f"   Stats: {stats}")
            except Exception as e:
                print(f"   Cannot access service: {e}")

diagnose_unhealthy_services()
```

**Solutions:**
- Check external dependencies (databases, APIs, network)
- Verify service configuration
- Review service health check implementation
- Check service logs for errors

## Testing Issues

### 1. Services Not Available in Tests

**Problem:** Services work in production but not in tests.

**Solution:**
```python
import pytest
from app.core.registry import get_registry, reset_registry

@pytest.fixture(autouse=True)
def setup_test_services():
    """Set up services for testing."""
    # Reset registry to clean state
    reset_registry()
    
    # Register minimal test services
    registry = get_registry()
    
    # Mock logger
    class MockLogger:
        def info(self, msg): pass
        def error(self, msg): pass
        def debug(self, msg): pass
        def health_check(self): return True
    
    registry.register_singleton('logger', MockLogger())
    
    # Mock config
    class MockConfig:
        def get(self, key, default=None):
            return {'test': True}.get(key, default)
        def health_check(self): return True
    
    registry.register_singleton('config', MockConfig())
    
    yield
    
    # Clean up after test
    reset_registry()
```

### 2. Service Mocking Issues

**Problem:** Difficulty mocking services for tests.

**Solution:**
```python
from unittest.mock import Mock, patch

def test_with_mocked_service():
    """Test with properly mocked service."""
    
    # Create mock service
    mock_service = Mock()
    mock_service.process_data.return_value = "mocked_result"
    mock_service.health_check.return_value = True
    
    # Register mock in registry
    registry = get_registry()
    registry.register_singleton('data_processor', mock_service)
    
    # Test component that uses the service
    component = MyComponent()
    result = component.do_work()
    
    # Verify mock was called
    mock_service.process_data.assert_called_once()
    assert result == "mocked_result"
```

## Debugging Tools

### Service Registry Inspector

```python
def inspect_service_registry():
    """Comprehensive service registry inspection."""
    registry = get_registry()
    
    print("=" * 50)
    print("SERVICE REGISTRY INSPECTION")
    print("=" * 50)
    
    services = registry.list_services()
    print(f"Total services: {len(services)}")
    
    # Group services by state
    states = {}
    for service_name in services:
        info = registry.get_service_info(service_name)
        state = info.lifecycle.value
        if state not in states:
            states[state] = []
        states[state].append(service_name)
    
    print("\nServices by state:")
    for state, service_list in states.items():
        print(f"  {state}: {len(service_list)} services")
        for service_name in service_list:
            print(f"    - {service_name}")
    
    # Check health
    print("\nHealth status:")
    health_status = registry.health_check()
    healthy_count = sum(1 for h in health_status.values() if h)
    print(f"  Healthy: {healthy_count}/{len(health_status)}")
    
    unhealthy = [name for name, healthy in health_status.items() if not healthy]
    if unhealthy:
        print(f"  Unhealthy services: {unhealthy}")
    
    # Check dependencies
    print("\nDependency validation:")
    errors = registry.validate_dependencies()
    if errors:
        print("  ❌ Dependency errors found:")
        for error in errors:
            print(f"    - {error}")
    else:
        print("  ✅ All dependencies are valid")
    
    print("=" * 50)

# Usage
inspect_service_registry()
```

### Service Performance Monitor

```python
import time
from contextlib import contextmanager

class ServicePerformanceMonitor:
    """Monitor service performance and usage."""
    
    def __init__(self):
        self.metrics = {}
    
    @contextmanager
    def monitor_operation(self, service_name, operation):
        """Monitor a service operation."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            if service_name not in self.metrics:
                self.metrics[service_name] = {}
            if operation not in self.metrics[service_name]:
                self.metrics[service_name][operation] = []
            
            self.metrics[service_name][operation].append(duration)
    
    def get_stats(self):
        """Get performance statistics."""
        stats = {}
        for service_name, operations in self.metrics.items():
            stats[service_name] = {}
            for operation, durations in operations.items():
                stats[service_name][operation] = {
                    'count': len(durations),
                    'avg_duration': sum(durations) / len(durations),
                    'max_duration': max(durations),
                    'min_duration': min(durations)
                }
        return stats

# Usage
monitor = ServicePerformanceMonitor()

with monitor.monitor_operation('database', 'query'):
    db = require_service('database')
    result = db.query("SELECT * FROM users")

print("Performance stats:", monitor.get_stats())
```

### Dependency Graph Visualizer

```python
def visualize_dependencies():
    """Create a text-based dependency graph."""
    registry = get_registry()
    
    print("SERVICE DEPENDENCY GRAPH")
    print("=" * 30)
    
    # Build dependency graph
    graph = {}
    for service_name in registry.list_services():
        info = registry.get_service_info(service_name)
        graph[service_name] = info.dependencies
    
    # Find root services (no dependencies)
    roots = [name for name, deps in graph.items() if not deps]
    
    def print_tree(service_name, level=0, visited=None):
        if visited is None:
            visited = set()
        
        if service_name in visited:
            print("  " * level + f"└── {service_name} (circular)")
            return
        
        visited.add(service_name)
        print("  " * level + f"└── {service_name}")
        
        # Find services that depend on this one
        dependents = [name for name, deps in graph.items() if service_name in deps]
        for dependent in dependents:
            print_tree(dependent, level + 1, visited.copy())
    
    # Print trees starting from root services
    for root in roots:
        print_tree(root)
    
    # Print orphaned services
    all_referenced = set()
    for deps in graph.values():
        all_referenced.update(deps)
    
    orphaned = set(graph.keys()) - all_referenced - set(roots)
    if orphaned:
        print("\nOrphaned services (not referenced by others):")
        for service in orphaned:
            print(f"  - {service}")

# Usage
visualize_dependencies()
```

This troubleshooting guide provides comprehensive diagnostic tools and solutions for common service registry issues. Keep this guide handy when debugging service-related problems in your application.