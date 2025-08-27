# API Integration Guide

Complete guide for integrating with the Automated AI Assessment (AAA) REST API.

## Base URL

```
http://localhost:8000  # Development
https://your-domain.com/api  # Production
```

## Authentication

Currently, the API uses API key authentication for LLM providers. No additional authentication is required for API access.

## Core Endpoints

### 1. Start Analysis

**POST** `/ingest`

Initiate a new analysis session.

```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "text",
    "payload": {
      "text": "I need to automate customer support ticket processing with AI analysis",
      "domain": "customer_support",
      "pattern_types": ["automation", "ai_processing"],
      "constraints": {
        "banned_tools": ["Azure"],
        "required_integrations": ["Salesforce", "Slack"],
        "compliance_requirements": ["GDPR", "SOX"],
        "data_sensitivity": "confidential"
      }
    }
  }'
```

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "created",
  "phase": "parsing",
  "message": "Analysis session created successfully"
}
```

### 2. Check Status

**GET** `/status/{session_id}`

Get current analysis status and progress.

```bash
curl "http://localhost:8000/status/123e4567-e89b-12d3-a456-426614174000"
```

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "phase": "qa_ready",
  "progress": 40,
  "status": "Questions generated, waiting for answers",
  "questions": [
    {
      "id": "volume_estimate",
      "question": "How many support tickets do you process daily?",
      "type": "text",
      "required": true
    }
  ],
  "requirements": {
    "description": "Customer support ticket processing automation",
    "domain": "customer_support"
  }
}
```

### 3. Submit Q&A Answers

**POST** `/qa/{session_id}`

Submit answers to clarifying questions.

```bash
curl -X POST "http://localhost:8000/qa/123e4567-e89b-12d3-a456-426614174000" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": {
      "volume_estimate": "500-1000 tickets daily",
      "complexity_level": "Medium - mix of simple and complex issues",
      "integration_requirements": "Must integrate with Salesforce and Slack"
    }
  }'
```

**Response:**
```json
{
  "status": "success",
  "phase": "matching",
  "message": "Answers submitted, proceeding with pattern matching"
}
```

### 4. Generate Recommendations

**POST** `/recommend`

Generate final recommendations and feasibility assessment.

```bash
curl -X POST "http://localhost:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "top_k": 3,
    "include_tech_stack": true,
    "include_diagrams": false
  }'
```

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "feasibility": "Fully Automatable",
  "confidence_score": 0.87,
  "assessment": {
    "key_insights": [
      "High volume processing suitable for automation",
      "Salesforce API provides robust integration capabilities"
    ],
    "challenges": [
      "Complex ticket categorization may require ML training",
      "Integration complexity with multiple systems"
    ],
    "recommended_approach": "Implement AI-powered ticket classification with automated routing",
    "next_steps": [
      "Design ticket classification model",
      "Plan Salesforce API integration",
      "Develop automated routing logic"
    ]
  },
  "pattern_matches": [
    {
      "pattern_id": "APAT-003",
      "name": "Autonomous Customer Support Resolution Agent",
      "relevance_score": 0.92,
      "autonomy_level": 0.97
    }
  ],
  "tech_stack": {
    "programming_languages": ["Python"],
    "frameworks": ["FastAPI", "Streamlit"],
    "databases": ["PostgreSQL", "Redis"],
    "ai_ml": ["OpenAI GPT-4", "scikit-learn"],
    "integrations": ["Salesforce API", "Slack API"]
  }
}
```

## Advanced Endpoints

### 5. Generate Diagrams

**POST** `/diagrams/{session_id}`

Generate architecture diagrams for the analysis.

```bash
curl -X POST "http://localhost:8000/diagrams/123e4567-e89b-12d3-a456-426614174000" \
  -H "Content-Type: application/json" \
  -d '{
    "diagram_type": "context",
    "format": "mermaid"
  }'
```

**Diagram Types:**
- `context` - System context diagram
- `container` - Container diagram
- `sequence` - Sequence diagram
- `c4` - C4 architecture diagram
- `infrastructure` - Infrastructure diagram
- `tech_stack_wiring` - Technical wiring diagram

### 6. Export Results

**GET** `/export/{session_id}`

Export analysis results in various formats.

```bash
# JSON export
curl "http://localhost:8000/export/123e4567-e89b-12d3-a456-426614174000?format=json"

# Markdown export
curl "http://localhost:8000/export/123e4567-e89b-12d3-a456-426614174000?format=markdown"

# HTML export
curl "http://localhost:8000/export/123e4567-e89b-12d3-a456-426614174000?format=html"
```

### 7. Pattern Management

**GET** `/patterns`

List available patterns.

```bash
curl "http://localhost:8000/patterns?pattern_type=agentic&domain=customer_support"
```

**GET** `/patterns/{pattern_id}`

Get specific pattern details.

```bash
curl "http://localhost:8000/patterns/APAT-003"
```

### 8. Technology Catalog

**GET** `/technologies`

List available technologies.

```bash
curl "http://localhost:8000/technologies?category=ai_ml&maturity=stable"
```

## Input Sources

### Text Input
```json
{
  "source": "text",
  "payload": {
    "text": "Your requirement description",
    "domain": "optional_domain",
    "pattern_types": ["optional", "pattern", "types"],
    "constraints": {
      "banned_tools": ["tool1", "tool2"],
      "required_integrations": ["system1", "system2"],
      "compliance_requirements": ["GDPR", "HIPAA"],
      "data_sensitivity": "confidential"
    }
  }
}
```

### File Upload
```json
{
  "source": "file",
  "payload": {
    "file_content": "base64_encoded_file_content",
    "file_name": "requirements.pdf",
    "file_type": "pdf"
  }
}
```

### Jira Integration
```json
{
  "source": "jira",
  "payload": {
    "ticket_key": "PROJ-123",
    "jira_config": {
      "base_url": "https://your-domain.atlassian.net",
      "email": "user@example.com",
      "api_token": "your_api_token"
    }
  }
}
```

## Error Handling

### Standard Error Response
```json
{
  "error": "error_type",
  "detail": "Detailed error message",
  "session_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Common Error Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | `validation_error` | Invalid request data |
| 404 | `session_not_found` | Session ID not found |
| 404 | `pattern_not_found` | Pattern ID not found |
| 422 | `processing_error` | Analysis processing failed |
| 429 | `rate_limit_exceeded` | Too many requests |
| 500 | `internal_error` | Internal server error |
| 503 | `llm_provider_error` | LLM provider unavailable |

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Analysis Requests**: 10 per minute per IP
- **Status Checks**: 60 per minute per IP
- **Export Requests**: 20 per minute per IP

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1640995200
```

## Webhooks (Future)

Webhook support for long-running analyses (planned feature):

```json
{
  "webhook_url": "https://your-app.com/webhook",
  "events": ["analysis_complete", "analysis_failed"]
}
```

## SDK Examples

### Python SDK Example

```python
import requests
import json
from typing import Dict, Any

class AAAClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def start_analysis(self, text: str, domain: str = None, 
                      constraints: Dict[str, Any] = None) -> str:
        """Start a new analysis and return session ID."""
        payload = {
            "source": "text",
            "payload": {
                "text": text,
                "domain": domain,
                "constraints": constraints or {}
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/ingest",
            json=payload
        )
        response.raise_for_status()
        
        return response.json()["session_id"]
    
    def get_status(self, session_id: str) -> Dict[str, Any]:
        """Get analysis status."""
        response = self.session.get(f"{self.base_url}/status/{session_id}")
        response.raise_for_status()
        return response.json()
    
    def submit_answers(self, session_id: str, 
                      answers: Dict[str, str]) -> Dict[str, Any]:
        """Submit Q&A answers."""
        response = self.session.post(
            f"{self.base_url}/qa/{session_id}",
            json={"answers": answers}
        )
        response.raise_for_status()
        return response.json()
    
    def get_recommendations(self, session_id: str, 
                           top_k: int = 3) -> Dict[str, Any]:
        """Get final recommendations."""
        payload = {
            "session_id": session_id,
            "top_k": top_k,
            "include_tech_stack": True
        }
        
        response = self.session.post(
            f"{self.base_url}/recommend",
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = AAAClient()

# Start analysis
session_id = client.start_analysis(
    text="Automate customer support with AI",
    domain="customer_support",
    constraints={
        "banned_tools": ["Azure"],
        "compliance_requirements": ["GDPR"]
    }
)

# Check status and answer questions
status = client.get_status(session_id)
if status["phase"] == "qa_ready":
    answers = {
        "volume_estimate": "1000 tickets daily",
        "complexity_level": "Medium complexity"
    }
    client.submit_answers(session_id, answers)

# Get recommendations
recommendations = client.get_recommendations(session_id)
print(f"Feasibility: {recommendations['feasibility']}")
print(f"Confidence: {recommendations['confidence_score']}")
```

### JavaScript SDK Example

```javascript
class AAAClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async startAnalysis(text, domain = null, constraints = {}) {
        const payload = {
            source: 'text',
            payload: {
                text,
                domain,
                constraints
            }
        };
        
        const response = await fetch(`${this.baseUrl}/ingest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.session_id;
    }
    
    async getStatus(sessionId) {
        const response = await fetch(`${this.baseUrl}/status/${sessionId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async submitAnswers(sessionId, answers) {
        const response = await fetch(`${this.baseUrl}/qa/${sessionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ answers })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async getRecommendations(sessionId, topK = 3) {
        const payload = {
            session_id: sessionId,
            top_k: topK,
            include_tech_stack: true
        };
        
        const response = await fetch(`${this.baseUrl}/recommend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
}

// Usage example
const client = new AAAClient();

async function analyzeRequirement() {
    try {
        // Start analysis
        const sessionId = await client.startAnalysis(
            'Automate customer support with AI',
            'customer_support',
            {
                banned_tools: ['Azure'],
                compliance_requirements: ['GDPR']
            }
        );
        
        // Check status and answer questions
        const status = await client.getStatus(sessionId);
        if (status.phase === 'qa_ready') {
            await client.submitAnswers(sessionId, {
                volume_estimate: '1000 tickets daily',
                complexity_level: 'Medium complexity'
            });
        }
        
        // Get recommendations
        const recommendations = await client.getRecommendations(sessionId);
        console.log(`Feasibility: ${recommendations.feasibility}`);
        console.log(`Confidence: ${recommendations.confidence_score}`);
        
    } catch (error) {
        console.error('Analysis failed:', error);
    }
}
```

## Best Practices

### 1. Session Management
- Store session IDs for later reference
- Implement proper error handling for session expiration
- Use status endpoint to track progress

### 2. Rate Limiting
- Implement exponential backoff for rate limit errors
- Cache responses when appropriate
- Use batch operations when available

### 3. Error Handling
- Always check response status codes
- Implement retry logic for transient errors
- Log errors for debugging and monitoring

### 4. Security
- Use HTTPS in production
- Validate all input data
- Implement proper authentication for production use

### 5. Performance
- Use async/await for non-blocking operations
- Implement connection pooling for high-volume usage
- Cache frequently accessed data (patterns, technologies)

## OpenAPI Specification

The complete OpenAPI specification is available at:
```
http://localhost:8000/docs
```

This provides interactive API documentation with request/response examples and the ability to test endpoints directly.