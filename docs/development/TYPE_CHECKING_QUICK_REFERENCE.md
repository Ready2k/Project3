# Type Checking Quick Reference

## Commands

```bash
# Type checking
make typecheck                    # Basic type check
make typecheck-verbose           # Detailed output
make test-types                  # Run type checking tests
make quality                     # Full quality check

# Pre-commit
pre-commit run mypy-type-check   # Run type check hook
pre-commit run --all-files       # Run all hooks
```

## Common Type Hints

```python
# Basic types
def func(name: str, count: int, active: bool) -> str:
    return f"{name}: {count}"

# Collections
from typing import List, Dict, Set, Tuple
items: List[str] = ["a", "b", "c"]
mapping: Dict[str, int] = {"key": 1}
coordinates: Tuple[float, float] = (1.0, 2.0)

# Optional and Union
from typing import Optional, Union
maybe_value: Optional[str] = None  # str | None
mixed: Union[str, int] = "hello"   # str | int

# Protocols (interfaces)
from typing import Protocol
class Drawable(Protocol):
    def draw(self) -> None: ...

# Generic types
from typing import TypeVar, Generic
T = TypeVar('T')
class Container(Generic[T]):
    def __init__(self, item: T) -> None:
        self.item = T
```

## Service Registry Types

```python
# Service registration
from app.utils.imports import require_service, optional_service
from app.core.service import LoggerProtocol

# Required service (raises if missing)
logger: LoggerProtocol = require_service('logger')

# Optional service (returns None if missing)  
cache: Optional[CacheProtocol] = optional_service('cache')
```

## Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserModel(BaseModel):
    name: str = Field(..., min_length=1)
    email: str
    tags: Optional[List[str]] = None
    created: datetime = Field(default_factory=datetime.now)
    
    class Config:
        validate_assignment = True
```

## Error Handling

```python
from typing import Union
from app.core.types import Result, ServiceError

def safe_func(data: str) -> Result[str, ServiceError]:
    try:
        return Result.ok(process(data))
    except Exception as e:
        return Result.error(ServiceError(str(e)))
```

## MyPy Configuration Snippets

```ini
# Ignore missing imports for library
[mypy-library_name.*]
ignore_missing_imports = True

# Relax rules for specific module
[mypy-app.legacy.module]
disallow_untyped_defs = False
warn_return_any = False

# Strict mode for module
[mypy-app.core.*]
disallow_untyped_defs = True
disallow_any_generics = True
```

## Common Fixes

```python
# Fix: Function missing return type
def process(data):  # ❌
def process(data: str) -> str:  # ✅

# Fix: Untyped variable
result = get_data()  # ❌
result: Dict[str, Any] = get_data()  # ✅

# Fix: Missing parameter types
def handle(request):  # ❌
def handle(request: Request) -> Response:  # ✅

# Fix: Any type usage
def get_config() -> Any:  # ❌
def get_config() -> Dict[str, Union[str, int]]:  # ✅
```

## IDE Setup

### VS Code
1. Install `ms-python.mypy-type-checker`
2. Enable in settings: `"python.linting.mypyEnabled": true`
3. Configure args: `"python.linting.mypyArgs": ["--config-file=mypy.ini"]`

### PyCharm
1. Settings → Editor → Inspections → Python → Type checker ✅
2. Settings → Project → Python Interpreter (verify correct env)
3. External Tools → Add MyPy tool

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Cannot find implementation or library stub` | Add `ignore_missing_imports = True` |
| `Function is missing a return type annotation` | Add `-> ReturnType` |
| `Call to untyped function` | Add type hints to called function |
| `Returning Any from function` | Use specific return type |
| `Need type annotation for variable` | Add `: Type` annotation |