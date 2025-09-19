# Dependency Management Guide

## Overview

This guide provides comprehensive information on managing dependencies in the AAA (Automated AI Assessment) system. The system uses a sophisticated dependency management approach that eliminates fallback imports, provides clear error handling, and ensures reliable service availability through a centralized service registry.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Adding New Dependencies](#adding-new-dependencies)
3. [Dependency Validation System](#dependency-validation-system)
4. [Required vs Optional Dependencies](#required-vs-optional-dependencies)
5. [Migration Guide for Existing Code](#migration-guide-for-existing-code)
6. [Configuration Management](#configuration-management)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Topics](#advanced-topics)

## Quick Start

### Basic Dependency Usage

```python
from app.utils.imports import require_service, optional_service

# Get a required dependency (raises error if not available)
logger = require_service('logger', context='MyComponent')

# Get an optional dependency (returns None if not available)
cache = optional_service('cache', context='MyComponent')
if cache:
    cache.set('key', 'value')
```

### Check Dependency Availability

```python
from app.core.dependencies import check_dependency

if check_dependency('redis'):
    # Redis is available, use caching features
    pass
else:
    # Redis not available, use memory cache
    pass
```

## Adding New Dependencies

### Step 1: Define the Dependency

Add your dependency to `config/dependencies.yaml`:

```yaml
dependencies:
  optional:  # or 'required' or 'development'
    - name: "my_new_package"
      version_constraint: ">=1.0.0"
      import_name: "my_package"  # How to import it
      installation_name: "my-package"  # pip install name
      purpose: "Description of what this package does"
      alternatives: ["alternative1", "alternative2"]
      category: "category_name"
      documentation_url: "https://docs.example.com"
      features_enabled: ["feature1", "feature2"]
      system_requirements:
        - "system dependency if needed"
      installation_notes: |
        Special installation instructions if needed
```

### Step 2: Register the Service (if applicable)

If your dependency provides a service, register it in `config/services.yaml`:

```yaml
services:
  my_service:
    class_path: "app.services.my_service.MyService"
    singleton: true  # or false for factory pattern
    dependencies: ["config", "logger"]  # Service dependencies
    config:
      # Service-specific configuration
      setting1: "value1"
      setting2: 42
    health_check:
      enabled: true
      interval_seconds: 300
```

### Step 3: Create Service Implementation (if applicable)

```python
# app/services/my_service.py
from typing import Dict, Any
from app.core.service import ConfigurableService
from app.utils.imports import require_service

class MyService(ConfigurableService):
    """Service for handling my_package functionality."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "my_service")
        self._client = None
    
    def _do_initialize(self) -> None:
        """Initialize the service."""
        try:
            import my_package
            self.logger = require_service('logger', context=self.name)
            
            # Initialize your service
            self._client = my_package.Client(
                api_key=self.get_config('api_key'),
                timeout=self.get_config('timeout', 30)
            )
            
            self.logger.info(f"{self.name} service initialized successfully")
            
        except ImportError as e:
            raise ServiceInitializationError(
                f"Required package 'my_package' not available: {e}"
            )
    
    def _do_shutdown(self) -> None:
        """Shutdown the service."""
        if self._client:
            self._client.close()
            self._client = None
    
    def _do_health_check(self) -> bool:
        """Check if service is healthy."""
        try:
            return self._client and self._client.ping()
        except Exception:
            return False
    
    def do_something(self, data: str) -> str:
        """Example service method."""
        if not self._client:
            raise ServiceNotAvailableError("Service not initialized")
        
        return self._client.process(data)
```

### Step 4: Register Service at Startup

Add service registration to `app/core/service_registration.py`:

```python
def register_my_services():
    """Register my custom services."""
    registry = get_registry()
    
    # Check if dependency is available
    if check_dependency('my_new_package'):
        from app.services.my_service import MyService
        
        def create_my_service():
            config_service = registry.get('config')
            service_config = config_service.get('services.my_service', {})
            return MyService(service_config)
        
        registry.register_factory('my_service', create_my_service, 
                                dependencies=['config'])
        logger.info("My service registered successfully")
    else:
        logger.warning("my_new_package not available, my_service disabled")
```

### Step 5: Update Feature Dependencies

Add your dependency to feature mappings in `config/dependencies.yaml`:

```yaml
feature_dependencies:
  my_feature:
    required: []  # Required dependencies for this feature
    optional: ["my_new_package"]  # Optional dependencies
    
dependency_groups:
  my_group:
    description: "Dependencies for my feature"
    dependencies: ["my_new_package"]
```

## Dependency Validation System

### How Validation Works

The dependency validation system automatically:

1. **Checks availability**: Verifies all dependencies can be imported
2. **Validates versions**: Ensures version constraints are met
3. **Generates reports**: Provides detailed dependency status
4. **Creates instructions**: Generates installation commands for missing dependencies

### Validation at Startup

```python
# In app/core/startup.py
from app.core.dependencies import validate_startup_dependencies

def validate_system_dependencies():
    """Validate all system dependencies at startup."""
    result = validate_startup_dependencies(include_dev=False)
    
    if result.has_errors():
        logger.error("Critical dependency validation failed:")
        for error in result.missing_required:
            logger.error(f"  Missing required: {error}")
        for error in result.version_conflicts:
            logger.error(f"  Version conflict: {error}")
        
        print(result.installation_instructions)
        raise SystemExit(1)
    
    if result.has_warnings():
        logger.warning("Dependency validation warnings:")
        for warning in result.warnings:
            logger.warning(f"  {warning}")
        for missing in result.missing_optional:
            logger.info(f"  Optional dependency missing: {missing}")
    
    logger.info("Dependency validation completed successfully")
```

### Manual Validation

```python
from app.core.dependencies import get_dependency_validator

# Get validator instance
validator = get_dependency_validator()

# Validate all dependencies
result = validator.validate_all(include_dev=True)

# Validate specific dependency
is_valid, error = validator.validate_dependency('openai')

# Get dependency information
dep_info = validator.get_dependency_info('openai')
if dep_info:
    print(f"Purpose: {dep_info.purpose}")
    print(f"Alternatives: {dep_info.alternatives}")

# Generate dependency report
report = validator.get_dependency_report()
print(report)
```

### Version Constraint Syntax

The system supports standard version constraint operators:

```yaml
version_constraint: ">=1.0.0"    # Greater than or equal
version_constraint: "<=2.0.0"    # Less than or equal  
version_constraint: "==1.5.0"    # Exact version
version_constraint: "!=1.3.0"    # Not equal
version_constraint: ">1.0.0"     # Greater than
version_constraint: "<2.0.0"     # Less than
```

## Required vs Optional Dependencies

### Required Dependencies

Required dependencies are **critical** for core system functionality. The system will **fail to start** if these are missing.

**Characteristics:**
- Core functionality depends on them
- System cannot operate without them
- Installation is mandatory
- Missing required dependencies cause startup failure

**Examples:**
```yaml
dependencies:
  required:
    - name: "streamlit"
      purpose: "Web UI framework - core functionality"
    - name: "fastapi" 
      purpose: "API framework - core backend"
    - name: "pydantic"
      purpose: "Data validation - core data handling"
```

**Usage Pattern:**
```python
# Required services always available after startup
logger = require_service('logger')  # Will never be None
config = require_service('config')  # Will never be None
```

### Optional Dependencies

Optional dependencies **enhance** functionality but are **not critical**. The system gracefully degrades when they're missing.

**Characteristics:**
- Provide enhanced or additional features
- System can operate without them (with reduced functionality)
- Installation is recommended but not mandatory
- Missing optional dependencies generate warnings, not errors

**Examples:**
```yaml
dependencies:
  optional:
    - name: "openai"
      purpose: "OpenAI LLM integration - enhanced AI features"
      features_enabled: ["gpt_models", "embeddings"]
    - name: "redis"
      purpose: "Distributed caching - performance enhancement"
      features_enabled: ["distributed_cache", "session_storage"]
    - name: "diagrams"
      purpose: "Infrastructure diagrams - visualization enhancement"
      features_enabled: ["infrastructure_diagrams"]
```

**Usage Pattern:**
```python
# Optional services may be None
llm_provider = optional_service('llm_provider', provider='openai')
if llm_provider:
    # Use enhanced LLM features
    response = llm_provider.generate(prompt)
else:
    # Graceful degradation
    response = "LLM service not available"

cache = optional_service('cache')
if cache:
    # Use caching for performance
    cached_result = cache.get(key)
    if cached_result:
        return cached_result
    result = expensive_operation()
    cache.set(key, result)
    return result
else:
    # No caching, direct computation
    return expensive_operation()
```

### Development Dependencies

Development dependencies are only needed during development, testing, or CI/CD.

**Examples:**
```yaml
dependencies:
  development:
    - name: "pytest"
      purpose: "Testing framework"
    - name: "mypy"
      purpose: "Static type checking"
    - name: "black"
      purpose: "Code formatting"
```

### Decision Guidelines

**Use Required when:**
- Core functionality breaks without it
- No reasonable fallback exists
- All deployment environments need it
- System cannot provide value without it

**Use Optional when:**
- Feature enhancement only
- Graceful degradation is possible
- Not all environments need it
- Alternative implementations exist

**Use Development when:**
- Only needed for development/testing
- Not needed in production
- Part of development workflow only

## Migration Guide for Existing Code

### Migrating from Fallback Imports

#### Before: Fallback Import Pattern
```python
# ❌ Old pattern - avoid this
try:
    from app.utils.logger import app_logger
except ImportError:
    import logging
    app_logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

if OPENAI_AVAILABLE:
    # Use OpenAI
    pass
else:
    # Fallback behavior
    pass
```

#### After: Service Registry Pattern
```python
# ✅ New pattern - use this
from app.utils.imports import require_service, optional_service

# Required service - always available after startup
app_logger = require_service('logger', context='MyComponent')

# Optional service - may be None
llm_provider = optional_service('llm_provider', provider='openai')
if llm_provider:
    # Use LLM provider
    response = llm_provider.generate(prompt)
else:
    # Graceful degradation
    response = "LLM service not available"
```

### Step-by-Step Migration Process

#### Step 1: Identify Fallback Patterns

Search for these patterns in your code:
```bash
# Find try/except import patterns
grep -r "try:" . --include="*.py" | grep -A 5 "import"

# Find availability flags
grep -r "_AVAILABLE" . --include="*.py"

# Find conditional imports
grep -r "ImportError" . --include="*.py"
```

#### Step 2: Categorize Dependencies

For each fallback import, determine:
- Is this a **required** or **optional** dependency?
- What **purpose** does it serve?
- What are the **alternatives**?
- What **features** are enabled/disabled?

#### Step 3: Register Dependencies

Add to `config/dependencies.yaml`:
```yaml
dependencies:
  optional:  # or required
    - name: "your_package"
      version_constraint: ">=1.0.0"
      import_name: "your_package"
      purpose: "What this package does"
      alternatives: ["alternative1", "alternative2"]
      features_enabled: ["feature1", "feature2"]
```

#### Step 4: Create Service (if needed)

If the dependency provides functionality used across the application:

```python
# app/services/your_service.py
from app.core.service import ConfigurableService

class YourService(ConfigurableService):
    def __init__(self, config):
        super().__init__(config, "your_service")
    
    def _do_initialize(self):
        try:
            import your_package
            self._client = your_package.Client()
        except ImportError:
            raise ServiceInitializationError("your_package not available")
    
    def your_method(self, data):
        return self._client.process(data)
```

#### Step 5: Register Service

```python
# In app/core/service_registration.py
def register_your_service():
    if check_dependency('your_package'):
        registry = get_registry()
        registry.register_singleton('your_service', YourService)
```

#### Step 6: Update Usage

Replace fallback patterns:
```python
# Before
try:
    import your_package
    result = your_package.process(data)
except ImportError:
    result = fallback_process(data)

# After
your_service = optional_service('your_service')
if your_service:
    result = your_service.your_method(data)
else:
    result = fallback_process(data)
```

#### Step 7: Test Migration

```python
# Test with dependency available
def test_with_dependency():
    # Ensure service is registered
    assert optional_service('your_service') is not None
    
    # Test functionality
    service = optional_service('your_service')
    result = service.your_method("test_data")
    assert result is not None

# Test without dependency
def test_without_dependency():
    # Mock missing dependency
    with patch('app.core.dependencies.check_dependency', return_value=False):
        service = optional_service('your_service')
        assert service is None
        
        # Test graceful degradation
        result = fallback_process("test_data")
        assert result is not None
```

### Common Migration Patterns

#### Pattern 1: Logger Migration
```python
# Before
try:
    from app.utils.logger import app_logger
except ImportError:
    import logging
    app_logger = logging.getLogger(__name__)

# After
from app.utils.imports import require_service
app_logger = require_service('logger', context='MyModule')
```

#### Pattern 2: Optional Feature Migration
```python
# Before
try:
    import redis
    cache = redis.Redis()
    CACHE_AVAILABLE = True
except ImportError:
    cache = None
    CACHE_AVAILABLE = False

def get_data(key):
    if CACHE_AVAILABLE and cache:
        cached = cache.get(key)
        if cached:
            return cached
    
    data = expensive_operation()
    
    if CACHE_AVAILABLE and cache:
        cache.set(key, data)
    
    return data

# After
from app.utils.imports import optional_service

def get_data(key):
    cache = optional_service('cache')
    
    if cache:
        cached = cache.get(key)
        if cached:
            return cached
    
    data = expensive_operation()
    
    if cache:
        cache.set(key, data)
    
    return data
```

#### Pattern 3: Provider Factory Migration
```python
# Before
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

def get_llm_provider():
    if OPENAI_AVAILABLE:
        return openai.OpenAI()
    elif ANTHROPIC_AVAILABLE:
        return anthropic.Anthropic()
    else:
        raise RuntimeError("No LLM provider available")

# After
from app.utils.imports import require_service

def get_llm_provider():
    factory = require_service('llm_provider_factory')
    return factory.create_provider()  # Handles availability internally
```

## Configuration Management

### Dependency Configuration Files

#### `config/dependencies.yaml`
Central registry of all system dependencies with metadata:

```yaml
dependencies:
  required:
    - name: "package_name"
      version_constraint: ">=1.0.0"
      import_name: "import_name"
      installation_name: "pip-package-name"
      purpose: "What this package does"
      alternatives: ["alt1", "alt2"]
      category: "category"
      documentation_url: "https://docs.example.com"

feature_dependencies:
  feature_name:
    required: ["req1", "req2"]
    optional: ["opt1", "opt2"]

dependency_groups:
  group_name:
    description: "Group description"
    dependencies: ["dep1", "dep2"]
```

#### `config/services.yaml`
Service configuration and registration:

```yaml
services:
  service_name:
    class_path: "app.services.service_module.ServiceClass"
    singleton: true
    dependencies: ["dep1", "dep2"]
    config:
      setting1: "value1"
      setting2: 42
    health_check:
      enabled: true
      interval_seconds: 300

environments:
  development:
    service_name:
      config:
        debug: true
  production:
    service_name:
      config:
        debug: false
```

### Environment-Specific Configuration

```yaml
# In config/dependencies.yaml
environments:
  development:
    required_groups: ["minimal", "development"]
    optional_groups: ["standard"]
    
  testing:
    required_groups: ["minimal", "development"]
    optional_groups: []
    
  production:
    required_groups: ["standard"]
    optional_groups: ["full"]
```

### Loading Configuration

```python
from app.core.dependencies import get_dependency_validator
from app.config import get_config

# Load environment-specific dependencies
config = get_config()
environment = config.get('environment', 'development')

validator = get_dependency_validator()
# Validator automatically loads environment-specific requirements
```

## Best Practices

### 1. Dependency Design Principles

#### Minimize Required Dependencies
- Keep required dependencies to absolute minimum
- Prefer optional dependencies with graceful degradation
- Consider alternatives and fallbacks

#### Clear Purpose Definition
```yaml
# Good: Clear, specific purpose
purpose: "Redis client for distributed caching and session storage"

# Avoid: Vague purpose
purpose: "Database stuff"
```

#### Proper Categorization
```yaml
categories:
  - web_framework      # FastAPI, Streamlit
  - llm_provider      # OpenAI, Anthropic
  - visualization     # Diagrams, Graphviz
  - caching          # Redis, Memcached
  - networking       # Requests, HTTPX
  - ml               # Scikit-learn, NumPy
  - testing          # Pytest, Mock
  - development_tools # Black, MyPy
```

### 2. Service Design Patterns

#### Interface Segregation
```python
# Good: Specific interfaces
class CacheProvider(Protocol):
    def get(self, key: str) -> Optional[str]: ...
    def set(self, key: str, value: str, ttl: int = 3600) -> bool: ...

class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str: ...
    def get_embeddings(self, text: str) -> List[float]: ...

# Avoid: Monolithic interfaces
class ServiceProvider(Protocol):
    def do_everything(self, *args, **kwargs) -> Any: ...
```

#### Graceful Degradation
```python
def enhanced_analysis(data):
    """Perform analysis with optional enhancements."""
    # Core analysis (always available)
    result = basic_analysis(data)
    
    # Optional ML enhancement
    ml_service = optional_service('ml_service')
    if ml_service:
        result = ml_service.enhance_analysis(result)
    
    # Optional caching
    cache = optional_service('cache')
    if cache:
        cache.set(f"analysis_{hash(data)}", result)
    
    return result
```

### 3. Error Handling

#### Clear Error Messages
```python
# Good: Actionable error message
def require_llm_provider():
    provider = optional_service('llm_provider')
    if not provider:
        raise ServiceNotAvailableError(
            "LLM provider not available. Install with: pip install openai anthropic"
        )
    return provider

# Avoid: Vague error message
def require_llm_provider():
    provider = optional_service('llm_provider')
    if not provider:
        raise Exception("LLM not working")
    return provider
```

#### Proper Exception Hierarchy
```python
class DependencyError(Exception):
    """Base class for dependency-related errors."""
    pass

class ServiceNotAvailableError(DependencyError):
    """Service is not available due to missing dependencies."""
    pass

class ServiceInitializationError(DependencyError):
    """Service failed to initialize properly."""
    pass
```

### 4. Testing Strategies

#### Mock Services for Testing
```python
@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    mock_service = Mock()
    mock_service.generate.return_value = "Mock response"
    
    with patch('app.utils.imports.optional_service') as mock_optional:
        mock_optional.return_value = mock_service
        yield mock_service

def test_with_llm_service(mock_llm_service):
    """Test functionality with LLM service available."""
    result = process_with_llm("test input")
    assert result == "Mock response"
    mock_llm_service.generate.assert_called_once()

def test_without_llm_service():
    """Test graceful degradation without LLM service."""
    with patch('app.utils.imports.optional_service', return_value=None):
        result = process_with_llm("test input")
        assert result == "Fallback response"
```

#### Dependency Validation Tests
```python
def test_dependency_validation():
    """Test that all required dependencies are available."""
    from app.core.dependencies import validate_startup_dependencies
    
    result = validate_startup_dependencies()
    
    # Should not have missing required dependencies
    assert len(result.missing_required) == 0, f"Missing required: {result.missing_required}"
    
    # Version conflicts should be resolved
    assert len(result.version_conflicts) == 0, f"Version conflicts: {result.version_conflicts}"
```

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Service Not Found
```
ServiceNotFoundError: Service 'my_service' not registered
```

**Diagnosis:**
```python
from app.core.registry import get_registry

registry = get_registry()
print(f"Available services: {registry.list_services()}")
print(f"Service registered: {registry.has('my_service')}")
```

**Solutions:**
1. Ensure service is registered during startup
2. Check dependency is available: `check_dependency('package_name')`
3. Verify service registration code is executed
4. Check for typos in service name

#### Issue 2: Import Errors
```
ImportError: No module named 'package_name'
```

**Diagnosis:**
```python
from app.core.dependencies import get_dependency_validator

validator = get_dependency_validator()
is_valid, error = validator.validate_dependency('package_name')
print(f"Valid: {is_valid}, Error: {error}")

# Get installation instructions
if not is_valid:
    instructions = validator.get_installation_instructions(['package_name'])
    print(instructions)
```

**Solutions:**
1. Install missing package: `pip install package_name`
2. Check package name spelling
3. Verify virtual environment is activated
4. Check requirements.txt includes the package

#### Issue 3: Version Conflicts
```
Version conflict: package_name: installed version 1.0.0 does not satisfy constraint >=2.0.0
```

**Diagnosis:**
```python
import package_name
print(f"Installed version: {package_name.__version__}")

validator = get_dependency_validator()
dep_info = validator.get_dependency_info('package_name')
print(f"Required version: {dep_info.version_constraint}")
```

**Solutions:**
1. Update package: `pip install --upgrade package_name`
2. Check if constraint is too strict
3. Verify compatibility with other packages
4. Consider using version ranges instead of exact versions

#### Issue 4: Service Initialization Failure
```
ServiceInitializationError: Failed to initialize service 'my_service'
```

**Diagnosis:**
```python
from app.core.registry import get_registry

registry = get_registry()
service_info = registry.get_service_info('my_service')
print(f"Service state: {service_info.lifecycle}")
print(f"Error: {service_info.error_message}")

# Check service health
health_status = registry.health_check()
print(f"Health status: {health_status}")
```

**Solutions:**
1. Check service configuration
2. Verify external dependencies (databases, APIs)
3. Review service initialization code
4. Check logs for detailed error information

### Debugging Tools

#### Dependency Report Generator
```python
def generate_dependency_report():
    """Generate comprehensive dependency report."""
    from app.core.dependencies import get_dependency_validator
    
    validator = get_dependency_validator()
    
    print("=== DEPENDENCY REPORT ===")
    print(validator.get_dependency_report())
    
    print("\n=== VALIDATION RESULTS ===")
    result = validator.validate_all(include_dev=True)
    
    if result.missing_required:
        print(f"❌ Missing required: {result.missing_required}")
    
    if result.missing_optional:
        print(f"⚠️  Missing optional: {result.missing_optional}")
    
    if result.version_conflicts:
        print(f"🔄 Version conflicts: {result.version_conflicts}")
    
    if result.installation_instructions:
        print(f"\n📦 Installation instructions:\n{result.installation_instructions}")

# Usage
generate_dependency_report()
```

#### Service Registry Inspector
```python
def inspect_service_registry():
    """Inspect current service registry state."""
    from app.core.registry import get_registry
    
    registry = get_registry()
    
    print("=== SERVICE REGISTRY INSPECTION ===")
    print(f"Total services: {len(registry.list_services())}")
    
    for service_name in sorted(registry.list_services()):
        service_info = registry.get_service_info(service_name)
        status = "✓" if service_info.health_status else "✗"
        
        print(f"{status} {service_name}")
        print(f"    Type: {service_info.service_type}")
        print(f"    State: {service_info.lifecycle}")
        print(f"    Dependencies: {service_info.dependencies}")
        
        if service_info.error_message:
            print(f"    Error: {service_info.error_message}")

# Usage
inspect_service_registry()
```

## Advanced Topics

### Custom Dependency Validators

```python
from app.core.dependencies import DependencyValidator, DependencyInfo, DependencyType

class CustomDependencyValidator(DependencyValidator):
    """Custom validator with additional rules."""
    
    def validate_custom_rules(self) -> List[str]:
        """Validate custom business rules."""
        errors = []
        
        # Rule: At least one LLM provider must be available
        llm_providers = ['openai', 'anthropic', 'boto3']
        available_providers = [
            provider for provider in llm_providers 
            if self.validate_dependency(provider)[0]
        ]
        
        if not available_providers:
            errors.append(
                "At least one LLM provider (openai, anthropic, boto3) must be available"
            )
        
        # Rule: If diagrams is available, graphviz must also be available
        if self.validate_dependency('diagrams')[0]:
            if not self.validate_dependency('graphviz')[0]:
                errors.append(
                    "graphviz is required when diagrams package is installed"
                )
        
        return errors
```

### Dynamic Service Registration

```python
def register_dynamic_services(config):
    """Register services based on runtime configuration."""
    registry = get_registry()
    
    # Register different implementations based on config
    cache_backend = config.get('cache.backend', 'memory')
    
    if cache_backend == 'redis' and check_dependency('redis'):
        from app.services.redis_cache import RedisCacheService
        registry.register_singleton('cache', RedisCacheService)
    elif cache_backend == 'memory':
        from app.services.memory_cache import MemoryCacheService
        registry.register_singleton('cache', MemoryCacheService)
    
    # Register LLM providers based on availability
    if check_dependency('openai'):
        from app.llm.openai_provider import OpenAIProvider
        registry.register_factory('openai_provider', OpenAIProvider)
    
    if check_dependency('anthropic'):
        from app.llm.anthropic_provider import AnthropicProvider
        registry.register_factory('anthropic_provider', AnthropicProvider)
```

### Dependency Injection Decorators

```python
from functools import wraps
from typing import Callable, Any

def inject_services(**service_mappings):
    """Decorator to inject services into function parameters."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Inject services based on mappings
            for param_name, service_name in service_mappings.items():
                if param_name not in kwargs:
                    service = optional_service(service_name)
                    if service:
                        kwargs[param_name] = service
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@inject_services(logger='logger', cache='cache')
def process_data(data, logger=None, cache=None):
    if logger:
        logger.info(f"Processing {len(data)} items")
    
    if cache:
        cached = cache.get(f"processed_{hash(data)}")
        if cached:
            return cached
    
    result = expensive_processing(data)
    
    if cache:
        cache.set(f"processed_{hash(data)}", result)
    
    return result
```

### Health Check Monitoring

```python
import asyncio
from typing import Dict, List

class DependencyHealthMonitor:
    """Monitor dependency health continuously."""
    
    def __init__(self, check_interval: int = 300):
        self.check_interval = check_interval
        self.health_history: Dict[str, List[bool]] = {}
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        while True:
            await self.check_all_dependencies()
            await asyncio.sleep(self.check_interval)
    
    async def check_all_dependencies(self):
        """Check health of all dependencies."""
        from app.core.registry import get_registry
        
        registry = get_registry()
        health_status = registry.health_check()
        
        for service_name, is_healthy in health_status.items():
            if service_name not in self.health_history:
                self.health_history[service_name] = []
            
            self.health_history[service_name].append(is_healthy)
            
            # Keep only last 100 checks
            if len(self.health_history[service_name]) > 100:
                self.health_history[service_name] = self.health_history[service_name][-100:]
            
            # Alert on consecutive failures
            recent_checks = self.health_history[service_name][-5:]
            if len(recent_checks) >= 5 and not any(recent_checks):
                await self.alert_service_failure(service_name)
    
    async def alert_service_failure(self, service_name: str):
        """Alert on service failure."""
        logger = require_service('logger')
        logger.error(f"Service {service_name} has failed health checks for 5 consecutive attempts")
        
        # Could send notifications, create tickets, etc.
```

This comprehensive dependency management guide provides all the information needed to effectively manage dependencies in the AAA system. It covers adding new dependencies, understanding the validation system, distinguishing between required and optional dependencies, and migrating existing code to the new patterns.