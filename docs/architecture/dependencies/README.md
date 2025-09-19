# Dependency Management System Documentation

This directory contains comprehensive documentation and tools for the dependency management system implemented in the Automated AI Assessment (AAA) project.

## Overview

The dependency management system provides:

- **Visual dependency graphs** from service registry
- **Comprehensive service documentation** with relationships
- **API documentation** generated from type hints
- **Dependency validation tools** for monitoring system health
- **Service registry inspection** utilities
- **Report templates** for automated monitoring

## Generated Documentation

### Core Documentation Files

- **[SERVICE_DEPENDENCIES.md](./SERVICE_DEPENDENCIES.md)** - Complete service dependency documentation with visual diagrams
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - Comprehensive API documentation for the service registry system
- **[dependency_analysis.json](./dependency_analysis.json)** - Machine-readable dependency analysis data

### Visual Diagrams

- **[service_dependency_graph.mmd](./service_dependency_graph.mmd)** - Mermaid diagram source for service dependencies
- **[service_dependency_graph.dot](./service_dependency_graph.dot)** - Graphviz DOT file for dependency visualization

### Report Templates

The `templates/` directory contains templates for generating dependency reports:

- **dependency_report.html** - HTML template for web-based reports
- **dependency_report.json** - JSON template for structured data reports
- **dependency_report.md** - Markdown template for documentation reports

## Tools and Scripts

### 1. Dependency Graph Generator

**Script:** `scripts/generate_dependency_graphs.py`

Generates visual dependency graphs and comprehensive documentation from the service registry.

```bash
# Generate all dependency documentation
python3 scripts/generate_dependency_graphs.py

# Generate with custom configuration
python3 scripts/generate_dependency_graphs.py --config config/services.yaml --output-dir docs/custom
```

**Features:**
- Mermaid diagram generation with category-based styling
- Graphviz DOT file generation for advanced visualization
- JSON analysis reports with dependency metrics
- Comprehensive Markdown documentation
- API documentation from type hints
- Report templates for monitoring

### 2. Dependency Validator

**Script:** `scripts/dependency_validator_simple.py`

Validates system dependencies and generates health reports.

```bash
# Validate all dependencies
python3 scripts/dependency_validator_simple.py validate --verbose

# Generate dependency report
python3 scripts/dependency_validator_simple.py report --output custom_report.json

# Install missing dependencies (dry run)
python3 scripts/dependency_validator_simple.py install --dry-run

# Install missing dependencies
python3 scripts/dependency_validator_simple.py install
```

**Features:**
- Required and optional dependency validation
- Version checking and constraint validation
- Installation instruction generation
- Comprehensive reporting in JSON and Markdown formats
- Automated dependency installation

### 3. Service Registry Inspector

**Script:** `scripts/service_inspector.py`

Provides detailed inspection and analysis of the service registry.

```bash
# Inspect a specific service
python3 scripts/service_inspector.py inspect logger --detailed

# Analyze dependency chain
python3 scripts/service_inspector.py analyze llm_provider_factory

# Generate service map
python3 scripts/service_inspector.py map --format markdown

# Monitor service lifecycle
python3 scripts/service_inspector.py monitor --service cache

# Debug service issues
python3 scripts/service_inspector.py debug --service security_validator
```

**Features:**
- Detailed service inspection with instance information
- Dependency chain analysis with cycle detection
- Service lifecycle monitoring
- Health status checking
- Issue debugging with recommendations
- Service map generation in multiple formats

## Service Categories

Services are organized into the following categories for better management:

### Core Services
- **logger** - Application logging service
- **config** - Configuration management service
- **cache** - Caching service with multiple backends

### Security Services
- **security_validator** - Input validation and sanitization
- **advanced_prompt_defender** - Advanced prompt attack detection

### LLM Services
- **llm_provider_factory** - Factory for LLM provider creation
- **openai_provider** - OpenAI API integration
- **anthropic_provider** - Anthropic Claude API integration
- **bedrock_provider** - AWS Bedrock integration

### Diagram Services
- **diagram_service_factory** - Factory for diagram service creation
- **mermaid_service** - Mermaid diagram generation
- **infrastructure_diagram_service** - Infrastructure diagram creation

### Analysis Services
- **pattern_matcher** - Pattern matching and analysis
- **agentic_matcher** - Agentic pattern matching
- **embedding_engine** - Text embedding and similarity

### Export Services
- **export_service** - Export functionality for reports and diagrams

### Monitoring Services
- **performance_monitor** - Performance metrics collection
- **health_checker** - System health monitoring

### Integration Services
- **jira_service** - JIRA integration for ticket management

### Pattern Services
- **pattern_loader** - Pattern library loading and management

## Dependency Validation

The system validates dependencies at multiple levels:

### 1. System Dependencies
- Python package availability
- Version constraint checking
- Installation instruction generation
- Alternative package suggestions

### 2. Service Dependencies
- Service registration validation
- Circular dependency detection
- Missing dependency identification
- Health status monitoring

### 3. Configuration Validation
- Service configuration completeness
- Dependency reference validation
- Environment-specific overrides

## Monitoring and Health Checks

### Health Check Endpoints

Services implement health checks that can be monitored:

```python
# Check all services
health_status = registry.health_check()

# Check specific service
logger_health = registry.health_check('logger')
```

### Performance Monitoring

The system tracks:
- Service initialization time
- Dependency resolution performance
- Memory usage of service instances
- Health check response times

### Automated Reporting

Generate automated reports for:
- Daily dependency health checks
- Service performance metrics
- Configuration validation results
- Security scan results

## Best Practices

### Service Development

1. **Implement Service Interface**
   ```python
   from app.core.service import Service, ConfigurableService
   
   class MyService(ConfigurableService):
       def _do_initialize(self) -> None:
           # Service initialization logic
           pass
   ```

2. **Define Dependencies Clearly**
   ```yaml
   my_service:
     class_path: "app.services.my_service.MyService"
     dependencies: ["logger", "config", "cache"]
   ```

3. **Implement Health Checks**
   ```python
   def _do_health_check(self) -> bool:
       # Check service health
       return self.is_operational()
   ```

### Dependency Management

1. **Use Semantic Versioning**
   ```yaml
   dependencies:
     required:
       - name: "fastapi"
         version_constraint: ">=0.104.0,<1.0.0"
   ```

2. **Provide Alternatives**
   ```yaml
   - name: "redis"
     alternatives: ["memory_cache", "file_cache"]
   ```

3. **Document Purpose**
   ```yaml
   - name: "openai"
     purpose: "OpenAI API integration for LLM services"
   ```

### Configuration Management

1. **Environment-Specific Overrides**
   ```yaml
   environments:
     development:
       logger:
         config:
           level: "DEBUG"
   ```

2. **Graceful Degradation**
   ```python
   cache = optional_service('cache')
   if cache:
       # Use caching
   else:
       # Fallback behavior
   ```

## Troubleshooting

### Common Issues

1. **Circular Dependencies**
   - Use the dependency analyzer to identify cycles
   - Refactor services to remove circular references
   - Consider using event-driven patterns

2. **Missing Dependencies**
   - Run dependency validation to identify missing packages
   - Use installation instructions provided by the validator
   - Check for typos in dependency names

3. **Service Initialization Failures**
   - Check service logs for detailed error messages
   - Verify all dependencies are available
   - Validate service configuration

4. **Health Check Failures**
   - Verify external dependencies (databases, APIs)
   - Check network connectivity
   - Review service-specific health check logic

### Debugging Commands

```bash
# Validate all dependencies
python3 scripts/dependency_validator_simple.py validate --verbose

# Debug specific service
python3 scripts/service_inspector.py debug --service problematic_service

# Analyze dependency chain
python3 scripts/service_inspector.py analyze problematic_service

# Generate comprehensive report
python3 scripts/dependency_validator_simple.py report
```

## Integration with CI/CD

### Pre-commit Hooks

Add dependency validation to pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-dependencies
        name: Validate Dependencies
        entry: python3 scripts/dependency_validator_simple.py validate
        language: system
        pass_filenames: false
```

### CI Pipeline

Include dependency validation in CI:

```yaml
# .github/workflows/ci.yml
- name: Validate Dependencies
  run: |
    python3 scripts/dependency_validator_simple.py validate
    python3 scripts/service_inspector.py debug
```

### Automated Reporting

Schedule regular dependency reports:

```bash
# Cron job for daily reports
0 6 * * * cd /path/to/project && python3 scripts/dependency_validator_simple.py report --output daily_report_$(date +%Y%m%d).json
```

## Future Enhancements

### Planned Features

1. **Real-time Monitoring Dashboard**
   - Web-based service health dashboard
   - Real-time dependency status updates
   - Performance metrics visualization

2. **Automated Dependency Updates**
   - Dependency update notifications
   - Automated security patch detection
   - Compatibility testing for updates

3. **Advanced Analytics**
   - Service usage analytics
   - Performance trend analysis
   - Dependency impact assessment

4. **Integration Enhancements**
   - Kubernetes health check integration
   - Prometheus metrics export
   - Grafana dashboard templates

### Contributing

To contribute to the dependency management system:

1. Follow the existing patterns for service development
2. Add comprehensive tests for new functionality
3. Update documentation for any changes
4. Ensure all dependency validation passes
5. Add appropriate type hints and docstrings

## Support

For issues or questions about the dependency management system:

1. Check the troubleshooting section above
2. Run the diagnostic tools provided
3. Review the generated documentation
4. Check service logs for detailed error information

## References

- [Service Registry Guide](../../development/SERVICE_REGISTRY_GUIDE.md)
- [Dependency Management Guide](../../development/DEPENDENCY_MANAGEMENT_GUIDE.md)
- [Type Checking Documentation](../../development/TYPE_CHECKING.md)
- [Architecture Overview](../ARCHITECTURE.md)