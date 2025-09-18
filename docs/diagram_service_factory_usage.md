# Diagram Service Factory Usage Guide

The Diagram Service Factory provides a centralized way to create and manage diagram services in the AAA system. It supports Mermaid diagrams, Infrastructure diagrams, and Draw.io export functionality with automatic dependency checking and graceful fallback behavior.

## Overview

The factory implements the service registry pattern and provides:
- **Feature availability checking** based on dependencies
- **Graceful fallback** to basic diagram functionality
- **Configuration-based service selection**
- **Service registry integration**

## Quick Start

### 1. Get the Factory from Service Registry

```python
from app.utils.imports import require_service

# Get the diagram service factory
diagram_factory = require_service("diagram_service_factory")
```

### 2. Create Diagram Services

```python
# Create Mermaid service
mermaid_result = diagram_factory.create_mermaid_service()
if mermaid_result.is_success():
    mermaid_service = mermaid_result.value
    
    # Validate Mermaid syntax
    is_valid, error = mermaid_service.validate_syntax(mermaid_code)
    
    # Generate diagram from prompt (requires LLM)
    diagram_code = await mermaid_service.generate_diagram(prompt, provider_config)

# Create Infrastructure service
infra_result = diagram_factory.create_infrastructure_service()
if infra_result.is_success():
    infra_service = infra_result.value
    
    # Create sample specification
    sample_spec = infra_service.create_sample_spec()
    
    # Generate diagram from specification
    diagram_path, python_code = infra_service.generate_diagram(
        diagram_spec, output_path, format="png"
    )

# Create Draw.io export service
drawio_result = diagram_factory.create_drawio_service()
if drawio_result.is_success():
    drawio_service = drawio_result.value
    
    # Export Mermaid to Draw.io format
    drawio_file = drawio_service.export_mermaid_diagram(
        mermaid_code, "My Diagram", output_path
    )
```

### 3. Use Fallback Behavior

```python
# Create service with automatic fallback
fallback_result = diagram_factory.create_service_with_fallback("infrastructure")
if fallback_result.is_success():
    service = fallback_result.value
    # Service will work even if dependencies are missing
```

## Service Types

### Mermaid Service
- **Purpose**: Generate and validate Mermaid diagrams
- **Dependencies**: None (core functionality)
- **Optional**: `streamlit-mermaid` for enhanced rendering
- **Features**: Generation, validation, rendering, export

```python
mermaid_service = diagram_factory.create_mermaid_service().value

# Validate syntax
is_valid, error = mermaid_service.validate_syntax(mermaid_code)

# Generate from prompt (async)
diagram_code = await mermaid_service.generate_diagram(prompt, provider_config)

# Render in UI (Streamlit)
mermaid_service.render_diagram(mermaid_code, height=400)
```

### Infrastructure Service
- **Purpose**: Generate infrastructure diagrams using mingrammer/diagrams
- **Dependencies**: `diagrams` package
- **Optional**: `graphviz` for rendering
- **Features**: AWS, GCP, Azure, K8s, On-prem components

```python
infra_service = diagram_factory.create_infrastructure_service().value

# Create sample specification
spec = infra_service.create_sample_spec()

# Generate diagram
diagram_path, python_code = infra_service.generate_diagram(
    spec, "output/diagram", format="png"
)
```

### Draw.io Export Service
- **Purpose**: Export diagrams to Draw.io format
- **Dependencies**: None (pure Python)
- **Features**: Mermaid export, Infrastructure export, XML generation

```python
drawio_service = diagram_factory.create_drawio_service().value

# Export Mermaid diagram
drawio_file = drawio_service.export_mermaid_diagram(
    mermaid_code, "My Diagram", "output/diagram"
)

# Export Infrastructure diagram
drawio_file = drawio_service.export_infrastructure_diagram(
    infrastructure_spec, "My Infrastructure", "output/infra"
)

# Export multiple formats
files = drawio_service.export_multiple_formats(
    {"mermaid_code": mermaid_code}, "My Diagram", "output/multi"
)
```

## Service Status and Health

### Check Service Availability

```python
# Check if specific service is available
is_available = diagram_factory.is_service_available("infrastructure")

# Get available services
available_services = diagram_factory.get_available_services()

# Get detailed service information
service_info = diagram_factory.get_service_info("mermaid")
print(f"Features: {service_info.features}")
print(f"Required packages: {service_info.required_packages}")
```

### Get Service Status

```python
# Get comprehensive status report
status = diagram_factory.get_service_status()

for service_name, service_status in status.items():
    print(f"{service_name}: {'Available' if service_status['available'] else 'Unavailable'}")
    if service_status.get('error_message'):
        print(f"  Error: {service_status['error_message']}")
```

### Installation Instructions

```python
# Get installation instructions for missing dependencies
instructions = diagram_factory.get_installation_instructions()

for service_name, instruction in instructions.items():
    print(f"To enable {service_name}:")
    print(instruction)
```

## Configuration

The factory can be configured through the service registry:

```python
config = {
    "mermaid_config": {
        "default_height": 400,
        "enable_enhanced_rendering": True,
        "theme": "default",
        "max_nodes": 100
    },
    "infrastructure_config": {
        "default_format": "png",
        "enable_dynamic_mapping": True,
        "dpi": 300,
        "font_size": 12,
        "max_components": 50
    },
    "drawio_config": {
        "enable_multiple_formats": True,
        "include_metadata": True,
        "export_path": "./exports"
    }
}

diagram_factory = DiagramServiceFactory(config)
```

## Error Handling

The factory uses the Result pattern for error handling:

```python
result = diagram_factory.create_mermaid_service()

if result.is_success():
    service = result.value
    # Use the service
else:
    error_message = result.error
    print(f"Failed to create service: {error_message}")
```

## Fallback Behavior

When dependencies are missing, the factory can provide fallback services:

```python
# This will always succeed, falling back to basic functionality if needed
fallback_result = diagram_factory.create_service_with_fallback("infrastructure")

if fallback_result.is_success():
    service = fallback_result.value
    
    if service.is_available():
        # Full functionality available
        pass
    else:
        # Basic fallback functionality
        # Service will provide text-based alternatives
        pass
```

## Integration with Existing Code

The factory integrates seamlessly with existing diagram code:

```python
# Old way (direct import with fallback)
try:
    from app.ui.mermaid_diagrams import MermaidDiagramGenerator
    mermaid_gen = MermaidDiagramGenerator()
except ImportError:
    mermaid_gen = None

# New way (service factory)
diagram_factory = require_service("diagram_service_factory")
mermaid_result = diagram_factory.create_mermaid_service()
mermaid_service = mermaid_result.value if mermaid_result.is_success() else None
```

## Best Practices

1. **Always check service availability** before using advanced features
2. **Use fallback services** for critical functionality
3. **Handle Result types properly** to catch errors early
4. **Cache service instances** when possible (factory handles this automatically)
5. **Check installation instructions** to help users resolve dependency issues

## Dependencies

### Required for Full Functionality
- `diagrams` - For infrastructure diagram generation
- `graphviz` - For rendering infrastructure diagrams
- `streamlit-mermaid` - For enhanced Mermaid rendering

### Installation
```bash
# Install Python packages
pip install diagrams streamlit-mermaid

# Install Graphviz
# Windows
choco install graphviz
# or
winget install graphviz

# macOS
brew install graphviz

# Linux
sudo apt-get install graphviz
```

## Troubleshooting

### Common Issues

1. **"Service not available"** - Check if required dependencies are installed
2. **"Graphviz not found"** - Install Graphviz system package
3. **"Import errors"** - Ensure all Python packages are installed
4. **"Service creation failed"** - Check service logs for detailed error messages

### Getting Help

```python
# Get detailed service status
status = diagram_factory.get_service_status()

# Get installation instructions
instructions = diagram_factory.get_installation_instructions()

# Check factory health
is_healthy = diagram_factory.health_check()
```