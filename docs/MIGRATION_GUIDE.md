# AAA System Migration Guide

This guide documents the major architectural changes made during the codebase cleanup and refactoring project.

## Overview

The AAA system has undergone a comprehensive refactoring to improve maintainability, performance, and code organization. This guide helps developers understand the changes and migrate their workflows.

## Architecture Changes

### Modular UI Structure

The monolithic Streamlit application has been decomposed into focused, reusable components:

#### Old Structure
- Single `streamlit_app.py` file (3000+ lines)
- All functionality mixed together
- Difficult to maintain and test

#### New Structure
- `app/ui/main_app.py` - Main application orchestrator
- `app/ui/tabs/` - Individual tab components
- `app/ui/components/` - Reusable UI components
- `app/ui/utils/` - UI utility functions

### Service Layer Architecture

#### New Components
- `app/core/registry.py` - Service registry for dependency injection
- `app/utils/result.py` - Result type pattern for error handling
- `app/utils/error_handler.py` - Centralized error handling
- `app/ui/lazy_loader.py` - Lazy loading for performance

## Configuration Changes

The configuration system has been completely restructured to use a hierarchical approach with consolidated settings from legacy files.

### Old Structure
- Single `config.yaml` file with all settings
- Separate `system_config.yaml` with system parameters
- Environment variables for overrides
- No environment-specific configurations

### New Structure
- `config/base.yaml` - Default configuration for all environments (consolidated from legacy files)
- `config/development.yaml` - Development-specific overrides
- `config/production.yaml` - Production-specific overrides
- `config/testing.yaml` - Testing-specific overrides
- `config/staging.yaml` - Staging-specific overrides
- `config/local.yaml` - Local development overrides (git-ignored)
- Environment variables with `AAA_` prefix for runtime overrides

### Configuration Loading Order
1. `config/base.yaml` (lowest priority)
2. `config/{environment}.yaml` (environment-specific)
3. `config/local.yaml` (local overrides, if exists)
4. Environment variables with `AAA_` prefix (highest priority)

### Consolidated Settings
The new `config/base.yaml` includes all settings from the legacy configuration files:
- **Advanced Prompt Defense**: Complete security configuration with all detector settings
- **Autonomy Assessment**: All autonomy calculation parameters and thresholds
- **LLM Generation**: API timeouts, model parameters, and generation settings
- **Pattern Matching**: Similarity thresholds and weighting factors
- **Rate Limiting**: Comprehensive rate limiting configuration for different user tiers
- **Recommendations**: Pattern enhancement and similarity thresholds
- **Deployment**: Health checks, rollback configuration, and monitoring settings

### Environment Variable Format
Use double underscores to separate nested keys:
```bash
# Old
PROVIDER=openai

# New
AAA_PROVIDER=openai
AAA_DATABASE__HOST=localhost
AAA_SECURITY__ENABLE_PROMPT_DEFENSE=true
AAA_ADVANCED_PROMPT_DEFENSE__ENABLED=true
AAA_AUTONOMY__MIN_AUTONOMY_THRESHOLD=0.8
```

### Local Development Setup
1. Copy `config/local.yaml.example` to `config/local.yaml`
2. Customize settings for your local environment
3. The `local.yaml` file is git-ignored and will override all other settings

### Migration Steps
1. ✅ Legacy configuration files moved to `legacy/` directory
2. ✅ Settings consolidated into hierarchical structure in `config/` directory
3. ✅ ConfigurationManager updated to support local.yaml overrides
4. ✅ All legacy settings preserved in new structure
5. Test configuration loading with new system using `app.config.settings.load_config()`

## File Organization Changes

### Test Files
- ✅ All test files moved from root directory to `app/tests/integration/`
- ✅ Import paths updated in all test files
- ✅ Test discovery and execution still works correctly

### Legacy Files
- ✅ Old `streamlit_app.py` archived to `legacy/streamlit_app_legacy.py`
- ✅ Debug files and temporary files removed
- ✅ Duplicate documentation consolidated
- ✅ Configuration files moved to `legacy/` directory

### Import Standardization
- ✅ All imports follow standard order: standard library, third-party, local
- ✅ Fallback imports replaced with proper dependency injection
- ✅ Unused imports removed throughout codebase

## Performance Improvements

### Lazy Loading
- Components are loaded on-demand to improve startup time
- Heavy imports deferred until actually needed
- Caching implemented for expensive operations

### Startup Time
- Target: 30% improvement in startup time
- Achieved through modular loading and import optimization

## Code Quality Improvements

### Type Safety
- Comprehensive type hints added throughout codebase
- Result type pattern for better error handling
- Pydantic models for configuration validation

### Error Handling
- Centralized error handling with consistent patterns
- Structured logging with PII redaction
- Graceful degradation for non-critical failures

### Documentation
- Comprehensive docstrings following established patterns
- API documentation generated from code annotations
- Migration guides and troubleshooting documentation

## Testing Strategy

### Test Organization
- Unit tests: `app/tests/unit/`
- Integration tests: `app/tests/integration/`
- End-to-end tests: `app/tests/e2e/`

### Test Coverage
- Maintain 100% test coverage requirement
- All new code must include appropriate tests
- Existing tests updated for new architecture

## Deployment Considerations

### Backward Compatibility
- All existing functionality preserved
- API endpoints remain unchanged
- Configuration migration is automatic

### Rollback Procedures
- Each phase can be rolled back independently
- Legacy files preserved for emergency rollback
- Comprehensive monitoring during migration

## Developer Workflow Changes

### Configuration Management
```python
# Old way
import yaml
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# New way
from app.config.settings import load_config
result = load_config()
if result.is_success():
    config = result.value
```

### Component Development
```python
# New base classes for consistency
from app.ui.tabs.base import BaseTab
from app.ui.components.base import BaseComponent

class MyTab(BaseTab):
    def render(self):
        # Implementation
        pass
```

### Error Handling
```python
# New Result pattern
from app.utils.result import Result

def my_function() -> Result[str, Exception]:
    try:
        # Implementation
        return Result.success("Success!")
    except Exception as e:
        return Result.error(e)
```

## Troubleshooting

### Configuration Issues
1. Check configuration loading order
2. Verify environment variable format (AAA_ prefix)
3. Validate YAML syntax in config files
4. Check file permissions on config directory

### Import Issues
1. Verify new import paths
2. Check for circular imports
3. Ensure all __init__.py files are present
4. Update IDE/editor configuration for new structure

### Performance Issues
1. Check lazy loading configuration
2. Monitor startup time metrics
3. Verify caching is working correctly
4. Profile import times if needed

## Support

For questions or issues with the migration:
1. Check this migration guide first
2. Review the troubleshooting section
3. Check the legacy files for reference
4. Contact the development team for assistance

## Validation Checklist

Before completing migration:
- [ ] All tests pass with new architecture
- [ ] Configuration loads correctly in all environments
- [ ] Performance meets or exceeds previous benchmarks
- [ ] All existing functionality works as expected
- [ ] Documentation is updated and accurate
- [ ] Rollback procedures are tested and documented