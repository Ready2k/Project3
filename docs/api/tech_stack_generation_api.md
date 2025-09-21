# Technology Stack Generation API Documentation

## Overview

This document provides comprehensive API documentation for the Enhanced Technology Stack Generation system. The API enables programmatic access to technology extraction, context analysis, catalog management, and tech stack generation capabilities.

## Base URL and Authentication

**Base URL:** `http://localhost:8000/api/v1`

**Authentication:** Bearer token (for protected endpoints)
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/v1/tech-stack/generate
```

## Core API Endpoints

### Technology Stack Generation

#### Generate Technology Stack

**Endpoint:** `POST /tech-stack/generate`

**Description:** Generate a technology stack based on user requirements with enhanced context awareness.

**Request Body:**
```json
{
  "requirements": {
    "title": "Customer Service Platform",
    "description": "Build a customer service platform using Amazon Connect for call handling and AWS Lambda for processing",
    "functional_requirements": [
      "Handle incoming customer calls",
      "Route calls based on inquiry type",
      "Generate automated responses"
    ],
    "non_functional_requirements": [
      "Support 1000+ concurrent calls",
      "99.9% uptime requirement",
      "Sub-second response time"
    ],
    "constraints": {
      "cloud_provider": "aws",
      "programming_language": "python",
      "budget": "medium",
      "timeline": "3_months"
    }
  },
  "options": {
    "include_reasoning": true,
    "confidence_threshold": 0.7,
    "max_technologies": 10,
    "ecosystem_preference": "aws"
  }
}
```

**Response:**
```json
{
  "tech_stack": {
    "id": "ts_abc123",
    "technologies": [
      {
        "id": "amazon-connect",
        "name": "Amazon Connect",
        "category": "communication",
        "confidence": 1.0,
        "priority": "explicit",
        "reasoning": "Explicitly mentioned in requirements for call handling"
      },
      {
        "id": "aws-lambda",
        "name": "AWS Lambda",
        "category": "compute",
        "confidence": 1.0,
        "priority": "explicit",
        "reasoning": "Explicitly mentioned for processing functionality"
      }
    ],
    "metadata": {
      "generation_time": 2.3,
      "total_confidence": 0.92,
      "ecosystem_consistency": "aws",
      "validation_status": "passed"
    }
  },
  "extraction_details": {
    "explicit_technologies": ["Amazon Connect", "AWS Lambda"],
    "inferred_technologies": ["Amazon S3", "Amazon RDS"],
    "context_clues": {
      "cloud_provider": "aws",
      "domain": "customer_service",
      "patterns": ["call_handling", "serverless"]
    }
  },
  "validation_results": {
    "compatibility_check": "passed",
    "ecosystem_consistency": "passed",
    "license_compatibility": "passed",
    "conflicts": []
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request format
- `422` - Validation errors
- `500` - Internal server error

#### Validate Technology Stack

**Endpoint:** `POST /tech-stack/validate`

**Description:** Validate a technology stack for compatibility and consistency.

**Request Body:**
```json
{
  "technologies": ["amazon-connect", "aws-lambda", "postgresql"],
  "context": {
    "domain": "customer_service",
    "ecosystem_preference": "aws",
    "constraints": ["hipaa_compliance"]
  }
}
```

**Response:**
```json
{
  "validation_result": {
    "overall_status": "warning",
    "compatibility_score": 0.85,
    "issues": [
      {
        "type": "ecosystem_inconsistency",
        "severity": "warning",
        "message": "PostgreSQL is not AWS-native, consider Amazon RDS",
        "affected_technologies": ["postgresql"],
        "suggestions": ["amazon-rds-postgresql"]
      }
    ],
    "recommendations": [
      {
        "action": "replace",
        "current": "postgresql",
        "suggested": "amazon-rds-postgresql",
        "reason": "Better AWS ecosystem integration"
      }
    ]
  }
}
```

### Technology Extraction

#### Extract Technologies from Text

**Endpoint:** `POST /extraction/technologies`

**Description:** Extract technology mentions from natural language text.

**Request Body:**
```json
{
  "text": "We need to build a REST API using FastAPI with PostgreSQL database and Redis for caching",
  "options": {
    "confidence_threshold": 0.7,
    "include_aliases": true,
    "resolve_abbreviations": true
  }
}
```

**Response:**
```json
{
  "extracted_technologies": [
    {
      "name": "FastAPI",
      "canonical_name": "FastAPI",
      "confidence": 0.95,
      "position": {"start": 35, "end": 42},
      "category": "web_framework",
      "aliases_matched": ["FastAPI"]
    },
    {
      "name": "PostgreSQL",
      "canonical_name": "PostgreSQL",
      "confidence": 0.98,
      "position": {"start": 48, "end": 58},
      "category": "database",
      "aliases_matched": ["PostgreSQL"]
    }
  ],
  "context_clues": {
    "patterns": ["rest_api", "web_service"],
    "domain_indicators": ["api_development"],
    "integration_hints": ["database_integration", "caching"]
  }
}
```

#### Extract Context from Requirements

**Endpoint:** `POST /extraction/context`

**Description:** Extract comprehensive context from structured requirements.

**Request Body:**
```json
{
  "requirements": {
    "description": "AWS-based microservices platform",
    "functional_requirements": ["API Gateway", "Lambda functions"],
    "constraints": {"cloud_provider": "aws"}
  }
}
```

**Response:**
```json
{
  "context": {
    "explicit_technologies": {
      "aws-api-gateway": 0.9,
      "aws-lambda": 0.95
    },
    "contextual_technologies": {
      "amazon-s3": 0.7,
      "amazon-rds": 0.6
    },
    "domain_context": {
      "primary": "microservices",
      "secondary": ["api_development", "serverless"]
    },
    "ecosystem_preference": "aws",
    "integration_requirements": ["api_gateway_lambda"],
    "priority_weights": {
      "explicit": 1.0,
      "contextual": 0.8,
      "pattern": 0.6
    }
  }
}
```

### Catalog Management

#### Search Technologies

**Endpoint:** `GET /catalog/search`

**Description:** Search for technologies in the catalog with fuzzy matching.

**Query Parameters:**
- `q` (required) - Search query
- `category` (optional) - Filter by category
- `ecosystem` (optional) - Filter by ecosystem
- `limit` (optional) - Maximum results (default: 20)

**Example:**
```bash
GET /catalog/search?q=connect&ecosystem=aws&limit=10
```

**Response:**
```json
{
  "results": [
    {
      "id": "amazon-connect",
      "name": "Amazon Connect",
      "category": "communication",
      "ecosystem": "aws",
      "description": "Cloud-based contact center service",
      "confidence": 0.95,
      "aliases": ["Connect", "AWS Connect"]
    }
  ],
  "total": 1,
  "query": "connect",
  "filters": {"ecosystem": "aws"}
}
```

#### Get Technology Details

**Endpoint:** `GET /catalog/technologies/{technology_id}`

**Description:** Get detailed information about a specific technology.

**Response:**
```json
{
  "technology": {
    "id": "amazon-connect",
    "name": "Amazon Connect",
    "category": "communication",
    "description": "Cloud-based contact center service",
    "aliases": ["Connect", "AWS Connect", "Amazon Connect Service"],
    "integrates_with": ["aws-lambda", "aws-s3", "salesforce-crm"],
    "alternatives": ["twilio-flex", "genesys-cloud"],
    "ecosystem": "aws",
    "maturity": "stable",
    "license": "proprietary",
    "metadata": {
      "use_cases": ["contact_center", "customer_service"],
      "deployment_types": ["cloud"],
      "pricing_model": "usage_based",
      "compliance": ["HIPAA", "PCI-DSS"]
    },
    "auto_generated": false,
    "pending_review": false,
    "confidence_score": 1.0
  }
}
```

#### Add Technology to Catalog

**Endpoint:** `POST /catalog/technologies`

**Description:** Add a new technology to the catalog.

**Request Body:**
```json
{
  "name": "New Technology",
  "category": "web_framework",
  "description": "A new web framework for building APIs",
  "aliases": ["NewTech", "NT"],
  "ecosystem": "open_source",
  "maturity": "beta",
  "license": "MIT",
  "integrates_with": ["postgresql", "redis"],
  "metadata": {
    "use_cases": ["api_development", "web_services"],
    "deployment_types": ["docker", "kubernetes"]
  }
}
```

**Response:**
```json
{
  "technology": {
    "id": "new-technology",
    "name": "New Technology",
    "category": "web_framework",
    "pending_review": true,
    "auto_generated": false,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "Technology added successfully and queued for review"
}
```

#### Update Technology

**Endpoint:** `PUT /catalog/technologies/{technology_id}`

**Description:** Update an existing technology in the catalog.

**Request Body:**
```json
{
  "description": "Updated description",
  "aliases": ["NewAlias1", "NewAlias2"],
  "integrates_with": ["new-integration"]
}
```

#### Delete Technology

**Endpoint:** `DELETE /catalog/technologies/{technology_id}`

**Description:** Remove a technology from the catalog.

**Response:**
```json
{
  "message": "Technology deleted successfully",
  "id": "technology-id"
}
```

### Validation and Compatibility

#### Check Technology Compatibility

**Endpoint:** `POST /validation/compatibility`

**Description:** Check compatibility between multiple technologies.

**Request Body:**
```json
{
  "technologies": ["fastapi", "postgresql", "redis"],
  "context": {
    "domain": "web_application",
    "constraints": ["docker_deployment"]
  }
}
```

**Response:**
```json
{
  "compatibility_result": {
    "overall_compatible": true,
    "compatibility_score": 0.92,
    "pairwise_compatibility": [
      {
        "tech_a": "fastapi",
        "tech_b": "postgresql",
        "compatible": true,
        "confidence": 0.95
      }
    ],
    "integration_suggestions": [
      {
        "technologies": ["fastapi", "postgresql"],
        "integration_method": "SQLAlchemy ORM",
        "confidence": 0.9
      }
    ]
  }
}
```

#### Validate Ecosystem Consistency

**Endpoint:** `POST /validation/ecosystem`

**Description:** Validate that technologies belong to consistent ecosystems.

**Request Body:**
```json
{
  "technologies": ["aws-lambda", "amazon-s3", "postgresql"],
  "preferred_ecosystem": "aws"
}
```

**Response:**
```json
{
  "ecosystem_validation": {
    "consistent": false,
    "primary_ecosystem": "aws",
    "inconsistent_technologies": [
      {
        "technology": "postgresql",
        "ecosystem": "open_source",
        "aws_alternative": "amazon-rds-postgresql"
      }
    ],
    "recommendations": [
      {
        "action": "replace",
        "technology": "postgresql",
        "with": "amazon-rds-postgresql",
        "reason": "AWS ecosystem consistency"
      }
    ]
  }
}
```

### Monitoring and Analytics

#### Get Generation Statistics

**Endpoint:** `GET /analytics/generation-stats`

**Description:** Get statistics about technology stack generation.

**Query Parameters:**
- `period` - Time period (7d, 30d, 90d)
- `ecosystem` - Filter by ecosystem

**Response:**
```json
{
  "statistics": {
    "total_generations": 1250,
    "average_confidence": 0.87,
    "explicit_inclusion_rate": 0.73,
    "ecosystem_distribution": {
      "aws": 45,
      "azure": 25,
      "gcp": 15,
      "open_source": 15
    },
    "most_requested_technologies": [
      {"name": "FastAPI", "count": 234},
      {"name": "PostgreSQL", "count": 198}
    ]
  },
  "period": "30d"
}
```

#### Get Catalog Health

**Endpoint:** `GET /analytics/catalog-health`

**Description:** Get catalog health and quality metrics.

**Response:**
```json
{
  "catalog_health": {
    "total_technologies": 847,
    "pending_review": 23,
    "auto_generated": 156,
    "completion_rate": 0.94,
    "integration_coverage": 0.78,
    "quality_score": 0.91,
    "issues": [
      {
        "type": "missing_integrations",
        "count": 45,
        "severity": "medium"
      }
    ]
  }
}
```

## Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request format",
    "details": {
      "field": "requirements.description",
      "issue": "Field is required"
    },
    "request_id": "req_abc123"
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Request validation failed | 400 |
| `TECHNOLOGY_NOT_FOUND` | Technology not in catalog | 404 |
| `EXTRACTION_FAILED` | Technology extraction failed | 422 |
| `LLM_ERROR` | LLM provider error | 503 |
| `CATALOG_ERROR` | Catalog operation failed | 500 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |

## Rate Limiting

**Limits:**
- General API: 100 requests/minute
- Generation endpoints: 10 requests/minute
- Catalog operations: 50 requests/minute

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## SDK and Client Libraries

### Python SDK

```python
from tech_stack_client import TechStackClient

client = TechStackClient(
    base_url="http://localhost:8000/api/v1",
    api_key="your-api-key"
)

# Generate tech stack
result = client.generate_tech_stack({
    "requirements": {
        "description": "Build a REST API with FastAPI"
    }
})

# Search catalog
technologies = client.search_catalog("fastapi")

# Validate compatibility
validation = client.validate_compatibility(["fastapi", "postgresql"])
```

### JavaScript SDK

```javascript
import { TechStackClient } from 'tech-stack-client';

const client = new TechStackClient({
  baseUrl: 'http://localhost:8000/api/v1',
  apiKey: 'your-api-key'
});

// Generate tech stack
const result = await client.generateTechStack({
  requirements: {
    description: 'Build a REST API with FastAPI'
  }
});

// Search catalog
const technologies = await client.searchCatalog('fastapi');
```

## Webhooks

### Technology Addition Webhook

**Endpoint:** `POST /webhooks/technology-added`

**Payload:**
```json
{
  "event": "technology.added",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "technology": {
      "id": "new-tech",
      "name": "New Technology",
      "pending_review": true
    }
  }
}
```

### Generation Completed Webhook

**Endpoint:** `POST /webhooks/generation-completed`

**Payload:**
```json
{
  "event": "generation.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "generation_id": "gen_abc123",
    "confidence": 0.92,
    "technology_count": 8
  }
}
```

## OpenAPI Specification

The complete OpenAPI specification is available at:
- **JSON:** `GET /api/v1/openapi.json`
- **YAML:** `GET /api/v1/openapi.yaml`
- **Interactive Docs:** `GET /docs`

## Testing and Development

### Test Endpoints

**Health Check:** `GET /health`
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "components": {
    "catalog": "healthy",
    "llm": "healthy",
    "extraction": "healthy"
  }
}
```

**API Version:** `GET /version`
```json
{
  "version": "2.0.0",
  "build": "abc123",
  "features": ["enhanced_extraction", "intelligent_catalog"]
}
```

### Development Configuration

```yaml
# config/development.yaml
api:
  debug: true
  cors_enabled: true
  rate_limiting: false
  
logging:
  level: DEBUG
  include_request_body: true
  include_response_body: true
```

For more examples and advanced usage, see the [API Examples](../examples/api_examples.md) documentation.