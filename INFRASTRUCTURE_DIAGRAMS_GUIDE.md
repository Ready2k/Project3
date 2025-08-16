# Infrastructure Diagrams Guide

This guide explains the new Infrastructure Diagram feature that supports both Mermaid and mingrammer/diagrams rendering.

## Overview

The AAA system now supports two types of diagram rendering:

1. **Mermaid Diagrams** (existing): Fast text-based diagrams for Context, Container, Sequence, and Tech Stack Wiring
2. **Infrastructure Diagrams** (new): Cloud architecture diagrams with vendor-specific icons using mingrammer/diagrams

## Features

### Infrastructure Diagram Support

- **Cloud Providers**: AWS, GCP, Azure, Kubernetes, On-Premises, SaaS
- **Component Types**: Compute, Database, Storage, Network, Integration, Security, Analytics, ML
- **Output Formats**: PNG and SVG
- **Code Generation**: Generates Python code using mingrammer/diagrams library

### Supported Components

#### AWS
- **Compute**: Lambda, EC2, ECS, Fargate, Batch
- **Database**: RDS, DynamoDB, Redshift, ElastiCache
- **Storage**: S3, EFS
- **Network**: API Gateway, CloudFront, ELB, VPC
- **Integration**: SQS, SNS, EventBridge
- **Security**: IAM, Cognito
- **Analytics**: Kinesis, Glue
- **ML**: SageMaker

#### GCP
- **Compute**: Functions, GCE, GKE, Cloud Run
- **Database**: Cloud SQL, Firestore, Bigtable
- **Storage**: Cloud Storage
- **Network**: Load Balancing, CDN
- **Analytics**: BigQuery, Dataflow
- **ML**: AI Platform, AutoML

#### Azure
- **Compute**: Functions, VM, AKS, Container Instances
- **Database**: SQL Database, Cosmos DB
- **Storage**: Blob Storage
- **Network**: Load Balancer, Application Gateway
- **Analytics**: Synapse Analytics
- **ML**: Machine Learning Service, Cognitive Services

#### Kubernetes
- **Compute**: Pod, Deployment, Job
- **Network**: Service, Ingress
- **Storage**: PV, PVC

#### On-Premises
- **Compute**: Server
- **Database**: PostgreSQL, MySQL, MongoDB, MariaDB
- **Network**: Nginx
- **Analytics**: Spark

#### SaaS
- **Identity**: Auth0, Okta
- **Chat**: Slack, Teams
- **Analytics**: Snowflake, Stitch

## Usage

### In Streamlit UI

1. Navigate to the **Diagrams** tab
2. Select **"Infrastructure Diagram"** from the dropdown
3. Click **"Generate Infrastructure Diagram"**
4. View the generated diagram with vendor-specific icons
5. Use the control buttons:
   - **🔍 Large View**: Toggle between normal and large view
   - **💾 Download**: Save PNG, SVG, and Python code to exports/
   - **📋 Show Code**: View generated Python code and JSON specification

### LLM Integration

The system uses LLM to generate infrastructure specifications in JSON format:

```json
{
  "title": "Infrastructure Diagram Title",
  "clusters": [
    {
      "provider": "aws",
      "name": "AWS Cloud",
      "nodes": [
        {"id": "api_gateway", "type": "apigateway", "label": "API Gateway"},
        {"id": "lambda_func", "type": "lambda", "label": "Lambda Function"}
      ]
    }
  ],
  "nodes": [
    {"id": "user", "type": "server", "provider": "onprem", "label": "User"}
  ],
  "edges": [
    ["user", "api_gateway", "HTTPS"],
    ["api_gateway", "lambda_func", "invoke"]
  ]
}
```

### Generated Python Code

The system automatically generates Python code using mingrammer/diagrams:

```python
from diagrams import Diagram, Cluster, Edge
from diagrams.aws import compute as aws_compute, network as aws_network

with Diagram("Infrastructure Diagram", show=False, filename="diagram", direction="TB"):
    with Cluster("AWS Cloud"):
        api_gateway = aws_network.APIGateway("API Gateway")
        lambda_func = aws_compute.Lambda("Lambda Function")
    
    user = onprem_compute.Server("User")
    user >> Edge(label="HTTPS") >> api_gateway
    api_gateway >> Edge(label="invoke") >> lambda_func
```

## Installation

### Dependencies

The infrastructure diagram feature requires additional dependencies:

```bash
pip install diagrams
```

### System Requirements

**Graphviz** must be installed on the system:

```bash
# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt-get install graphviz

# CentOS/RHEL
sudo yum install graphviz
```

### Docker Support

The Dockerfile has been updated to include Graphviz:

```dockerfile
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    graphviz \
    && rm -rf /var/lib/apt/lists/*
```

## API Integration

### FastAPI Endpoint

Infrastructure diagrams can be generated via API (when implemented):

```python
POST /api/diagrams/infrastructure
{
  "requirement": "Build a web application",
  "recommendations": [...],
  "format": "png"  # or "svg"
}
```

### Response Format

```json
{
  "diagram_path": "/path/to/diagram.png",
  "python_code": "from diagrams import...",
  "specification": {...}
}
```

## Configuration

### Component Mapping

The system includes a comprehensive mapping from component types to diagrams classes:

```python
component_mapping = {
    "aws": {
        "lambda": aws_compute.Lambda,
        "dynamodb": aws_database.Dynamodb,
        "s3": aws_storage.SimpleStorageServiceS3,
        # ... more components
    },
    # ... other providers
}
```

### Error Handling

- **Missing Dependencies**: Graceful fallback to JSON specification display
- **Invalid Specifications**: Automatic fallback to sample infrastructure
- **Generation Failures**: Error messages with troubleshooting suggestions

## Testing

### Unit Tests

```bash
python3 test_infrastructure_diagrams.py
```

### Integration Tests

```bash
python3 test_streamlit_integration.py
```

### Manual Testing

1. Start the Streamlit application
2. Submit a requirement
3. Navigate to Diagrams tab
4. Select "Infrastructure Diagram"
5. Generate and verify the diagram

## Troubleshooting

### Common Issues

1. **"Diagrams library not available"**
   - Install: `pip install diagrams`
   - Install Graphviz system dependency

2. **"dot not found"**
   - Install Graphviz: `brew install graphviz` (macOS) or `apt-get install graphviz` (Linux)

3. **"Component type not found"**
   - Check the component mapping in `app/diagrams/infrastructure.py`
   - Verify the component exists in the diagrams library

4. **"Generation failed"**
   - Check LLM provider configuration
   - Verify API key is valid
   - Try with fake provider for testing

### Debug Mode

Enable debug information in the Streamlit sidebar to troubleshoot issues:

- Session ID and requirements
- Provider configuration
- API key status
- Error details

## File Structure

```
app/
├── diagrams/
│   ├── __init__.py
│   └── infrastructure.py          # Infrastructure diagram generator
├── main.py                        # Streamlit UI integration
└── ...

streamlit_app.py                   # Main Streamlit application
requirements.txt                   # Updated with diagrams dependency
Dockerfile                         # Updated with Graphviz
test_infrastructure_diagrams.py    # Unit tests
test_streamlit_integration.py      # Integration tests
```

## Future Enhancements

### Planned Features

1. **More Cloud Providers**: Oracle Cloud, IBM Cloud, Alibaba Cloud
2. **Custom Icons**: Support for custom component icons
3. **Interactive Diagrams**: Clickable components with details
4. **Diagram Templates**: Pre-built architecture patterns
5. **Export Options**: PDF, PowerPoint integration
6. **Collaboration**: Shared diagram editing and comments

### API Enhancements

1. **Batch Generation**: Generate multiple diagram types at once
2. **Caching**: Cache generated diagrams for performance
3. **Versioning**: Track diagram changes over time
4. **Integration**: Webhook support for external systems

## Best Practices

### Diagram Design

1. **Keep it Simple**: Limit to 10-15 components per diagram
2. **Use Clusters**: Group related components logically
3. **Clear Labels**: Use descriptive, concise labels
4. **Consistent Naming**: Follow naming conventions for components

### Performance

1. **Cache Results**: Store generated diagrams for reuse
2. **Optimize Images**: Use appropriate formats (PNG for web, SVG for print)
3. **Batch Operations**: Generate multiple formats together
4. **Error Recovery**: Implement robust fallback mechanisms

### Security

1. **Input Validation**: Sanitize LLM-generated specifications
2. **File Permissions**: Secure temporary file handling
3. **Resource Limits**: Prevent excessive resource usage
4. **Access Control**: Implement proper authentication for API endpoints