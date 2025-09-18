# Dependency and Import Management Design

## Overview

This design document outlines the approach for eliminating fallback imports and implementing a robust dependency management system for the AAA codebase. The solution focuses on explicit dependency declaration, service registry pattern, and comprehensive type safety.

## Architecture

### Current State Analysis

The current codebase has several dependency management issues:
- 15+ locations with try/except import patterns
- Silent failures when optional dependencies are missing
- Circular import dependencies
- No centralized dependency management
- Missing type hints throughout the codebase

### Target Architecture

```
app/
├── core/
│   ├── registry.py              # Service registry implementation
│   ├── dependencies.py          # Dependency validation and management
│   └── types.py                 # Common type definitions
├── config/
│   ├── services.yaml           # Service configuration
│   └── dependencies.yaml       # Dependency requirements
└── utils/
    ├── imports.py              # Import utilities
    └── validation.py           # Dependency validation
```

## Components and Interfaces

### 1. Service Registry Implementation

#### Core Registry (`app/core/registry.py`)
```python
from typing import Any, Dict, Type, TypeVar, Optional, Callable
from abc import ABC, abstractmethod
import inspect

T = TypeVar('T')

class ServiceRegistry:
    """Centralized service registry for dependency injection."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._dependencies: Dict[str, List[str]] = {}
    
    def register_singleton(self, name: str, service: Any) -> None:
        """Register a singleton service instance."""
        self._singletons[name] = service
        self._services[name] = service
    
    def register_factory(self, name: str, factory: Callable[[], T]) -> None:
        """Register a service factory for on-demand creation."""
        self._factories[name] = factory
    
    def register_class(self, name: str, cls: Type[T], dependencies: List[str] = None) -> None:
        """Register a class with automatic dependency injection."""
        self._dependencies[name] = dependencies or []
        
        def factory():
            # Resolve dependencies automatically
            kwargs = {}
            for dep_name in self._dependencies[name]:
                kwargs[dep_name] = self.get(dep_name)
            return cls(**kwargs)
        
        self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        """Get service instance, creating if necessary."""
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]
        
        # Check if already created
        if name in self._services:
            return self._services[name]
        
        # Create from factory
        if name in self._factories:
            service = self._factories[name]()
            self._services[name] = service
            return service
        
        raise ServiceNotFoundError(f"Service '{name}' not registered")
    
    def has(self, name: str) -> bool:
        """Check if service is registered."""
        return name in self._services or name in self._factories or name in self._singletons
    
    def validate_dependencies(self) -> List[str]:
        """Validate all registered dependencies can be resolved."""
        errors = []
        for service_name, deps in self._dependencies.items():
            for dep_name in deps:
                if not self.has(dep_name):
                    errors.append(f"Service '{service_name}' depends on unregistered '{dep_name}'")
        return errors

class ServiceNotFoundError(Exception):
    """Raised when a requested service is not found in the registry."""
    pass

# Global registry instance
_registry = ServiceRegistry()

def get_registry() -> ServiceRegistry:
    """Get the global service registry."""
    return _registry
```

#### Service Interface (`app/core/service.py`)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class Service(ABC):
    """Base interface for all services."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the service gracefully."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if service is healthy."""
        pass
    
    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """List of service dependencies."""
        pass

class ConfigurableService(Service):
    """Base class for services that require configuration."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialized = False
    
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized
```

### 2. Dependency Validation System

#### Dependency Validator (`app/core/dependencies.py`)
```python
from typing import List, Dict, Any, Optional, Tuple
import importlib
import sys
from dataclasses import dataclass
from enum import Enum

class DependencyType(Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    DEVELOPMENT = "development"

@dataclass
class DependencyInfo:
    """Information about a dependency."""
    name: str
    version_constraint: Optional[str]
    dependency_type: DependencyType
    purpose: str
    alternatives: List[str]
    import_name: Optional[str] = None
    
    def __post_init__(self):
        if self.import_name is None:
            self.import_name = self.name

@dataclass
class ValidationResult:
    """Result of dependency validation."""
    is_valid: bool
    missing_required: List[str]
    missing_optional: List[str]
    version_conflicts: List[str]
    warnings: List[str]

class DependencyValidator:
    """Validates system dependencies at startup."""
    
    def __init__(self):
        self.dependencies: Dict[str, DependencyInfo] = {}
        self._load_dependency_definitions()
    
    def _load_dependency_definitions(self) -> None:
        """Load dependency definitions from configuration."""
        # This would load from a YAML file or configuration
        self.dependencies = {
            "streamlit": DependencyInfo(
                name="streamlit",
                version_constraint=">=1.28.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Web UI framework",
                alternatives=["dash", "gradio"]
            ),
            "openai": DependencyInfo(
                name="openai",
                version_constraint=">=1.3.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="OpenAI API integration",
                alternatives=["anthropic", "local_llm"]
            ),
            "diagrams": DependencyInfo(
                name="diagrams",
                version_constraint=">=0.23.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="Infrastructure diagram generation",
                alternatives=["manual_diagrams", "mermaid_only"]
            )
        }
    
    def validate_all(self) -> ValidationResult:
        """Validate all dependencies."""
        missing_required = []
        missing_optional = []
        version_conflicts = []
        warnings = []
        
        for name, dep_info in self.dependencies.items():
            try:
                module = importlib.import_module(dep_info.import_name)
                
                # Check version if constraint exists
                if dep_info.version_constraint and hasattr(module, '__version__'):
                    if not self._check_version_constraint(module.__version__, dep_info.version_constraint):
                        version_conflicts.append(
                            f"{name}: {module.__version__} does not satisfy {dep_info.version_constraint}"
                        )
                
            except ImportError:
                if dep_info.dependency_type == DependencyType.REQUIRED:
                    missing_required.append(name)
                else:
                    missing_optional.append(name)
                    warnings.append(
                        f"Optional dependency '{name}' not available. "
                        f"Feature disabled: {dep_info.purpose}"
                    )
        
        is_valid = len(missing_required) == 0 and len(version_conflicts) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            missing_required=missing_required,
            missing_optional=missing_optional,
            version_conflicts=version_conflicts,
            warnings=warnings
        )
    
    def _check_version_constraint(self, version: str, constraint: str) -> bool:
        """Check if version satisfies constraint."""
        # Simplified version checking - in production, use packaging.specifiers
        if constraint.startswith(">="):
            required_version = constraint[2:]
            return version >= required_version
        elif constraint.startswith("=="):
            required_version = constraint[2:]
            return version == required_version
        return True
    
    def get_installation_instructions(self, missing_deps: List[str]) -> str:
        """Generate installation instructions for missing dependencies."""
        instructions = ["Missing dependencies detected. Install with:"]
        
        pip_packages = []
        for dep_name in missing_deps:
            if dep_name in self.dependencies:
                dep_info = self.dependencies[dep_name]
                if dep_info.version_constraint:
                    pip_packages.append(f"{dep_name}{dep_info.version_constraint}")
                else:
                    pip_packages.append(dep_name)
        
        if pip_packages:
            instructions.append(f"pip install {' '.join(pip_packages)}")
        
        return "\n".join(instructions)
```

### 3. Import Management System

#### Safe Import Utilities (`app/utils/imports.py`)
```python
from typing import Any, Optional, Type, TypeVar, Callable
import importlib
from app.core.registry import get_registry

T = TypeVar('T')

class ImportManager:
    """Manages safe imports and service resolution."""
    
    def __init__(self):
        self.registry = get_registry()
    
    def safe_import(self, module_name: str, class_name: Optional[str] = None) -> Optional[Any]:
        """Safely import a module or class."""
        try:
            module = importlib.import_module(module_name)
            if class_name:
                return getattr(module, class_name)
            return module
        except ImportError as e:
            # Log the import error but don't fail
            from app.utils.logger import app_logger
            app_logger.warning(f"Failed to import {module_name}: {e}")
            return None
    
    def require_service(self, service_name: str) -> Any:
        """Require a service from the registry."""
        if not self.registry.has(service_name):
            raise ServiceRequiredError(f"Required service '{service_name}' not available")
        return self.registry.get(service_name)
    
    def optional_service(self, service_name: str, default: Any = None) -> Any:
        """Get an optional service with fallback."""
        if self.registry.has(service_name):
            return self.registry.get(service_name)
        return default

class ServiceRequiredError(Exception):
    """Raised when a required service is not available."""
    pass

# Global import manager
_import_manager = ImportManager()

def get_import_manager() -> ImportManager:
    """Get the global import manager."""
    return _import_manager

# Convenience functions
def require_service(service_name: str) -> Any:
    """Require a service from the registry."""
    return _import_manager.require_service(service_name)

def optional_service(service_name: str, default: Any = None) -> Any:
    """Get an optional service with fallback."""
    return _import_manager.optional_service(service_name, default)
```

### 4. Type System Enhancement

#### Common Types (`app/core/types.py`)
```python
from typing import TypeVar, Generic, Union, Dict, Any, List, Optional, Callable, Protocol
from dataclasses import dataclass
from enum import Enum

# Result type for error handling
T = TypeVar('T')
E = TypeVar('E')

@dataclass
class Success(Generic[T]):
    """Successful result containing a value."""
    value: T
    
    def is_success(self) -> bool:
        return True
    
    def is_error(self) -> bool:
        return False

@dataclass
class Error(Generic[E]):
    """Error result containing error information."""
    error: E
    
    def is_success(self) -> bool:
        return False
    
    def is_error(self) -> bool:
        return True

Result = Union[Success[T], Error[E]]

# Service protocols
class LoggerProtocol(Protocol):
    """Protocol for logger services."""
    def info(self, message: str, **kwargs) -> None: ...
    def warning(self, message: str, **kwargs) -> None: ...
    def error(self, message: str, **kwargs) -> None: ...
    def debug(self, message: str, **kwargs) -> None: ...

class ConfigProtocol(Protocol):
    """Protocol for configuration services."""
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
    def has(self, key: str) -> bool: ...

class CacheProtocol(Protocol):
    """Protocol for cache services."""
    def get(self, key: str) -> Optional[Any]: ...
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None: ...
    def delete(self, key: str) -> bool: ...
    def clear(self) -> None: ...

# Configuration types
@dataclass
class ServiceConfig:
    """Configuration for a service."""
    name: str
    class_path: str
    dependencies: List[str]
    config: Dict[str, Any]
    singleton: bool = True

# Error types
class DependencyError(Exception):
    """Base class for dependency-related errors."""
    pass

class ServiceNotAvailableError(DependencyError):
    """Raised when a required service is not available."""
    pass

class CircularDependencyError(DependencyError):
    """Raised when circular dependencies are detected."""
    pass
```

## Migration Strategy

### Phase 1: Foundation Setup (Week 1)

#### Day 1-2: Core Infrastructure
```python
# 1. Create service registry
# 2. Implement dependency validator
# 3. Set up import manager
# 4. Define common types and protocols
```

#### Day 3-4: Service Registration
```python
# 1. Register core services (logger, config, cache)
# 2. Create service configuration files
# 3. Implement service lifecycle management
# 4. Add dependency validation at startup
```

#### Day 5: Testing Infrastructure
```python
# 1. Create test fixtures for service registry
# 2. Implement mock service patterns
# 3. Add dependency injection testing utilities
# 4. Create integration tests for service resolution
```

### Phase 2: Migration (Week 2)

#### Replace Fallback Imports
```python
# Before (problematic):
try:
    from app.utils.logger import app_logger
except ImportError:
    import logging
    app_logger = logging.getLogger(__name__)

# After (service registry):
from app.utils.imports import require_service
app_logger = require_service('logger')
```

#### Update Component Initialization
```python
# Before (direct imports):
class AnalysisService:
    def __init__(self):
        from app.services.cache import CacheService
        self.cache = CacheService()

# After (dependency injection):
class AnalysisService:
    def __init__(self, cache: CacheProtocol, logger: LoggerProtocol):
        self.cache = cache
        self.logger = logger

# Registration:
registry.register_class(
    'analysis_service',
    AnalysisService,
    dependencies=['cache', 'logger']
)
```

### Phase 3: Type Safety (Week 2-3)

#### Add Type Hints
```python
# Before:
def process_data(data):
    return {"result": data}

# After:
def process_data(data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
    if not data:
        return Error("Data is required")
    return Success({"result": data})
```

#### Implement Protocols
```python
# Define service interfaces
class LLMProviderProtocol(Protocol):
    async def generate(self, prompt: str, **kwargs) -> str: ...
    def get_model_info(self) -> Dict[str, Any]: ...

# Use in type hints
class AnalysisService:
    def __init__(self, llm_provider: LLMProviderProtocol):
        self.llm_provider = llm_provider
```

## Configuration

### Service Configuration (`config/services.yaml`)
```yaml
services:
  logger:
    class_path: "app.utils.logger.AppLogger"
    singleton: true
    config:
      level: "INFO"
      format: "structured"
  
  cache:
    class_path: "app.services.cache.CacheService"
    singleton: true
    dependencies: ["config"]
    config:
      backend: "redis"
      ttl: 300
  
  llm_provider:
    class_path: "app.llm.factory.LLMProviderFactory"
    singleton: false
    dependencies: ["config", "logger"]
    config:
      default_provider: "openai"
```

### Dependency Configuration (`config/dependencies.yaml`)
```yaml
dependencies:
  required:
    - name: "streamlit"
      version: ">=1.28.0"
      purpose: "Web UI framework"
    - name: "fastapi"
      version: ">=0.104.0"
      purpose: "API framework"
  
  optional:
    - name: "openai"
      version: ">=1.3.0"
      purpose: "OpenAI API integration"
      alternatives: ["anthropic", "local_llm"]
    - name: "diagrams"
      version: ">=0.23.0"
      purpose: "Infrastructure diagram generation"
      alternatives: ["mermaid_only"]
```

## Testing Strategy

### Service Registry Testing
```python
# test_service_registry.py
import pytest
from app.core.registry import ServiceRegistry, ServiceNotFoundError

class TestServiceRegistry:
    def test_register_and_get_singleton(self):
        registry = ServiceRegistry()
        service = MockService()
        registry.register_singleton('test_service', service)
        
        retrieved = registry.get('test_service')
        assert retrieved is service
    
    def test_dependency_injection(self):
        registry = ServiceRegistry()
        registry.register_singleton('logger', MockLogger())
        registry.register_class('service', ServiceWithDeps, ['logger'])
        
        service = registry.get('service')
        assert isinstance(service, ServiceWithDeps)
        assert service.logger is not None
```

### Dependency Validation Testing
```python
# test_dependency_validator.py
import pytest
from app.core.dependencies import DependencyValidator

class TestDependencyValidator:
    def test_validate_missing_required(self):
        validator = DependencyValidator()
        # Mock missing required dependency
        result = validator.validate_all()
        
        assert not result.is_valid
        assert len(result.missing_required) > 0
```

## Performance Considerations

### Lazy Loading
```python
class LazyServiceRegistry(ServiceRegistry):
    """Service registry with lazy loading support."""
    
    def get(self, name: str) -> Any:
        # Only create services when first requested
        if name not in self._services and name in self._factories:
            self._services[name] = self._factories[name]()
        return super().get(name)
```

### Caching
```python
class CachedImportManager(ImportManager):
    """Import manager with module caching."""
    
    def __init__(self):
        super().__init__()
        self._module_cache = {}
    
    def safe_import(self, module_name: str, class_name: Optional[str] = None) -> Optional[Any]:
        cache_key = f"{module_name}.{class_name}" if class_name else module_name
        
        if cache_key in self._module_cache:
            return self._module_cache[cache_key]
        
        result = super().safe_import(module_name, class_name)
        self._module_cache[cache_key] = result
        return result
```

## Success Metrics

### Code Quality Metrics
- **Import Errors**: Zero try/except import patterns
- **Type Coverage**: 100% type hint coverage
- **Dependency Resolution**: All services resolvable at startup
- **Circular Dependencies**: Zero circular dependencies detected

### Performance Metrics
- **Startup Time**: <2 seconds for service registration
- **Memory Usage**: <10MB overhead for service registry
- **Resolution Time**: <1ms average service resolution time

### Developer Experience Metrics
- **IDE Support**: Full autocompletion and error detection
- **Test Setup**: <5 lines to mock any service
- **Debugging**: Clear error messages for dependency issues
- **Documentation**: Auto-generated dependency graphs