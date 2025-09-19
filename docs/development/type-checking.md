# Type Checking with MyPy

This project uses MyPy for static type checking to improve code quality and catch potential bugs early in development.

## Configuration

Type checking is configured in `mypy.ini` with the following key settings:

- **Python Version**: 3.10+
- **Gradual Typing**: Starting with relaxed settings to allow incremental adoption
- **Third-party Libraries**: Configured to ignore missing imports for external libraries
- **Exclusions**: Test files and fixtures are excluded from strict checking

## Running Type Checks

### Command Line

```bash
# Run type checking
make typecheck

# Run as part of linting
make lint

# Run all code quality checks
make fmt && make lint
```

### IDE Integration

For the best development experience, configure your IDE to run MyPy:

#### VS Code
Install the Python extension and add to your settings:
```json
{
    "python.linting.mypyEnabled": true,
    "python.linting.mypyArgs": ["--config-file=mypy.ini"]
}
```

#### PyCharm
1. Go to Settings → Tools → External Tools
2. Add MyPy with arguments: `--config-file=mypy.ini`

## CI/CD Integration

Type checking runs automatically in our CI pipeline:

- **Pre-commit hooks**: Run on every commit
- **GitHub Actions**: Run on pull requests and pushes
- **Make commands**: Integrated into development workflow

## Current Status

The project is in **gradual typing mode** with 876 type errors remaining. This is expected as we migrate from untyped to typed code.

### Error Categories

1. **Missing logger attributes**: Services need proper logger initialization
2. **Any return types**: Functions returning `Any` instead of specific types
3. **Union type handling**: Proper handling of optional values
4. **Generic type parameters**: Adding proper type parameters to collections

## Fixing Type Errors

### Priority Order

1. **Critical Services**: Core services and registry components
2. **API Layer**: FastAPI endpoints and request/response models
3. **Business Logic**: Pattern matching and recommendation services
4. **UI Components**: Streamlit interface components

### Common Patterns

#### Logger Initialization
```python
# Before
class MyService:
    def method(self):
        self.logger.info("message")  # Error: no logger attribute

# After
class MyService:
    def __init__(self):
        self.logger = require_service('logger', context='MyService')
```

#### Return Type Annotations
```python
# Before
def get_data():
    return some_function()  # Returns Any

# After
def get_data() -> dict[str, Any]:
    return some_function()
```

#### Optional Handling
```python
# Before
def process(value: str | None):
    return value.upper()  # Error: None has no upper()

# After
def process(value: str | None) -> str | None:
    return value.upper() if value else None
```

## Incremental Migration Plan

### Phase 1: Core Infrastructure (Current)
- Service registry and dependency injection
- Configuration and logging services
- Basic type annotations

### Phase 2: API Layer
- FastAPI endpoints with proper types
- Request/response models
- Error handling

### Phase 3: Business Logic
- Pattern matching services
- Recommendation engine
- LLM providers

### Phase 4: Strict Mode
- Enable strict type checking
- Fix remaining errors
- Full type coverage

## Best Practices

1. **Add type hints incrementally**: Start with function signatures
2. **Use Union types**: For optional parameters and return values
3. **Leverage Pydantic**: For data validation and serialization
4. **Document complex types**: Use type aliases for readability
5. **Test type annotations**: Ensure types match runtime behavior

## Resources

- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pydantic Types](https://docs.pydantic.dev/latest/concepts/types/)
- [FastAPI Type Hints](https://fastapi.tiangolo.com/python-types/)