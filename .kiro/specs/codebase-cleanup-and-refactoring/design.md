# Design Document

## Overview

This design document outlines the architectural approach for cleaning up and refactoring the AAA codebase. The solution focuses on modular decomposition, consistent patterns, and maintainable architecture while preserving all existing functionality.

## Architecture

### Current State Analysis

The current codebase has several architectural challenges:
- Monolithic `streamlit_app.py` (7600+ lines)
- Multiple entry points causing confusion
- Inconsistent import patterns and error handling
- Test files scattered across directories
- Configuration spread across multiple files
- Mixed logging approaches

### Target Architecture

```
aaa-system/
├── app/
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_app.py              # Primary Streamlit entry point
│   │   ├── tabs/                    # Individual tab components
│   │   │   ├── __init__.py
│   │   │   ├── analysis_tab.py
│   │   │   ├── qa_tab.py
│   │   │   ├── results_tab.py
│   │   │   ├── agent_solution_tab.py
│   │   │   └── about_tab.py
│   │   ├── components/              # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   ├── provider_config.py
│   │   │   ├── session_management.py
│   │   │   ├── results_display.py
│   │   │   ├── diagram_viewer.py
│   │   │   └── export_controls.py
│   │   └── utils/                   # UI utility functions
│   │       ├── __init__.py
│   │       ├── mermaid_helpers.py
│   │       └── form_helpers.py
│   ├── services/
│   │   ├── core/                    # Core business services
│   │   ├── integrations/            # External integrations
│   │   └── ai/                      # AI/LLM related services
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py              # Unified configuration
│   │   ├── base.yaml               # Base configuration
│   │   ├── development.yaml        # Dev overrides
│   │   ├── production.yaml         # Prod overrides
│   │   └── local.yaml.example      # Local overrides template
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
├── legacy/                          # Archived legacy files
│   └── streamlit_app_legacy.py
└── docs/                           # Current documentation only
    ├── README.md
    ├── CHANGELOG.md
    ├── DEPLOYMENT.md
    └── SECURITY_REVIEW.md
```

## Components and Interfaces

### 1. UI Layer Decomposition

#### Main Application (`app/ui/main_app.py`)
```python
class AAAStreamlitApp:
    """Main Streamlit application orchestrator."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.session_manager = SessionManager()
        self.tab_registry = TabRegistry()
    
    def run(self) -> None:
        """Run the main application."""
        self._setup_page_config()
        self._render_sidebar()
        self._render_main_content()
    
    def _render_main_content(self) -> None:
        """Render tabbed interface using registered tabs."""
        tabs = self.tab_registry.get_tabs()
        tab_objects = st.tabs([tab.title for tab in tabs])
        
        for tab_obj, tab_handler in zip(tab_objects, tabs):
            with tab_obj:
                tab_handler.render()
```

#### Tab Interface (`app/ui/tabs/base.py`)
```python
from abc import ABC, abstractmethod

class BaseTab(ABC):
    """Base interface for all tab components."""
    
    @property
    @abstractmethod
    def title(self) -> str:
        """Tab title for display."""
        pass
    
    @abstractmethod
    def render(self) -> None:
        """Render the tab content."""
        pass
    
    @abstractmethod
    def can_render(self) -> bool:
        """Check if tab can be rendered (e.g., session requirements)."""
        pass
```

#### Component Interface (`app/ui/components/base.py`)
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseComponent(ABC):
    """Base interface for reusable UI components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    def render(self, **kwargs) -> Any:
        """Render the component."""
        pass
    
    def validate_props(self, **kwargs) -> bool:
        """Validate component properties."""
        return True
```

### 2. Configuration Management

#### Unified Configuration Service (`app/config/settings.py`)
```python
from typing import Any, Dict, Optional
from pathlib import Path
import yaml
from pydantic import BaseSettings

class ConfigurationManager:
    """Centralized configuration management."""
    
    def __init__(self, env: str = "development"):
        self.env = env
        self._config_cache: Optional[Dict[str, Any]] = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load hierarchical configuration."""
        if self._config_cache is None:
            base_config = self._load_yaml("base.yaml")
            env_config = self._load_yaml(f"{self.env}.yaml")
            local_config = self._load_yaml("local.yaml", required=False)
            
            self._config_cache = self._merge_configs(
                base_config, env_config, local_config
            )
        
        return self._config_cache
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support."""
        config = self.load_config()
        return self._get_nested_value(config, key, default)
```

### 3. Error Handling Standardization

#### Result Type Pattern (`app/utils/result.py`)
```python
from typing import Generic, TypeVar, Union, Callable
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E')

@dataclass
class Success(Generic[T]):
    value: T
    
    def is_success(self) -> bool:
        return True
    
    def is_error(self) -> bool:
        return False

@dataclass
class Error(Generic[E]):
    error: E
    
    def is_success(self) -> bool:
        return False
    
    def is_error(self) -> bool:
        return True

Result = Union[Success[T], Error[E]]

class ResultBuilder:
    """Builder for creating Result types."""
    
    @staticmethod
    def success(value: T) -> Success[T]:
        return Success(value)
    
    @staticmethod
    def error(error: E) -> Error[E]:
        return Error(error)
    
    @staticmethod
    def from_exception(func: Callable[[], T]) -> Result[T, Exception]:
        """Execute function and wrap result/exception."""
        try:
            return Success(func())
        except Exception as e:
            return Error(e)
```

### 4. Import Management

#### Dependency Registry (`app/core/registry.py`)
```python
from typing import Any, Dict, Type, TypeVar, Optional
from abc import ABC, abstractmethod

T = TypeVar('T')

class ServiceRegistry:
    """Centralized service registry for dependency injection."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
    
    def register(self, name: str, service: Any) -> None:
        """Register a service instance."""
        self._services[name] = service
    
    def register_factory(self, name: str, factory: callable) -> None:
        """Register a service factory."""
        self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        """Get service instance, creating if necessary."""
        if name in self._services:
            return self._services[name]
        
        if name in self._factories:
            service = self._factories[name]()
            self._services[name] = service
            return service
        
        raise ValueError(f"Service '{name}' not registered")
```

## Data Models

### Configuration Schema
```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class UIConfig(BaseModel):
    """UI-specific configuration."""
    page_title: str = "Automated AI Assessment (AAA)"
    page_icon: str = "🤖"
    layout: str = "wide"
    sidebar_state: str = "expanded"

class SecurityConfig(BaseModel):
    """Security configuration."""
    enable_advanced_defense: bool = True
    max_request_size: int = 10 * 1024 * 1024
    rate_limit_enabled: bool = True

class PerformanceConfig(BaseModel):
    """Performance configuration."""
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    lazy_loading: bool = True
    startup_timeout: int = 30

class AppConfig(BaseModel):
    """Main application configuration."""
    ui: UIConfig = Field(default_factory=UIConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    debug_mode: bool = False
    environment: str = "development"
```

### File Organization Schema
```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class FileType(Enum):
    PRODUCTION = "production"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    LEGACY = "legacy"
    UTILITY = "utility"

@dataclass
class FileAction:
    """Represents an action to take on a file."""
    source_path: str
    action: str  # "move", "remove", "rename", "archive"
    target_path: Optional[str] = None
    reason: str = ""

@dataclass
class OrganizationPlan:
    """Plan for organizing files."""
    actions: List[FileAction]
    validation_rules: List[str]
    rollback_plan: List[FileAction]
```

## Error Handling

### Standardized Error Types
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AppError:
    """Standardized application error."""
    code: str
    message: str
    severity: ErrorSeverity
    context: Optional[Dict[str, Any]] = None
    cause: Optional[Exception] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None
        }

class ErrorHandler:
    """Centralized error handling."""
    
    def __init__(self, logger):
        self.logger = logger
    
    def handle_error(self, error: AppError) -> None:
        """Handle error based on severity."""
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.error(f"[{error.code}] {error.message}", extra=error.to_dict())
        else:
            self.logger.warning(f"[{error.code}] {error.message}", extra=error.to_dict())
```

## Testing Strategy

### Test Organization
```python
# app/tests/conftest.py
import pytest
from app.config.settings import ConfigurationManager
from app.core.registry import ServiceRegistry

@pytest.fixture
def test_config():
    """Test configuration fixture."""
    config_manager = ConfigurationManager(env="testing")
    return config_manager.load_config()

@pytest.fixture
def service_registry():
    """Service registry fixture."""
    registry = ServiceRegistry()
    # Register test services
    return registry

# app/tests/unit/ui/test_main_app.py
import pytest
from unittest.mock import Mock, patch
from app.ui.main_app import AAAStreamlitApp

class TestAAAStreamlitApp:
    """Test suite for main Streamlit application."""
    
    def test_initialization(self, test_config):
        """Test app initialization."""
        app = AAAStreamlitApp()
        assert app.config_manager is not None
        assert app.session_manager is not None
        assert app.tab_registry is not None
    
    @patch('streamlit.set_page_config')
    def test_page_setup(self, mock_set_page_config, test_config):
        """Test page configuration setup."""
        app = AAAStreamlitApp()
        app._setup_page_config()
        mock_set_page_config.assert_called_once()
```

### Integration Testing
```python
# app/tests/integration/test_ui_workflow.py
import pytest
from app.ui.main_app import AAAStreamlitApp
from app.tests.fixtures.test_fixtures import create_test_session

class TestUIWorkflow:
    """Integration tests for UI workflows."""
    
    def test_complete_analysis_workflow(self, test_config):
        """Test complete analysis workflow."""
        app = AAAStreamlitApp()
        session = create_test_session()
        
        # Test workflow steps
        result = app.process_analysis_request(session)
        assert result.is_success()
        assert result.value.session_id is not None
```

## Performance Optimization

### Lazy Loading Strategy
```python
# app/ui/lazy_loader.py
from typing import Any, Callable, Dict, Optional
import importlib

class LazyLoader:
    """Lazy loading for heavy components."""
    
    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}
        self._module_factories: Dict[str, Callable] = {}
    
    def register_module(self, name: str, module_path: str, factory: Optional[Callable] = None):
        """Register a module for lazy loading."""
        self._module_factories[name] = factory or (lambda: importlib.import_module(module_path))
    
    def get_module(self, name: str) -> Any:
        """Get module, loading if necessary."""
        if name not in self._loaded_modules:
            if name not in self._module_factories:
                raise ValueError(f"Module '{name}' not registered")
            
            self._loaded_modules[name] = self._module_factories[name]()
        
        return self._loaded_modules[name]

# Usage in main app
lazy_loader = LazyLoader()
lazy_loader.register_module("enhanced_patterns", "app.ui.enhanced_pattern_management")
lazy_loader.register_module("diagram_generator", "app.diagrams.infrastructure")
```

### Caching Strategy
```python
# app/utils/cache_manager.py
from typing import Any, Optional, Callable
import functools
import time

class CacheManager:
    """Centralized cache management."""
    
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def cached(self, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
        """Decorator for caching function results."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = key_func(*args, **kwargs) if key_func else f"{func.__name__}:{hash((args, tuple(kwargs.items())))}"
                
                if self._is_cached_and_valid(cache_key, ttl or self.default_ttl):
                    return self._cache[cache_key]["value"]
                
                result = func(*args, **kwargs)
                self._cache[cache_key] = {
                    "value": result,
                    "timestamp": time.time()
                }
                return result
            return wrapper
        return decorator
```

## Migration Strategy

### Phase 1: Foundation (Week 1)
1. Create new directory structure
2. Implement configuration management
3. Set up service registry
4. Create base interfaces and error handling

### Phase 2: UI Decomposition (Week 2)
1. Break down monolithic Streamlit app
2. Create tab components
3. Implement reusable UI components
4. Migrate functionality incrementally

### Phase 3: Cleanup and Optimization (Week 3)
1. Remove unused files
2. Organize test files
3. Implement performance optimizations
4. Complete documentation updates

## Rollback Plan

Each phase will include:
1. **Backup Strategy**: Git branches for each major change
2. **Feature Flags**: Ability to switch between old and new implementations
3. **Validation Tests**: Comprehensive testing before each deployment
4. **Monitoring**: Performance and error monitoring during migration
5. **Quick Rollback**: Ability to revert to previous version within 5 minutes

## Success Metrics

1. **Code Quality**: Reduction in file sizes, improved maintainability scores
2. **Performance**: 30% improvement in startup time
3. **Developer Experience**: Reduced time to find and modify code
4. **Test Coverage**: Maintained or improved test coverage
5. **Error Reduction**: Fewer import errors and runtime exceptions