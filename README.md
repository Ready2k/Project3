# Automated AI Assessment (AAA)

Interactive GUI + API system that judges if user stories/requirements are automatable with agentic AI. The system asks clarifying questions, matches requirements to reusable solution patterns, and exports results with feasibility assessments.

## Features

- 🤖 **Multi-Provider LLM Support**: OpenAI, Anthropic/Bedrock, Claude Direct, Internal HTTP, FakeLLM for testing
- 🔍 **Intelligent Pattern Matching**: Tag filtering + vector similarity with FAISS
- ❓ **AI-Generated Q&A System**: LLM creates contextual clarifying questions based on your specific requirement
- 📊 **Feasibility Assessment**: Automatable, Partially Automatable, or Not Automatable with confidence scores
- 🛠️ **LLM-Driven Tech Stack Generation**: Intelligent technology recommendations based on requirements, constraints, and available patterns
- 🏗️ **AI-Generated Architecture Explanations**: LLM explains how technology components work together for your specific use case
- 📈 **AI-Generated Architecture Diagrams**: Context, Container, and Sequence diagrams using Mermaid *(WIP - diagrams functionality is still being refined)*
- 📤 **Export Results**: JSON and Markdown formats with comprehensive analysis
- 🎯 **Constraint-Aware**: Filters banned tools and applies business constraints
- 🔍 **LLM Message Audit Trail**: Complete visibility into LLM prompts and responses for transparency
- 🧪 **100% Test Coverage**: TDD approach with deterministic fakes
- 🐳 **Docker Ready**: Complete containerization with docker-compose
- 🔄 **Real-time Progress Tracking**: Live status updates during analysis phases

## Quick Start

### Prerequisites

- Python 3.10+
- pip or uv package manager

### Installation

```bash
# Clone and enter directory
cd agentic_or_not

# Install dependencies
make install
# or
python3 -m pip install -r requirements.txt
```

### Running the Application

#### Option 1: Using Make (Recommended)

```bash
# Start both API and UI (opens browser automatically)
make dev
# or
make up

# Or start services individually:
make api        # FastAPI only
make streamlit  # Streamlit UI only (opens browser)
```

This starts:
- FastAPI server at http://localhost:8000
- Streamlit UI at http://localhost:8501 (opens automatically in browser)

#### Option 2: Manual Start

```bash
# Terminal 1: Start API server
make api
# or
python3 -m uvicorn app.api:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Streamlit UI
make streamlit
# or
make ui
# or
python3 run_streamlit.py
```

#### Option 3: Docker Compose

```bash
# Start all services with Redis (production-like)
make docker-up
# or
docker-compose up -d

# Development with live reloading
make docker-dev
# or
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production deployment
make docker-prod
# or
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Usage

### 1. Web Interface (Streamlit)

1. **Configure Provider** (Sidebar):
   - Select LLM provider: OpenAI, Bedrock, Claude, Internal, or FakeLLM
   - Enter API key and select model
   - Test connection to verify setup

2. **Submit Requirements** (Analysis Tab):
   - Choose input method: Text, File Upload, or Jira
   - Enter your automation requirement description
   - Optionally specify domain and pattern types
   - Click "🚀 Analyze Requirements"

3. **Answer AI Questions** (Automatic):
   - System generates personalized questions using AI
   - Questions focus on physical vs digital, data sources, complexity
   - Answer questions and click "🚀 Submit Answers"
   - System progresses through: Parsing → Validating → Q&A → Matching → Recommending → Done

4. **View Results** (Analysis Tab):
   - See feasibility assessment with confidence scores
   - Review detailed reasoning and tech stack recommendations
   - Export results in JSON or Markdown format

5. **Generate Diagrams** (Diagrams Tab): *(WIP - functionality being refined)*
   - Create AI-generated architecture diagrams
   - Context Diagram: System boundaries and external integrations
   - Container Diagram: Internal components and data flow
   - Sequence Diagram: Step-by-step process flow with decision points

6. **Monitor Performance** (Observability Tab):
   - View API call statistics and response times
   - Track provider usage and performance metrics

### 2. API Usage

#### Start Analysis
```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "text",
    "payload": {
      "text": "I need to automate web scraping for data collection",
      "domain": "data_processing"
    }
  }'
```

#### Check Status
```bash
curl "http://localhost:8000/status/{session_id}"
```

#### Answer Questions
```bash
curl -X POST "http://localhost:8000/qa/{session_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": {
      "frequency": "daily",
      "data_sensitivity": "medium"
    }
  }'
```

#### Get Recommendations
```bash
curl -X POST "http://localhost:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "{session_id}",
    "top_k": 3
  }'
```

## Intelligent Tech Stack Generation

The system uses LLM-driven analysis to generate contextual, justified technology recommendations instead of generic rule-based suggestions.

### How It Works

1. **Context Analysis**: LLM analyzes your specific requirements, domain, volume, compliance needs, and constraints
2. **Pattern-Aware**: Considers technologies from similar successful patterns as starting points
3. **Constraint-Aware**: Respects banned tools and required integrations from your organization
4. **Intelligent Selection**: LLM selects technologies that directly address your needs with reasoning

### Example

**Input Requirements:**
```json
{
  "description": "Automate customer support ticket processing with AI analysis",
  "domain": "customer_support",
  "volume": {"daily": 1000},
  "integrations": ["database", "email", "slack"],
  "compliance": ["GDPR"]
}
```

**LLM-Generated Tech Stack:**
- **Python**: Core language for automation and AI integration
- **FastAPI**: High-performance API endpoints for ticket ingestion
- **SQLAlchemy**: Database operations for ticket and customer data
- **Redis**: Caching and message broker for asynchronous processing
- **Docker**: Consistent deployment across environments
- **Prometheus**: System monitoring for 1000+ daily tickets

**Architecture Explanation (LLM-Generated):**
> "This customer support automation system uses a modern Python-based architecture designed for scalability and reliability. The core is built around FastAPI, which provides high-performance API endpoints for ticket ingestion and processing. SQLAlchemy handles database operations, ensuring reliable storage and retrieval of ticket data, customer information, and processing history. Redis serves as both a caching layer for frequently accessed data and a message broker for asynchronous task processing..."

### LLM Message Transparency

All tech stack generation prompts and responses are logged and visible in the **Observability Tab > LLM Messages**:

- **Full Prompts**: See exactly what context was provided to the LLM
- **Structured Responses**: View the LLM's reasoning and technology choices
- **Purpose Filtering**: Filter messages by "tech_stack_generation" or "architecture_explanation"
- **Audit Trail**: Complete transparency into AI decision-making

### Benefits Over Rule-Based Systems

- **Contextual**: Technologies chosen based on actual requirements, not generic rules
- **Justified**: LLM provides reasoning for each technology choice
- **Adaptive**: Learns from patterns while adapting to new requirements
- **Transparent**: Full visibility into the decision-making process

## Configuration

### Environment Variables

Create a `.env` file (see `.env.example`):

```bash
# LLM Provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Jira Integration (optional)
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=...

# Configuration Overrides
PROVIDER=openai
MODEL=gpt-4o
LOGGING_LEVEL=INFO
```

### YAML Configuration

Edit `config.yaml` for advanced settings:

```yaml
provider: openai
model: gpt-4o
pattern_library_path: ./data/patterns
export_path: ./exports
constraints:
  unavailable_tools: []
timeouts:
  llm: 20
  http: 10
logging:
  level: INFO
  redact_pii: true
bedrock:
  region: eu-west-2
```

## Development

### Available Make Commands

For a complete list of available commands, run:

```bash
make help
```

Key commands:
- `make dev` - Start both API and Streamlit UI (recommended for development)
- `make streamlit` - Start Streamlit UI only (opens browser automatically)
- `make api` - Start FastAPI backend only
- `make test` - Run all tests with coverage
- `make fmt` - Format code
- `make lint` - Lint code
- `make install` - Install dependencies
- `make clean` - Clean cache files

### Running Tests

```bash
# All tests with coverage
make test

# Unit tests only
python3 -m pytest app/tests/unit/ -v

# Integration tests
python3 -m pytest app/tests/integration/ -v

# Specific test
python3 -m pytest app/tests/unit/test_config.py -v
```

### Code Quality

```bash
# Format code
make fmt

# Lint code
make lint

# Type checking
mypy app/ --ignore-missing-imports
```

### Adding New Patterns

1. Create a new JSON file in `data/patterns/`:

```json
{
  "pattern_id": "PAT-004",
  "name": "Email Automation",
  "description": "Automated email processing and response system",
  "feasibility": "Automatable",
  "pattern_type": ["email_automation", "workflow_automation"],
  "input_requirements": ["email_templates", "trigger_conditions"],
  "tech_stack": ["Python", "SMTP", "IMAP"],
  "confidence_score": 0.85,
  "domain": "communication",
  "complexity": "Medium"
}
```

2. Restart the application to load new patterns

## Architecture

### Components

- **FastAPI Backend**: REST API with async endpoints
- **Streamlit Frontend**: Interactive web interface
- **Pattern Library**: JSON-based reusable solution patterns
- **FAISS Index**: Vector similarity search for pattern matching
- **Q&A System**: Template-based question generation
- **Tech Stack Generator**: LLM-driven intelligent technology recommendations
- **Architecture Explainer**: LLM-generated explanations of how components work together
- **State Management**: Session persistence with diskcache/Redis
- **Export System**: JSON and Markdown result export
- **Audit System**: Complete LLM message logging and observability

### Request Flow

1. **Ingest** → Create session, parse requirements
2. **Q&A Loop** → Collect missing information
3. **Pattern Matching** → Tag filtering + vector similarity
4. **Recommendations** → Generate feasibility assessment
5. **Export** → Download results in preferred format

## API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Sample Patterns

The system includes 3 sample patterns:

1. **PAT-001**: Web Scraping Automation
2. **PAT-002**: API Integration Workflow  
3. **PAT-003**: Document Processing Pipeline

## Deployment

For detailed deployment instructions including production setups, Docker configurations, and cloud deployments, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Quick Docker Start

```bash
# Build and start with Docker
make docker-build
make docker-up

# Or for development
make docker-dev
```

## Monitoring

### Health Checks

```bash
# Check all services
python3 scripts/health_check.py

# JSON output
python3 scripts/health_check.py --json

# Continuous monitoring
./scripts/monitor.sh 30  # Check every 30 seconds
```

## Troubleshooting

### 🔧 LLM Provider Issues

If you're getting "❌ Connection failed" when testing providers:

1. **Check Model Name**: Use `gpt-4o` (not `gpt-5` or `gpt4-o`)
2. **Verify API Key**: Ensure it starts with `sk-` and is valid
3. **Enable Debug Mode**: Check the debug checkbox in Streamlit sidebar
4. **Test Directly**: Run `python3 test_provider.py YOUR_API_KEY`

### 📋 Common Issues

1. **Import Errors**: Ensure `PYTHONPATH` includes the project root
2. **Port Conflicts**: Change ports in docker-compose.yml or Makefile  
3. **Missing Dependencies**: Run `make install` or `pip install -r requirements.txt`
4. **FAISS Issues**: Install `faiss-cpu` for CPU-only environments

### 📖 Detailed Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for comprehensive debugging guide including:
- Detailed error solutions
- Debug mode usage
- Test scripts and commands
- Performance optimization tips

### 📝 Logs

- API logs: Check console output from uvicorn
- Streamlit logs: Check browser console and terminal
- Application logs: Configured via `config.yaml` logging section

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure 100% test coverage: `make test`
5. Format and lint code: `make fmt && make lint`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

---

**Automated AI Assessment (AAA)** - Assess automation feasibility with AI-powered pattern matching.