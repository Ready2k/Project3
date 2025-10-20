# Automated AI Assessment (AAA)

Interactive GUI + API system that evaluates user stories/requirements for **autonomous agentic AI** implementation. The system uses advanced AI reasoning to assess autonomy potential, matches requirements to specialized agentic solution patterns, and provides comprehensive feasibility assessments with detailed implementation guidance.

## 📚 Documentation

- **[Complete User Guide](docs/guides/USER_GUIDE.md)** - Comprehensive usage guide
- **[Development Guide](docs/development/DEVELOPMENT.md)** - Developer setup and guidelines  
- **[Architecture Overview](docs/architecture/ARCHITECTURE.md)** - System design and components
- **[API Integration Guide](docs/guides/INTEGRATION_GUIDE.md)** - API usage and examples
- **[Deployment Guide](docs/deployment/DEPLOYMENT.md)** - Production deployment
- **[Security Guide](docs/architecture/SECURITY_REVIEW.md)** - Security features and best practices

## ✨ Key Features

### 🤖 **Agentic AI Assessment**
- **Autonomous Agent Evaluation**: Multi-dimensional scoring with 90%+ accuracy
- **Agentic Pattern Library**: 5 specialized APAT patterns (95-98% autonomy levels)
- **Multi-Agent System Design**: Hierarchical, collaborative, and swarm architectures
- **Exception Handling Through Reasoning**: AI agents resolve problems autonomously

### 🔍 **Intelligent Analysis**
- **Multi-Provider LLM Support**: OpenAI (GPT-4, GPT-5, o1), Anthropic, Bedrock, Claude, Internal HTTP
- **GPT-5 Full Support**: Automatic parameter conversion, enhanced error handling, intelligent retry logic
- **Smart Pattern Matching**: Tag filtering + FAISS vector similarity search
- **AI-Generated Q&A**: Contextual clarifying questions based on requirements
- **Comprehensive Feasibility Assessment**: Detailed insights with confidence scoring

### 📊 **Visualization & Documentation**
- **AI-Generated Diagrams**: Context, Container, Sequence, C4, Infrastructure, Tech Stack Wiring
- **Mermaid Diagram Rendering**: Real-time diagram visualization with streamlit-mermaid integration
- **Infrastructure Diagrams**: AWS/GCP/Azure architecture diagrams with 50+ component types
- **Draw.io Export**: Professional diagram customization and team collaboration
- **Technology Catalog**: 60+ technologies across 18+ categories with rich metadata
- **Pattern Analytics**: Real-time usage metrics and performance tracking
- **AI-Powered Pattern Enhancement**: Intelligent pattern improvement with LLM-driven insights

### 🛡️ **Enterprise Security**
- **Advanced Prompt Defense**: 8 specialized detectors for comprehensive threat protection
- **Multi-language Security**: Attack detection in 6 languages
- **Enterprise Constraints**: Technology restrictions, compliance requirements, integration constraints
- **Complete Audit Trail**: Full LLM interaction logging and security event tracking

### 🚀 **Session & Export Management**
- **Session Continuity**: Resume previous analyses with UUID-based session management
- **Multi-format Export**: JSON, Markdown, and interactive HTML with comprehensive analysis
- **Real-time Progress**: Live status updates during analysis phases
- **Cross-platform Compatibility**: Web UI + REST API with Docker deployment

### 🤖 **AI-Powered Pattern Enhancement**
- **Intelligent Pattern Improvement**: Use AI to enhance existing patterns with better descriptions, tech stacks, and implementation guidance
- **Multi-Dimensional Enhancement**: Improve descriptions, suggest modern technologies, add implementation steps, identify challenges, and provide insights
- **Before/After Comparison**: Visual comparison showing exactly what was enhanced
- **Custom Enhancement Instructions**: Tell the AI what to focus on (cloud-native, security, enterprise, etc.)
- **Enhancement History Tracking**: Track all AI improvements with reasoning and timestamps
- **Seamless Integration**: Built into the Pattern Library with intuitive sub-tab organization

## 🤖 Agentic AI Transformation

The system evaluates requirements for **autonomous agentic AI** implementation, prioritizing agent-based solutions over traditional automation.

### Key Capabilities

- **Autonomous Agent Assessment**: Multi-dimensional analysis across reasoning complexity, decision boundaries, and workflow automation
- **Agentic Pattern Library**: 5 specialized APAT patterns with 95-98% autonomy levels
- **Multi-Agent System Design**: Hierarchical, collaborative, and swarm intelligence architectures
- **Exception Handling Through Reasoning**: AI agents resolve problems autonomously using multiple reasoning approaches

### Sample Assessment Output

```
🟢 Feasibility: Fully Automatable
Confidence Level: 87%

🔍 Key Insights:
• High-volume processing suitable for AI automation
• Salesforce API provides robust integration capabilities

🎯 Recommended Approach:
Implement autonomous customer support agent with AI-powered 
ticket classification and automated response generation.

📋 Next Steps:
• Design ticket classification model
• Plan Salesforce API integration  
• Develop automated routing logic
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- LLM provider API key (OpenAI with GPT-5 support, Anthropic, or AWS Bedrock)

### Installation & Setup

```bash
# Clone and install
git clone <repository-url>
cd agentic_or_not
make install

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start the system
make dev
```

This starts:
- FastAPI server at http://localhost:8000
- Streamlit UI at http://localhost:8500 (opens automatically)

### Docker Deployment

```bash
# Production deployment
docker-compose up -d

# Development with live reloading  
make docker-dev
```

## 💡 Usage

### Web Interface
1. **Configure Provider**: Select LLM provider and enter API key
2. **Submit Requirements**: Enter automation requirement or resume previous session
3. **Answer AI Questions**: Respond to contextual clarifying questions
4. **View Results**: Review feasibility assessment and recommendations
5. **Generate Diagrams**: Create architecture diagrams with Draw.io export
6. **Export Results**: Download in JSON, Markdown, or HTML formats

### API Integration
```bash
# Start analysis
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"source": "text", "payload": {"text": "Automate customer support"}}'

# Check status
curl "http://localhost:8000/status/{session_id}"

# Get recommendations  
curl -X POST "http://localhost:8000/recommend" \
  -d '{"session_id": "{session_id}", "top_k": 3}'
```

See **[Complete API Guide](docs/guides/API_GUIDE.md)** for detailed integration examples.

## 🧠 Intelligent Tech Stack Generation

The system uses LLM-driven analysis to generate contextual technology recommendations:

- **Context-Aware**: Analyzes specific requirements, domain, volume, and constraints
- **Pattern-Informed**: Considers technologies from similar successful implementations  
- **Constraint-Compliant**: Respects banned tools and required integrations
- **Fully Transparent**: Complete audit trail of LLM reasoning and decisions

**Example Output:**
- **Python + FastAPI**: High-performance API for ticket processing
- **SQLAlchemy + Redis**: Database operations with caching layer
- **Docker + Prometheus**: Containerized deployment with monitoring

See **[User Guide](docs/guides/USER_GUIDE.md)** for detailed examples and explanations.

## 📊 Architecture Diagrams

The system generates multiple diagram types using AI:

- **Context Diagrams**: System boundaries and external integrations
- **Container Diagrams**: Internal components and data flow  
- **Sequence Diagrams**: Step-by-step process flows
- **C4 Architecture**: Standardized C4 model diagrams
- **Infrastructure Diagrams**: Cloud architecture with vendor icons
- **Tech Stack Wiring**: Technical component connections

All diagrams support:
- **Enhanced Viewing**: Full-size browser view with zoom/pan
- **Draw.io Export**: Professional editing and customization
- **Multiple Formats**: SVG, PNG, PDF export options

See **[User Guide](docs/guides/USER_GUIDE.md)** for detailed diagram examples.

## 🏢 Enterprise Constraints

The system supports comprehensive enterprise technology constraints:

- **Banned Technologies**: Specify tools that cannot be used
- **Required Integrations**: Must work with existing systems  
- **Compliance Requirements**: GDPR, HIPAA, SOX, PCI-DSS, etc.
- **Data Sensitivity**: Public, Internal, Confidential, Restricted
- **Deployment Preferences**: Cloud-only, On-premises, Hybrid

Constraints are automatically applied to:
- LLM context for intelligent recommendations
- Technology filtering and pattern selection
- Final assessment and implementation guidance

## ⚙️ Configuration

### Environment Variables
```bash
# Create .env file (see .env.example)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Optional Jira integration
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=...
```

### YAML Configuration
```yaml
# config.yaml
provider: openai
model: gpt-4o
pattern_library_path: ./data/patterns
export_path: ./exports
timeouts:
  llm: 20
  http: 10
```

See **[Deployment Guide](docs/deployment/DEPLOYMENT.md)** for complete configuration options.

## 🛠️ Development

### Quick Commands
```bash
make dev          # Start both API and UI
make test         # Run all tests with coverage
make fmt          # Format code
make lint         # Lint code
make clean        # Clean cache files
```

### Testing
```bash
make test                              # All tests
pytest app/tests/unit/ -v             # Unit tests
pytest app/tests/integration/ -v      # Integration tests
```

See **[Development Guide](docs/development/DEVELOPMENT.md)** for complete setup, testing, and contribution guidelines.

## 🏗️ Architecture

### Core Components
- **FastAPI Backend**: Async REST API with security middleware
- **Streamlit Frontend**: Interactive web interface  
- **Pattern Library**: JSON-based solution patterns with analytics
- **Technology Catalog**: 60+ technologies across 18+ categories
- **FAISS Index**: Vector similarity search for pattern matching
- **Security System**: Multi-layered prompt defense with 8 detectors
- **Export System**: JSON, Markdown, and HTML export capabilities

### Request Flow
1. **Ingest** → Parse requirements and create session
2. **Q&A** → Collect clarifying information  
3. **Match** → Find relevant patterns using AI
4. **Recommend** → Generate feasibility assessment
5. **Export** → Download results in multiple formats

See **[Architecture Guide](docs/architecture/ARCHITECTURE.md)** for detailed system design.

## 📖 Additional Resources

- **[Complete User Guide](docs/guides/USER_GUIDE.md)** - Comprehensive usage instructions
- **[API Integration Guide](docs/guides/API_GUIDE.md)** - REST API documentation and examples
- **[Development Guide](docs/development/DEVELOPMENT.md)** - Setup and contribution guidelines
- **[Architecture Overview](docs/architecture/ARCHITECTURE.md)** - System design and components
- **[Deployment Guide](docs/deployment/DEPLOYMENT.md)** - Production deployment instructions
- **[Security Guide](docs/architecture/SECURITY_REVIEW.md)** - Security features and best practices

## 🔗 API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Automated AI Assessment (AAA)** - Evaluate requirements for autonomous agentic AI implementation with comprehensive feasibility assessment and implementation guidance.