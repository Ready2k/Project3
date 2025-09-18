# Import Fallback Catalog

## Summary Statistics
- **Total Fallback Patterns**: 23
- **Files Affected**: 8 core files + test files
- **Required Services**: 8
- **Optional Services**: 12
- **Test-Only Patterns**: 3

## Categorized Import Patterns

### REQUIRED SERVICES (8 patterns)

#### 1. Core Logging (Priority: CRITICAL)
| Location | Pattern | Impact | Migration Complexity |
|----------|---------|---------|---------------------|
| `streamlit_app.py:19` | `app.utils.logger` fallback | HIGH | LOW |
| Multiple locations | `app.utils.audit` fallback | HIGH | MEDIUM |

#### 2. Pattern Management (Priority: HIGH)
| Location | Pattern | Impact | Migration Complexity |
|----------|---------|---------|---------------------|
| `streamlit_app.py:7172` | `app.pattern.loader` | HIGH | MEDIUM |
| `streamlit_app.py:8530` | `app.pattern.enhanced_loader` | HIGH | MEDIUM |
| `streamlit_app.py:8531` | `app.services.pattern_enhancement_service` | HIGH | MEDIUM |

#### 3. Core Services (Priority: HIGH)
| Location | Pattern | Impact | Migration Complexity |
|----------|---------|---------|---------------------|
| `streamlit_app.py:4633` | `app.services.tech_stack_generator` | MEDIUM | LOW |
| `streamlit_app.py:4753` | `app.services.architecture_explainer` | MEDIUM | MEDIUM |
| `streamlit_app.py:8553` | `app.llm.fakes` | MEDIUM | LOW |

### OPTIONAL SERVICES (12 patterns)

#### 1. LLM Providers (Priority: MEDIUM)
| Location | Pattern | Impact | Migration Complexity |
|----------|---------|---------|---------------------|
| `streamlit_app.py:27` | `openai` library | MEDIUM | LOW |

#### 2. Diagram Services (Priority: MEDIUM)
| Location | Pattern | Impact | Migration Complexity |
|----------|---------|---------|---------------------|
| `app/diagrams/infrastructure.py:16` | `diagrams` library (full suite) | MEDIUM | HIGH |
| `streamlit_app.py:6106` | `streamlit_mermaid` (large view) | MEDIUM | LOW |
| `streamlit_app.py:6123` | `streamlit_mermaid` (regular view) | MEDIUM | LOW |
| `app/ui/mermaid_diagrams.py:237` | `streamlit_mermaid` (core) | MEDIUM | LOW |
| `app/ui/analysis_display.py:321` | `streamlit_mermaid` (analysis) | MEDIUM | LOW |
| `app/ui/analysis_display.py:605` | `streamlit_mermaid` (flow) | MEDIUM | LOW |

#### 3. Export Services (Priority: LOW)
| Location | Pattern | Impact | Migration Complexity |
|----------|---------|---------|---------------------|
| `streamlit_app.py:6341` | `app.exporters.drawio_exporter` | LOW | LOW |
| `streamlit_app.py:6406` | `app.exporters.drawio_exporter` | LOW | LOW |

#### 4. Infrastructure Services (Priority: LOW)
| Location | Pattern | Impact | Migration Complexity |
|----------|---------|---------|---------------------|
| `streamlit_app.py:6515` | `app.diagrams.infrastructure` | MEDIUM | MEDIUM |
| `streamlit_app.py:6658` | `app.diagrams.infrastructure` | MEDIUM | MEDIUM |

#### 5. Monitoring Services (Priority: LOW)
| Location | Pattern | Impact | Migration Complexity |
|----------|---------|---------|---------------------|
| `app/security/performance_optimizer.py:22` | `psutil` library | LOW | LOW |

### TEST-ONLY PATTERNS (3 patterns)

#### 1. Test Infrastructure (Priority: LOW)
| Location | Pattern | Impact | Migration Complexity |
|----------|---------|---------|---------------------|
| `app/tests/unit/test_observability_dashboard.py:16` | `streamlit` availability | LOW | LOW |
| `app/tests/e2e/test_streamlit_ui.py:22` | `streamlit` availability | LOW | LOW |
| `app/tests/e2e/test_streamlit_ui.py:425` | Mermaid test functions | LOW | LOW |

## Detailed Pattern Analysis

### High-Impact Patterns (Immediate Action Required)

#### Logger Fallback Pattern
```python
# Current (problematic)
try:
    from app.utils.logger import app_logger
except ImportError:
    import logging
    app_logger = logging.getLogger(__name__)

# Target (service registry)
from app.utils.imports import require_service
app_logger = require_service('logger')
```
**Risk**: Core functionality failure if logger service unavailable
**Mitigation**: Ensure logger service is always available at startup

#### Audit Logger Pattern
```python
# Current (problematic)
try:
    from app.utils.audit import get_audit_logger
except ImportError:
    pass  # Silent failure

# Target (service registry)
from app.utils.imports import require_service
audit_logger = require_service('audit_logger')
```
**Risk**: Security compliance issues if audit logging fails silently
**Mitigation**: Make audit logging failure visible and actionable

### Medium-Impact Patterns (Planned Migration)

#### Diagram Service Pattern
```python
# Current (problematic)
try:
    from diagrams import Diagram, Cluster, Edge
    DIAGRAMS_AVAILABLE = True
except ImportError:
    DIAGRAMS_AVAILABLE = False

# Target (service factory)
from app.utils.imports import optional_service
diagram_service = optional_service('diagram_service', type='infrastructure')
if diagram_service:
    # Use diagram functionality
else:
    # Graceful degradation
```
**Risk**: Feature unavailability but application continues
**Mitigation**: Clear user messaging about missing features

#### LLM Provider Pattern
```python
# Current (problematic)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Target (provider factory)
from app.utils.imports import optional_service
llm_provider = optional_service('llm_provider', provider='openai')
if llm_provider:
    # Use LLM functionality
else:
    # Use fallback or mock provider
```
**Risk**: AI features unavailable
**Mitigation**: Fallback to mock providers or alternative implementations

### Low-Impact Patterns (Future Enhancement)

#### Performance Monitoring Pattern
```python
# Current (problematic)
try:
    import psutil
except ImportError:
    psutil = None

# Target (monitoring service)
from app.utils.imports import optional_service
monitor = optional_service('performance_monitor')
if monitor:
    metrics = monitor.get_system_metrics()
```
**Risk**: Missing performance metrics
**Mitigation**: Acceptable degradation, metrics not critical

## Migration Complexity Assessment

### LOW Complexity (13 patterns)
- Simple library imports with boolean flags
- Direct replacement with service registry calls
- Minimal testing required
- Examples: `openai`, `psutil`, `streamlit_mermaid`

### MEDIUM Complexity (8 patterns)
- Service imports with configuration
- Multiple fallback behaviors
- Integration testing required
- Examples: `audit_logger`, `pattern_services`, `architecture_explainer`

### HIGH Complexity (2 patterns)
- Complex library suites with many imports
- Multiple component dependencies
- Extensive testing required
- Examples: `diagrams` library suite

## Service Registration Requirements

### Core Services (Must be available at startup)
1. **Logger Service**: `app.utils.logger.app_logger`
2. **Audit Service**: `app.utils.audit.get_audit_logger`
3. **Pattern Loader**: `app.pattern.loader.PatternLoader`
4. **Enhanced Pattern Loader**: `app.pattern.enhanced_loader.EnhancedPatternLoader`
5. **Pattern Enhancement Service**: `app.services.pattern_enhancement_service.PatternEnhancementService`

### Optional Services (Graceful degradation allowed)
1. **LLM Provider Factory**: Multiple providers (OpenAI, Anthropic, Bedrock)
2. **Diagram Service Factory**: Infrastructure, Mermaid, Draw.io
3. **Export Service Factory**: Various export formats
4. **Monitoring Service**: Performance and system metrics
5. **Architecture Services**: AI-powered architecture explanation

### Test Services (Development only)
1. **Test Dependency Checker**: Streamlit availability
2. **Mock Service Factory**: Test doubles for services
3. **Test Configuration**: Environment-specific settings

## Implementation Priority Matrix

| Priority | Complexity | Patterns | Timeline |
|----------|------------|----------|----------|
| CRITICAL | LOW | 1 | Week 1, Day 1 |
| HIGH | MEDIUM | 7 | Week 1, Days 2-5 |
| MEDIUM | LOW | 6 | Week 2, Days 1-3 |
| MEDIUM | MEDIUM | 4 | Week 2, Days 4-5 |
| MEDIUM | HIGH | 2 | Week 3, Days 1-2 |
| LOW | LOW | 3 | Week 3, Days 3-5 |

## Validation Checklist

### Pre-Migration Validation
- [ ] All fallback patterns identified and cataloged
- [ ] Service interfaces defined for each pattern
- [ ] Migration complexity assessed
- [ ] Test coverage planned
- [ ] Rollback strategy defined

### Post-Migration Validation
- [ ] Zero fallback import patterns remain
- [ ] All services registered in service registry
- [ ] Service resolution working correctly
- [ ] Error messages clear and actionable
- [ ] Performance impact acceptable
- [ ] Full test suite passing
- [ ] Documentation updated

## Risk Assessment Summary

### HIGH RISK (Immediate attention required)
- **Logger fallbacks**: Core functionality dependency
- **Audit logger fallbacks**: Security and compliance critical
- **Pattern service fallbacks**: Core business logic

### MEDIUM RISK (Planned migration)
- **LLM provider fallbacks**: Feature degradation acceptable
- **Diagram service fallbacks**: Graceful degradation possible
- **Architecture service fallbacks**: Optional feature

### LOW RISK (Future enhancement)
- **Performance monitoring fallbacks**: Nice-to-have metrics
- **Export service fallbacks**: Optional export features
- **Test infrastructure fallbacks**: Development-only impact

This catalog provides the foundation for systematic migration of all fallback import patterns to a proper service registry architecture.