# Deployment Guide - Automated AI Assessment (AAA)

This guide covers various deployment options for Automated AI Assessment (AAA), from local development to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)
- [Monitoring and Observability](#monitoring-and-observability)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **CPU**: 2+ cores recommended
- **Memory**: 4GB+ RAM (8GB+ for production)
- **Storage**: 2GB+ free space
- **Network**: Internet access for LLM providers

### Software Requirements

- **Python**: 3.10 or higher
- **Docker**: 20.10+ (optional, for containerized deployment)
- **Docker Compose**: 2.0+ (optional)

### API Keys Required

At least one of the following LLM providers:
- **OpenAI**: API key from https://platform.openai.com/
- **Anthropic**: API key from https://console.anthropic.com/
- **AWS Bedrock**: AWS credentials with Bedrock access
- **Internal HTTP**: Custom provider endpoint

## Local Development

### Quick Start

```bash
# 1. Clone and setup
git clone <repository>
cd agentic-or-not
cp .env.example .env

# 2. Edit .env with your API keys
nano .env

# 3. Install dependencies
make install

# 4. Start services
make dev
```

This starts:
- FastAPI server at http://localhost:8000
- Streamlit UI at http://localhost:8501 (opens automatically)

### Individual Services

```bash
# Start API only
make api

# Start UI only (requires API running)
make streamlit
```

### Development Workflow

```bash
# Format code
make fmt

# Lint code
make lint

# Run tests
make test

# Run integration tests
make e2e

# Clean cache
make clean
```

## Docker Deployment

### Development with Docker

```bash
# Build images
make docker-build

# Start development environment (with live reloading)
make docker-dev
```

### Production-like with Docker

```bash
# Start production-like environment
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

### Docker Compose Profiles

#### Standard Deployment (with Redis)
```bash
docker-compose up -d
```

#### Without Redis (uses diskcache)
```bash
docker-compose --profile no-redis up api ui
```

#### With Nginx Reverse Proxy
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile nginx up -d
```

### Docker Commands Reference

```bash
# Build and start
make docker-build
make docker-up

# Development mode (live reloading)
make docker-dev

# Production mode (optimized)
make docker-prod

# View logs
make docker-logs

# Run tests in container
make docker-test

# Shell access
make docker-shell

# Stop services
make docker-down
```

## Production Deployment

### Option 1: Docker Compose (Recommended)

1. **Prepare environment**:
```bash
# Create production directory
mkdir -p /opt/agentic-or-not
cd /opt/agentic-or-not

# Copy application files
git clone <repository> .

# Setup environment
cp .env.example .env
nano .env  # Configure production settings
```

2. **Configure production settings**:
```bash
# .env file
PROVIDER=openai
MODEL=gpt-4o
LOGGING_LEVEL=INFO
REDIS_URL=redis://redis:6379/0

# API Keys
OPENAI_API_KEY=sk-your-production-key
ANTHROPIC_API_KEY=your-anthropic-key
```

3. **Deploy**:
```bash
# Start production services
make docker-prod

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Option 2: Kubernetes

Create Kubernetes manifests:

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agentic-or-not

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agentic-config
  namespace: agentic-or-not
data:
  config.yaml: |
    provider: openai
    model: gpt-4o
    logging:
      level: INFO
    redis:
      url: redis://redis:6379/0

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: agentic-secrets
  namespace: agentic-or-not
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-your-key-here"
  ANTHROPIC_API_KEY: "your-key-here"

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentic-api
  namespace: agentic-or-not
spec:
  replicas: 2
  selector:
    matchLabels:
      app: agentic-api
  template:
    metadata:
      labels:
        app: agentic-api
    spec:
      containers:
      - name: api
        image: agentic-or-not:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: agentic-secrets
              key: OPENAI_API_KEY
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

Deploy:
```bash
kubectl apply -f k8s/
```

### Option 3: Cloud Platforms

#### AWS ECS/Fargate

1. **Build and push image**:
```bash
# Build for production
docker build -t agentic-or-not:latest .

# Tag for ECR
docker tag agentic-or-not:latest <account>.dkr.ecr.<region>.amazonaws.com/agentic-or-not:latest

# Push to ECR
docker push <account>.dkr.ecr.<region>.amazonaws.com/agentic-or-not:latest
```

2. **Create ECS task definition**:
```json
{
  "family": "agentic-or-not",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<account>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account>.dkr.ecr.<region>.amazonaws.com/agentic-or-not:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "PROVIDER",
          "value": "bedrock"
        }
      ],
      "secrets": [
        {
          "name": "AWS_ACCESS_KEY_ID",
          "valueFrom": "arn:aws:secretsmanager:<region>:<account>:secret:agentic-secrets"
        }
      ]
    }
  ]
}
```

#### Google Cloud Run

```bash
# Build and deploy
gcloud run deploy agentic-or-not \
  --image gcr.io/<project>/agentic-or-not:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PROVIDER=openai \
  --set-secrets OPENAI_API_KEY=openai-key:latest
```

## Environment Configuration

### Environment Variables

Create `.env` file with required settings:

```bash
# LLM Provider Configuration
PROVIDER=openai                    # openai, anthropic, bedrock, internal
MODEL=gpt-4o                      # Model name
OPENAI_API_KEY=sk-...             # OpenAI API key
ANTHROPIC_API_KEY=...             # Anthropic API key
AWS_ACCESS_KEY_ID=...             # AWS credentials
AWS_SECRET_ACCESS_KEY=...         # AWS credentials

# Jira Integration (Optional)
JIRA_BASE_URL=https://company.atlassian.net
JIRA_EMAIL=user@company.com
JIRA_API_TOKEN=...

# Application Settings
LOGGING_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR
REDIS_URL=redis://localhost:6379/0  # Redis connection string

# Security (Production)
SECRET_KEY=your-secret-key-here   # For session encryption
ALLOWED_HOSTS=localhost,yourdomain.com
CORS_ORIGINS=https://yourdomain.com
```

### Configuration File (config.yaml)

```yaml
# Application Configuration
provider: openai
model: gpt-4o
pattern_library_path: ./data/patterns
export_path: ./exports

# Constraints
constraints:
  unavailable_tools: []
  max_patterns: 10

# Timeouts
timeouts:
  llm: 30
  http: 10
  redis: 5

# Logging
logging:
  level: INFO
  redact_pii: true
  format: json

# Provider-specific settings
bedrock:
  region: us-east-1
  model_id: anthropic.claude-3-sonnet-20240229-v1:0

openai:
  base_url: https://api.openai.com/v1
  timeout: 30

# Redis settings
redis:
  url: redis://localhost:6379/0
  ttl: 3600
  max_connections: 10
```

## Monitoring and Observability

### Health Checks

The application provides health check endpoints:

```bash
# API health
curl http://localhost:8000/health

# Streamlit health (Docker)
curl http://localhost:8501/_stcore/health
```

### Logging

Logs are structured JSON format in production:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "message": "LLM request completed",
  "session_id": "abc123",
  "provider": "openai",
  "model": "gpt-4o",
  "latency_ms": 1500,
  "tokens": 150
}
```

### Metrics Collection

The application includes built-in observability:

- **SQLite audit database**: Tracks LLM calls and pattern matches
- **Streamlit dashboard**: Performance metrics and usage patterns
- **Health checks**: Service availability monitoring

### External Monitoring

#### Prometheus Metrics

Add Prometheus metrics endpoint:

```python
# app/metrics.py
from prometheus_client import Counter, Histogram, generate_latest

llm_requests = Counter('llm_requests_total', 'Total LLM requests', ['provider', 'model'])
llm_latency = Histogram('llm_request_duration_seconds', 'LLM request latency')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### Grafana Dashboard

Create dashboard with panels for:
- Request rate and latency
- Error rates by provider
- Pattern matching accuracy
- Resource utilization

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
make docker-logs

# Common fixes
docker-compose down
docker-compose build --no-cache
make docker-up
```

#### 2. API Connection Errors

```bash
# Test API directly
curl http://localhost:8000/health

# Check environment variables
docker-compose exec api env | grep API_KEY

# Verify network connectivity
docker-compose exec api ping api
```

#### 3. LLM Provider Issues

```bash
# Test provider connection
docker-compose exec api python3 -c "
from app.llm.openai_provider import OpenAIProvider
import asyncio
provider = OpenAIProvider()
print(asyncio.run(provider.test_connection()))
"
```

#### 4. Redis Connection Issues

```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Test connection from API
docker-compose exec api python3 -c "
import redis
r = redis.from_url('redis://redis:6379/0')
print(r.ping())
"
```

#### 5. Performance Issues

```bash
# Check resource usage
docker stats

# Scale services
docker-compose up -d --scale api=3

# Check logs for bottlenecks
make docker-logs | grep -E "(ERROR|WARNING|slow)"
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Environment variable
export LOGGING_LEVEL=DEBUG

# Or in .env file
LOGGING_LEVEL=DEBUG

# Restart services
make docker-down
make docker-up
```

### Log Analysis

```bash
# View recent logs
make docker-logs --tail=100

# Filter by service
docker-compose logs api

# Search for errors
make docker-logs | grep ERROR

# Monitor in real-time
make docker-logs -f
```

### Performance Tuning

#### Resource Limits

Adjust Docker resource limits in `docker-compose.prod.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'      # Increase CPU
          memory: 2G       # Increase memory
        reservations:
          cpus: '1.0'
          memory: 1G
```

#### Redis Optimization

```yaml
redis:
  command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
```

#### Application Tuning

```yaml
# config.yaml
timeouts:
  llm: 60          # Increase for complex requests
  http: 30
  redis: 10

constraints:
  max_patterns: 20  # Increase for better matching
```

## Security Considerations

### Production Security Checklist

- [ ] Use strong, unique API keys
- [ ] Enable HTTPS/TLS encryption
- [ ] Configure firewall rules
- [ ] Use non-root container users
- [ ] Enable PII redaction in logs
- [ ] Rotate API keys regularly
- [ ] Monitor for suspicious activity
- [ ] Keep dependencies updated
- [ ] Use secrets management (not .env files)
- [ ] Enable audit logging

### Secrets Management

#### Docker Secrets

```yaml
# docker-compose.yml
services:
  api:
    secrets:
      - openai_api_key
    environment:
      - OPENAI_API_KEY_FILE=/run/secrets/openai_api_key

secrets:
  openai_api_key:
    file: ./secrets/openai_api_key.txt
```

#### Kubernetes Secrets

```bash
kubectl create secret generic agentic-secrets \
  --from-literal=OPENAI_API_KEY=sk-your-key \
  --namespace=agentic-or-not
```

### Network Security

```yaml
# docker-compose.yml
networks:
  internal:
    driver: bridge
    internal: true
  external:
    driver: bridge

services:
  api:
    networks:
      - internal
      - external
  redis:
    networks:
      - internal  # Redis not exposed externally
```

## Backup and Recovery

### Data Backup

```bash
# Backup Redis data
docker-compose exec redis redis-cli BGSAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb ./backup/

# Backup exports and cache
tar -czf backup/data-$(date +%Y%m%d).tar.gz exports/ cache/

# Backup configuration
cp .env config.yaml backup/
```

### Disaster Recovery

```bash
# Restore Redis data
docker cp ./backup/dump.rdb $(docker-compose ps -q redis):/data/
docker-compose restart redis

# Restore application data
tar -xzf backup/data-20240101.tar.gz
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      replicas: 3  # Scale API instances

  # Add load balancer
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - api
```

### Vertical Scaling

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4.0'    # More CPU
          memory: 8G     # More memory
```

This deployment guide covers the essential aspects of deploying Automated AI Assessment (AAA) in various environments. Choose the deployment method that best fits your infrastructure and requirements.