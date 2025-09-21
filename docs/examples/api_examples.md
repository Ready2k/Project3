# Technology Stack Generation API Examples

## Overview

This document provides practical examples for using the Enhanced Technology Stack Generation API. These examples demonstrate common use cases and best practices for integrating with the system.

## Basic Examples

### 1. Simple Technology Stack Generation

```python
import requests
import json

# Basic tech stack generation
def generate_basic_tech_stack():
    url = "http://localhost:8000/api/v1/tech-stack/generate"
    
    payload = {
        "requirements": {
            "title": "Simple Web API",
            "description": "Build a REST API using FastAPI with PostgreSQL database",
            "functional_requirements": [
                "Create user management endpoints",
                "Implement authentication",
                "Store data in relational database"
            ]
        },
        "options": {
            "include_reasoning": True,
            "confidence_threshold": 0.7
        }
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("Generated Tech Stack:")
        for tech in result['tech_stack']['technologies']:
            print(f"- {tech['name']} (confidence: {tech['confidence']})")
            if 'reasoning' in tech:
                print(f"  Reasoning: {tech['reasoning']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

generate_basic_tech_stack()
```

### 2. AWS Ecosystem Technology Stack

```python
def generate_aws_tech_stack():
    url = "http://localhost:8000/api/v1/tech-stack/generate"
    
    payload = {
        "requirements": {
            "title": "AWS Customer Service Platform",
            "description": "Build a customer service platform using Amazon Connect for call handling and AWS Lambda for processing",
            "functional_requirements": [
                "Handle incoming customer calls via Amazon Connect",
                "Process call data using AWS Lambda functions",
                "Store call transcripts in AWS S3",
                "Use Amazon RDS for customer data"
            ],
            "constraints": {
                "cloud_provider": "aws",
                "programming_language": "python",
                "compliance": ["HIPAA"]
            }
        },
        "options": {
            "include_reasoning": True,
            "ecosystem_preference": "aws",
            "max_technologies": 8
        }
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    print("AWS Tech Stack:")
    print(f"Ecosystem Consistency: {result['tech_stack']['metadata']['ecosystem_consistency']}")
    print(f"Total Confidence: {result['tech_stack']['metadata']['total_confidence']}")
    
    for tech in result['tech_stack']['technologies']:
        print(f"- {tech['name']} ({tech['category']})")
        print(f"  Priority: {tech['priority']}, Confidence: {tech['confidence']}")

generate_aws_tech_stack()
```

### 3. Technology Extraction from Text

```python
def extract_technologies_from_text():
    url = "http://localhost:8000/api/v1/extraction/technologies"
    
    payload = {
        "text": "We need to build a microservices architecture using Docker containers, deployed on Kubernetes, with a React frontend, FastAPI backend, and PostgreSQL database. The system should use Redis for caching and integrate with Stripe for payments.",
        "options": {
            "confidence_threshold": 0.7,
            "include_aliases": True,
            "resolve_abbreviations": True
        }
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    print("Extracted Technologies:")
    for tech in result['extracted_technologies']:
        print(f"- {tech['name']} ({tech['category']})")
        print(f"  Confidence: {tech['confidence']}")
        print(f"  Position: {tech['position']['start']}-{tech['position']['end']}")
    
    print("\nContext Clues:")
    for pattern in result['context_clues']['patterns']:
        print(f"- {pattern}")

extract_technologies_from_text()
```

## Advanced Examples

### 4. Multi-Cloud Technology Validation

```python
def validate_multi_cloud_stack():
    url = "http://localhost:8000/api/v1/tech-stack/validate"
    
    payload = {
        "technologies": [
            "aws-lambda",
            "azure-functions", 
            "google-cloud-functions",
            "postgresql"
        ],
        "context": {
            "domain": "serverless_computing",
            "constraints": ["multi_cloud_deployment"]
        }
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    print("Validation Results:")
    print(f"Overall Status: {result['validation_result']['overall_status']}")
    print(f"Compatibility Score: {result['validation_result']['compatibility_score']}")
    
    if result['validation_result']['issues']:
        print("\nIssues Found:")
        for issue in result['validation_result']['issues']:
            print(f"- {issue['type']}: {issue['message']}")
            print(f"  Severity: {issue['severity']}")
    
    if result['validation_result']['recommendations']:
        print("\nRecommendations:")
        for rec in result['validation_result']['recommendations']:
            print(f"- {rec['action']}: Replace {rec['current']} with {rec['suggested']}")
            print(f"  Reason: {rec['reason']}")

validate_multi_cloud_stack()
```

### 5. Catalog Search and Management

```python
def search_and_manage_catalog():
    base_url = "http://localhost:8000/api/v1"
    
    # Search for technologies
    search_url = f"{base_url}/catalog/search"
    search_params = {
        "q": "api framework",
        "category": "web_framework",
        "limit": 5
    }
    
    response = requests.get(search_url, params=search_params)
    search_results = response.json()
    
    print("Search Results:")
    for tech in search_results['results']:
        print(f"- {tech['name']} ({tech['category']})")
        print(f"  Confidence: {tech['confidence']}")
        print(f"  Ecosystem: {tech.get('ecosystem', 'N/A')}")
    
    # Get detailed information about a specific technology
    if search_results['results']:
        tech_id = search_results['results'][0]['id']
        detail_url = f"{base_url}/catalog/technologies/{tech_id}"
        
        response = requests.get(detail_url)
        tech_detail = response.json()
        
        print(f"\nDetailed Information for {tech_detail['technology']['name']}:")
        print(f"Description: {tech_detail['technology']['description']}")
        print(f"Aliases: {', '.join(tech_detail['technology']['aliases'])}")
        print(f"Integrates with: {', '.join(tech_detail['technology']['integrates_with'][:3])}...")

search_and_manage_catalog()
```

### 6. Batch Technology Stack Generation

```python
def batch_generate_tech_stacks():
    url = "http://localhost:8000/api/v1/tech-stack/generate"
    
    requirements_batch = [
        {
            "title": "E-commerce Platform",
            "description": "Build an e-commerce platform with React frontend and Node.js backend",
            "domain": "e_commerce"
        },
        {
            "title": "Data Analytics Pipeline", 
            "description": "Create a data pipeline using Apache Kafka and Apache Spark",
            "domain": "data_analytics"
        },
        {
            "title": "Mobile App Backend",
            "description": "Build a mobile app backend using Firebase and Google Cloud Functions",
            "domain": "mobile_backend"
        }
    ]
    
    results = []
    
    for req in requirements_batch:
        payload = {
            "requirements": req,
            "options": {
                "include_reasoning": False,
                "confidence_threshold": 0.6
            }
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            results.append({
                "title": req["title"],
                "tech_count": len(result['tech_stack']['technologies']),
                "confidence": result['tech_stack']['metadata']['total_confidence'],
                "ecosystem": result['tech_stack']['metadata'].get('ecosystem_consistency', 'mixed')
            })
    
    print("Batch Generation Results:")
    for result in results:
        print(f"- {result['title']}: {result['tech_count']} technologies")
        print(f"  Confidence: {result['confidence']:.2f}, Ecosystem: {result['ecosystem']}")

batch_generate_tech_stacks()
```

## Integration Examples

### 7. Integration with Pattern Creation Workflow

```python
class TechStackPatternIntegration:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
    
    def generate_pattern_with_tech_stack(self, requirements):
        # Step 1: Generate technology stack
        tech_stack = self._generate_tech_stack(requirements)
        
        # Step 2: Validate technology compatibility
        validation = self._validate_tech_stack(tech_stack['technologies'])
        
        # Step 3: Create pattern with validated tech stack
        pattern = self._create_pattern(requirements, tech_stack, validation)
        
        return pattern
    
    def _generate_tech_stack(self, requirements):
        url = f"{self.base_url}/tech-stack/generate"
        payload = {
            "requirements": requirements,
            "options": {
                "include_reasoning": True,
                "confidence_threshold": 0.7
            }
        }
        
        response = requests.post(url, json=payload)
        return response.json()['tech_stack']
    
    def _validate_tech_stack(self, technologies):
        url = f"{self.base_url}/tech-stack/validate"
        tech_ids = [tech['id'] for tech in technologies]
        
        payload = {
            "technologies": tech_ids,
            "context": {"validation_level": "comprehensive"}
        }
        
        response = requests.post(url, json=payload)
        return response.json()['validation_result']
    
    def _create_pattern(self, requirements, tech_stack, validation):
        # Integrate with existing pattern creation system
        pattern_data = {
            "title": requirements["title"],
            "description": requirements["description"],
            "technologies": tech_stack['technologies'],
            "confidence_score": tech_stack['metadata']['total_confidence'],
            "validation_status": validation['overall_status'],
            "ecosystem": tech_stack['metadata'].get('ecosystem_consistency')
        }
        
        return pattern_data

# Usage example
integration = TechStackPatternIntegration()
requirements = {
    "title": "AI-Powered Customer Service",
    "description": "Build an AI customer service system using OpenAI API and AWS services",
    "functional_requirements": [
        "Process customer inquiries using AI",
        "Integrate with existing CRM system",
        "Provide real-time chat support"
    ]
}

pattern = integration.generate_pattern_with_tech_stack(requirements)
print(f"Created pattern: {pattern['title']}")
print(f"Technologies: {len(pattern['technologies'])}")
print(f"Confidence: {pattern['confidence_score']:.2f}")
```

### 8. Real-time Technology Monitoring

```python
import asyncio
import websockets
import json

class TechStackMonitor:
    def __init__(self, websocket_url="ws://localhost:8000/ws/tech-stack"):
        self.websocket_url = websocket_url
    
    async def monitor_generations(self):
        async with websockets.connect(self.websocket_url) as websocket:
            print("Connected to tech stack generation monitor")
            
            async for message in websocket:
                data = json.loads(message)
                await self._handle_generation_event(data)
    
    async def _handle_generation_event(self, event):
        if event['type'] == 'generation_started':
            print(f"Generation started: {event['data']['title']}")
        
        elif event['type'] == 'technology_extracted':
            tech = event['data']['technology']
            print(f"Extracted: {tech['name']} (confidence: {tech['confidence']})")
        
        elif event['type'] == 'generation_completed':
            result = event['data']
            print(f"Generation completed: {result['tech_count']} technologies")
            print(f"Total confidence: {result['total_confidence']:.2f}")
        
        elif event['type'] == 'validation_warning':
            warning = event['data']
            print(f"Warning: {warning['message']}")

# Usage
async def main():
    monitor = TechStackMonitor()
    await monitor.monitor_generations()

# Run the monitor
# asyncio.run(main())
```

## Error Handling Examples

### 9. Robust Error Handling

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class TechStackClient:
    def __init__(self, base_url="http://localhost:8000/api/v1", api_key=None):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def generate_tech_stack(self, requirements, options=None):
        url = f"{self.base_url}/tech-stack/generate"
        payload = {
            "requirements": requirements,
            "options": options or {}
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            return {"error": "Request timed out", "retry": True}
        
        except requests.exceptions.HTTPError as e:
            if response.status_code == 400:
                error_detail = response.json().get('error', {})
                return {
                    "error": "Invalid request",
                    "details": error_detail.get('details', {}),
                    "retry": False
                }
            elif response.status_code == 422:
                return {
                    "error": "Validation failed",
                    "details": response.json().get('error', {}),
                    "retry": False
                }
            elif response.status_code == 429:
                return {
                    "error": "Rate limit exceeded",
                    "retry_after": response.headers.get('Retry-After', 60),
                    "retry": True
                }
            else:
                return {
                    "error": f"HTTP {response.status_code}",
                    "message": str(e),
                    "retry": True
                }
        
        except requests.exceptions.RequestException as e:
            return {
                "error": "Network error",
                "message": str(e),
                "retry": True
            }

# Usage with error handling
client = TechStackClient()

requirements = {
    "title": "Test Application",
    "description": "Build a test application with FastAPI"
}

result = client.generate_tech_stack(requirements)

if "error" in result:
    print(f"Error: {result['error']}")
    if result.get("retry"):
        print("This error can be retried")
    if "details" in result:
        print(f"Details: {result['details']}")
else:
    print("Success!")
    print(f"Generated {len(result['tech_stack']['technologies'])} technologies")
```

### 10. Async API Client

```python
import asyncio
import aiohttp
import json

class AsyncTechStackClient:
    def __init__(self, base_url="http://localhost:8000/api/v1", api_key=None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    async def generate_tech_stack(self, requirements, options=None):
        url = f"{self.base_url}/tech-stack/generate"
        payload = {
            "requirements": requirements,
            "options": options or {}
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url, 
                    json=payload, 
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        return {
                            "error": f"HTTP {response.status}",
                            "message": error_text
                        }
            except asyncio.TimeoutError:
                return {"error": "Request timed out"}
            except Exception as e:
                return {"error": str(e)}
    
    async def batch_generate(self, requirements_list):
        tasks = []
        for req in requirements_list:
            task = self.generate_tech_stack(req)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

# Usage
async def main():
    client = AsyncTechStackClient()
    
    requirements_list = [
        {"title": "Web App 1", "description": "React and Node.js app"},
        {"title": "Web App 2", "description": "Vue.js and Python app"},
        {"title": "Web App 3", "description": "Angular and Java app"}
    ]
    
    results = await client.batch_generate(requirements_list)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Request {i+1} failed: {result}")
        elif "error" in result:
            print(f"Request {i+1} error: {result['error']}")
        else:
            tech_count = len(result['tech_stack']['technologies'])
            print(f"Request {i+1} success: {tech_count} technologies")

# Run async example
# asyncio.run(main())
```

## Testing Examples

### 11. API Testing with pytest

```python
import pytest
import requests
from unittest.mock import patch

class TestTechStackAPI:
    BASE_URL = "http://localhost:8000/api/v1"
    
    def test_basic_generation(self):
        url = f"{self.BASE_URL}/tech-stack/generate"
        payload = {
            "requirements": {
                "title": "Test App",
                "description": "Simple FastAPI application"
            }
        }
        
        response = requests.post(url, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "tech_stack" in data
        assert "technologies" in data["tech_stack"]
        assert len(data["tech_stack"]["technologies"]) > 0
    
    def test_aws_ecosystem_consistency(self):
        url = f"{self.BASE_URL}/tech-stack/generate"
        payload = {
            "requirements": {
                "description": "AWS Lambda function with S3 storage"
            },
            "options": {
                "ecosystem_preference": "aws"
            }
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        assert response.status_code == 200
        assert data["tech_stack"]["metadata"]["ecosystem_consistency"] == "aws"
    
    def test_validation_endpoint(self):
        url = f"{self.BASE_URL}/tech-stack/validate"
        payload = {
            "technologies": ["fastapi", "postgresql"],
            "context": {"domain": "web_application"}
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        assert response.status_code == 200
        assert "validation_result" in data
        assert "overall_status" in data["validation_result"]
    
    def test_catalog_search(self):
        url = f"{self.BASE_URL}/catalog/search"
        params = {"q": "fastapi", "limit": 5}
        
        response = requests.get(url, params=params)
        data = response.json()
        
        assert response.status_code == 200
        assert "results" in data
        assert len(data["results"]) <= 5
    
    def test_error_handling(self):
        url = f"{self.BASE_URL}/tech-stack/generate"
        payload = {}  # Invalid payload
        
        response = requests.post(url, json=payload)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

# Run tests
# pytest test_tech_stack_api.py -v
```

These examples demonstrate the full range of capabilities available through the Enhanced Technology Stack Generation API. They cover basic usage, advanced features, error handling, and integration patterns that can be adapted for various use cases.