# Type Checking Guide

This guide covers type checking practices, configuration, and workflows for the Automated AI Assessment (AAA) project.

## Overview

The project uses **MyPy** for static type checking with strict configuration to ensure type safety across the codebase. Type checking is integrated into the development workflow through pre-commit hooks, IDE integration, and the test suite.

## Quick Start

### Running Type Checks

```bash
# Basic type checking
make typecheck

# Verbose type checking with detailed output
make typecheck-verbose

# Run type checking tests
make test-types

# Full quality check (formatting, linting, type checking)
make quality
```

### Pre-commit Integration

Type checking runs automatically on every commit via pre-commit hooks:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Run only type checking
pre-commit run mypy-type-check
```

## Configuration

### MyPy Configuration (`mypy.ini`)

The project uses a comprehensive MyPy configuration with the following key settings:

- **Python Version**: 3.10+
- **Strict Mode**: Gradually enabled (currently in migration)
- **Files Checked**: `app/` directory
- **Cache**: SQLite cache enabled for performance
- **Plugins**: Pydantic plugin for model validation

### Key Configuration Sections

```ini
[mypy]
# Basic settings
python_version = 3.10
files = app/
cache_dir = .mypy_cache

# Gradual typing (being tightened over time)
disallow_untyped_defs = False  # Will be True in future
check_untyped_defs = True
warn_return_any = True

# Third-party library stubs
[mypy-streamlit.*]
ignore_missing_imports = True
```

## IDE Integration

### Visual Studio Code

The project includes VS Code configuration for optimal type checking:

- **MyPy Extension**: Real-time type checking
- **Python Analysis**: Strict mode enabled
- **Auto-formatting**: Black formatter on save
- **Import Organization**: Automatic import sorting

**Required Extensions:**
- `ms-python.mypy-type-checker`
- `ms-python.python`
- `ms-python.black-formatter`
- `charliermarsh.ruff`

### PyCharm/IntelliJ

Configuration includes:
- Type checker inspection enabled
- Unresolved references warnings
- PEP 8 compliance (with project-specific exceptions)

## Writing Type-Safe Code

### Basic Type Hints

```python
from typing import List, Dict, Optional, Union, Any
from pathlib import Path

# Function annotations
def process_data(items: List[str], config: Dict[str, Any]) -> Optional[str]:
    """Process data with proper type hints."""
    if not items:
        return None
    return items[0]

# Class annotations
class DataProcessor:
    def __init__(self, name: str, max_items: int = 100) -> None:
        self.name: str = name
        self.max_items: int = max_items
        self._cache: Dict[str, Any] = {}
```

### Service Registry Types

```python
from typing import Protocol, TypeVar, Generic
from app.core.service import Service

# Protocol for type-safe service interfaces
class LoggerProtocol(Protocol):
    def info(self, message: str) -> None: ...
    def error(self, message: str, exc_info: bool = False) -> None: ...

# Generic service factory
T = TypeVar('T', bound=Service)

class ServiceFactory(Generic[T]):
    def create(self) -> T:
        ...
```

### Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserRequest(BaseModel):
    """Type-safe request model."""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    preferences: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        # Enable Pydantic MyPy plugin features
        validate_assignment = True
        use_enum_values = True
```

### Error Handling with Types

```python
from typing import Union, Result
from app.core.types import Result, ServiceError

def safe_operation(data: str) -> Result[str, ServiceError]:
    """Type-safe error handling."""
    try:
        processed = process_data(data)
        return Result.ok(processed)
    except ValueError as e:
        return Result.error(ServiceError(f"Processing failed: {e}"))
```

## Common Patterns

### Service Registration

```python
from typing import TypeVar, Type, Callable
from app.core.registry import ServiceRegistry

T = TypeVar('T')

# Type-safe service registration
def register_service(
    registry: ServiceRegistry,
    service_type: Type[T],
    factory: Callable[[], T]
) -> None:
    registry.register_factory(service_type.__name__.lower(), factory)
```

### Optional Dependencies

```python
from typing import Optional
from app.utils.imports import optional_service

# Type-safe optional service access
cache_service: Optional[CacheService] = optional_service('cache')
if cache_service is not None:
    cache_service.set('key', 'value')
```

### Async Code

```python
from typing import AsyncGenerator, Awaitable
import asyncio

async def process_items(items: List[str]) -> AsyncGenerator[str, None]:
    """Async generator with proper typing."""
    for item in items:
        result = await process_item_async(item)
        yield result

async def process_item_async(item: str) -> str:
    """Async function with type hints."""
    await asyncio.sleep(0.1)  # Simulate async work
    return f"processed_{item}"
```

## Testing Type Safety

### Type Checking Tests

The project includes automated type checking tests:

```python
# Run type checking as part of test suite
pytest app/tests/test_type_checking.py -v

# Test specific modules
pytest app/tests/test_type_checking.py::test_core_modules_type_safety -v
```

### Mock Objects with Types

```python
from typing import Protocol
from unittest.mock import Mock, MagicMock

class MockLogger:
    """Type-safe mock logger."""
    def info(self, message: str) -> None:
        pass
    
    def error(self, message: str, exc_info: bool = False) -> None:
        pass

# Use in tests
def test_with_typed_mock():
    logger: LoggerProtocol = MockLogger()
    service = MyService(logger)
    # Test implementation
```

## Troubleshooting

### Common Type Errors

**1. Missing Type Stubs**
```bash
# Error: Cannot find implementation or library stub
# Solution: Add to mypy.ini
[mypy-problematic_library.*]
ignore_missing_imports = True
```

**2. Untyped Function Calls**
```python
# Error: Call to untyped function
# Solution: Add type hints
def my_function(param: str) -> str:  # Add return type
    return param.upper()
```

**3. Any Type Usage**
```python
# Warning: Returning Any from function
# Solution: Use specific types
def get_config() -> Dict[str, Union[str, int]]:  # Instead of Any
    return {"key": "value", "count": 42}
```

### Performance Issues

**Slow Type Checking:**
- Use `--cache-dir` for persistent caching
- Exclude test files and fixtures from checking
- Use incremental mode (enabled by default)

**Memory Usage:**
- Limit checked files with `files` configuration
- Use `--no-error-summary` for large codebases

### IDE Issues

**VS Code Not Showing Type Errors:**
1. Check Python interpreter path
2. Verify MyPy extension is installed and enabled
3. Reload window (`Cmd/Ctrl + Shift + P` → "Reload Window")

**PyCharm Type Checking Disabled:**
1. Go to Settings → Editor → Inspections
2. Enable "Type checker" under Python
3. Ensure project interpreter is correct

## Migration Strategy

The project is gradually migrating to stricter type checking:

### Phase 1: Basic Type Hints (✅ Complete)
- Add type hints to function signatures
- Configure MyPy with relaxed settings
- Set up IDE integration

### Phase 2: Strict Core Modules (🔄 In Progress)
- Enable strict checking for `app/core/`
- Add comprehensive type hints to service layer
- Fix all type errors in critical paths

### Phase 3: Full Strict Mode (📋 Planned)
- Enable `disallow_untyped_defs = True`
- Remove `ignore_missing_imports` where possible
- Achieve 100% type hint coverage

### Migration Commands

```bash
# Check current type coverage
mypy --config-file mypy.ini --html-report mypy-report

# Test specific module migration
mypy app/core/registry.py --strict

# Generate type stub for external library
stubgen -p external_library -o stubs/
```

## Best Practices

### 1. Start with Function Signatures
Always add type hints to function parameters and return values first.

### 2. Use Protocols for Interfaces
Define protocols instead of abstract base classes for better flexibility.

### 3. Leverage Pydantic for Data Validation
Use Pydantic models for all data structures that cross boundaries.

### 4. Gradual Adoption
Enable stricter checking module by module, not all at once.

### 5. Document Type Decisions
Add comments explaining complex type annotations.

### 6. Test Type Safety
Include type checking in your test suite and CI/CD pipeline.

## Resources

- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
- [Pydantic MyPy Plugin](https://pydantic-docs.helpmanual.io/mypy_plugin/)
- [VS Code Python Type Checking](https://code.visualstudio.com/docs/python/linting#_mypy)

## Support

For type checking issues:
1. Check this documentation
2. Review MyPy error messages carefully
3. Consult the project's type checking tests
4. Ask in team chat with specific error messages