# User Guide: Providing Technology Context in Requirements

## Overview

This guide helps users provide effective technology context in their requirements to ensure the Enhanced Technology Stack Generation system produces accurate and relevant technology recommendations.

## Best Practices for Technology Context

### 1. Be Explicit About Technology Preferences

**✅ Good Examples:**
```
"The system should integrate with Amazon Connect for call handling"
"Use AWS S3 for file storage and AWS Lambda for serverless functions"
"Implement the API using FastAPI with SQLAlchemy for database operations"
```

**❌ Avoid Vague References:**
```
"The system should handle calls" (unclear technology preference)
"Use cloud storage" (no specific provider mentioned)
"Build a REST API" (no framework preference)
```

### 2. Specify Cloud Ecosystem Preferences

**Preferred Approach:**
```
"This is an AWS-based solution requiring:
- Amazon Connect for contact center functionality
- AWS S3 for document storage
- AWS Lambda for event processing
- Amazon RDS for relational data"
```

**Why This Works:**
- Clearly indicates ecosystem preference (AWS)
- Provides specific service names
- Ensures consistent technology selection

### 3. Include Integration Requirements

**Effective Integration Context:**
```
"The system must integrate with:
- Existing Salesforce CRM via REST API
- Microsoft Active Directory for authentication
- Slack for notifications
- PostgreSQL database (existing infrastructure)"
```

**Benefits:**
- Identifies required integrations
- Influences technology selection for compatibility
- Prevents incompatible technology recommendations

### 4. Mention Existing Technology Constraints

**Constraint Examples:**
```
"Technology Constraints:
- Must use Python 3.10+ (existing team expertise)
- Cannot use GPL-licensed software (licensing policy)
- Must be compatible with Docker deployment
- Requires support for HIPAA compliance"
```

## Technology Context Patterns

### Cloud Provider Context

**AWS Context:**
```
"AWS-based microservices architecture requiring:
- API Gateway for request routing
- Lambda functions for business logic
- DynamoDB for session storage
- CloudWatch for monitoring"
```

**Azure Context:**
```
"Azure cloud solution with:
- Azure Functions for serverless compute
- Azure Cosmos DB for document storage
- Azure Service Bus for messaging
- Azure Monitor for observability"
```

**Google Cloud Context:**
```
"Google Cloud Platform implementation using:
- Cloud Functions for event processing
- Firestore for document database
- Pub/Sub for messaging
- Cloud Monitoring for metrics"
```

### Domain-Specific Context

**Financial Services:**
```
"Financial services application requiring:
- High-frequency trading capabilities
- Real-time risk calculation
- Regulatory compliance (SOX, PCI-DSS)
- Low-latency data processing"
```

**Healthcare:**
```
"Healthcare system with:
- HIPAA compliance requirements
- HL7 FHIR integration
- Electronic health record (EHR) connectivity
- Patient data encryption"
```

**E-commerce:**
```
"E-commerce platform featuring:
- Payment processing (Stripe, PayPal)
- Inventory management
- Order fulfillment automation
- Customer analytics"
```

### Integration Pattern Context

**API Integration:**
```
"RESTful API integration requiring:
- OpenAPI/Swagger documentation
- JWT authentication
- Rate limiting
- API versioning support"
```

**Event-Driven Architecture:**
```
"Event-driven system with:
- Message queuing (RabbitMQ/Apache Kafka)
- Event sourcing patterns
- CQRS implementation
- Eventual consistency handling"
```

**Microservices Architecture:**
```
"Microservices deployment requiring:
- Container orchestration (Kubernetes)
- Service mesh (Istio)
- Distributed tracing
- Circuit breaker patterns"
```

## Common Technology Aliases

The system recognizes various aliases and abbreviations. Here are common examples:

### AWS Services
- "Connect" → "Amazon Connect"
- "S3" → "Amazon S3"
- "Lambda" → "AWS Lambda"
- "RDS" → "Amazon RDS"
- "EC2" → "Amazon EC2"

### Development Frameworks
- "React" → "React.js"
- "Vue" → "Vue.js"
- "Express" → "Express.js"
- "Django" → "Django Framework"
- "Flask" → "Flask Framework"

### Databases
- "Postgres" → "PostgreSQL"
- "Mongo" → "MongoDB"
- "Redis" → "Redis Cache"
- "Elastic" → "Elasticsearch"

### DevOps Tools
- "Docker" → "Docker Container"
- "K8s" → "Kubernetes"
- "Jenkins" → "Jenkins CI/CD"
- "Terraform" → "Terraform IaC"

## Requirement Structure Examples

### Complete Requirement Example

```yaml
title: "Customer Service Automation Platform"

business_requirements:
  - "Automate customer inquiry routing and response"
  - "Integrate with existing CRM system"
  - "Provide real-time analytics dashboard"

technology_context:
  cloud_provider: "AWS"
  preferred_technologies:
    - "Amazon Connect"
    - "AWS Lambda"
    - "Amazon S3"
    - "Amazon RDS"
  
  integrations:
    - "Salesforce CRM (REST API)"
    - "Slack (Webhooks)"
    - "Microsoft Teams (Graph API)"
  
  constraints:
    - "Python 3.10+ required"
    - "Must support GDPR compliance"
    - "Docker deployment preferred"

functional_requirements:
  - "Route customer calls based on inquiry type"
  - "Generate automated responses using AI"
  - "Store conversation transcripts securely"
  - "Provide real-time agent dashboard"

non_functional_requirements:
  - "Handle 1000+ concurrent calls"
  - "99.9% uptime requirement"
  - "Sub-second response time"
  - "HIPAA compliance required"
```

### Minimal Effective Example

```
"Build a customer service chatbot using AWS services. 
The system should use Amazon Connect for call handling, 
AWS Lambda for processing, and integrate with our existing 
Salesforce CRM via REST API. The solution must be Python-based 
and deployable with Docker."
```

## Technology Context Validation

### High-Quality Context Indicators

✅ **Explicit Technology Names**: Specific service/framework names
✅ **Ecosystem Consistency**: All technologies from same cloud provider
✅ **Integration Details**: Specific integration methods mentioned
✅ **Constraint Clarity**: Clear technical and business constraints
✅ **Domain Context**: Industry-specific requirements included

### Context Quality Checklist

- [ ] Cloud provider preference specified
- [ ] Key technologies explicitly named
- [ ] Integration requirements detailed
- [ ] Technical constraints documented
- [ ] Domain/industry context provided
- [ ] Performance requirements specified
- [ ] Compliance requirements mentioned
- [ ] Existing infrastructure described

## Common Mistakes to Avoid

### 1. Generic Technology References
**❌ Avoid:** "Use a database"
**✅ Better:** "Use PostgreSQL for relational data storage"

### 2. Mixed Ecosystems Without Justification
**❌ Avoid:** "Use AWS Lambda with Azure Functions"
**✅ Better:** "Use AWS Lambda for compute (existing AWS infrastructure)"

### 3. Incomplete Integration Context
**❌ Avoid:** "Integrate with CRM"
**✅ Better:** "Integrate with Salesforce CRM using REST API and OAuth 2.0"

### 4. Missing Performance Context
**❌ Avoid:** "System should be fast"
**✅ Better:** "API response time under 200ms, support 10,000 concurrent users"

## Getting Help

### Technology Not Recognized?
1. Check the [Technology Catalog](../api/technology_catalog.md) for supported technologies
2. Use canonical names instead of abbreviations
3. Provide additional context about the technology
4. Contact support to add missing technologies

### Unexpected Technology Selections?
1. Review your technology context for clarity
2. Check for conflicting requirements
3. Verify ecosystem consistency
4. Review the [Troubleshooting Guide](tech_stack_troubleshooting.md)

### Need Technology Recommendations?
1. Describe your use case and domain
2. Specify any existing technology constraints
3. Mention integration requirements
4. Include performance and compliance needs

## Advanced Features

### Custom Technology Priorities
```yaml
technology_priorities:
  explicit_weight: 1.0      # Directly mentioned technologies
  contextual_weight: 0.8    # Inferred from context
  pattern_weight: 0.6       # Pattern-based suggestions
  generic_weight: 0.4       # Generic recommendations
```

### Ecosystem Migration Guidance
The system can suggest equivalent technologies when migrating between cloud providers:

```
"Current AWS solution using Lambda, S3, and RDS. 
Need Azure equivalent recommendations for migration."
```

### Technology Compatibility Validation
The system validates technology selections for:
- License compatibility
- Performance characteristics
- Integration capabilities
- Ecosystem consistency

For more advanced features, see the [Advanced Configuration Guide](tech_stack_advanced_config.md).