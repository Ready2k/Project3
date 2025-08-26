# Technology Stack & Build System

## Core Technologies

- **Python 3.10+**: Primary language
- **FastAPI**: Async REST API framework with robust caching and security middleware
- **Streamlit**: Interactive web UI framework with enhanced components and professional debug controls
- **Streamlit-Mermaid**: Native Mermaid diagram rendering with v10.2.4 compatibility
- **Pydantic**: Data validation, settings management, and security configuration
- **FAISS**: Vector similarity search (faiss-cpu)
- **Sentence Transformers**: Text embeddings
- **SQLAlchemy**: Database ORM with audit logging
- **Diskcache/Redis**: Session state management with multi-layer caching

## Enhanced System Components *(New in v2.7.0)*

- **Enhanced Pattern Management**: Advanced CRUD operations with bulk functionality, filtering, and analytics
- **Agentic Necessity Assessment**: Multi-dimensional scoring for autonomous agent evaluation
- **Dynamic Configuration Management**: Real-time system parameter adjustment with validation
- **Advanced Error Boundaries**: Comprehensive error handling with graceful degradation
- **Enhanced Security Validation**: Strengthened input sanitization and pattern validation

## Security Technologies

- **Advanced Prompt Defense**: Multi-layered security system with 8 specialized detectors
- **Input Validation**: Comprehensive sanitization and validation pipeline
- **Attack Pattern Detection**: Machine learning-based attack identification
- **Security Event Logging**: Structured logging with PII redaction
- **Performance Optimization**: Sub-100ms security validation with caching
- **Deployment Management**: Gradual rollout with automatic rollback capabilities

## LLM Providers

- **OpenAI**: GPT-4o, GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3 models via direct API
- **AWS Bedrock**: Claude models via AWS
- **Internal HTTP**: Custom provider support

## Development Tools

- **pytest**: Testing framework with asyncio support
- **black**: Code formatting
- **ruff**: Fast Python linter
- **mypy**: Static type checking
- **coverage**: Test coverage reporting

## Build System (Make)

### Development Commands

```bash
# Start both API and UI (recommended)
make dev
make up

# Start services individually
make api        # FastAPI only (port 8000)
make streamlit  # Streamlit UI only (port 8501)
make ui         # Same as streamlit
```

### Testing Commands

```bash
make test       # All tests with coverage
make e2e        # Integration tests only
make coverage   # Generate HTML coverage report
```

### Code Quality Commands

```bash
make fmt        # Format with black and ruff
make lint       # Lint with ruff and mypy
```

### Setup Commands

```bash
make install    # Install Python dependencies
make clean      # Clean cache and temp files
make help       # Show all available commands
```

## Technology Catalog System *(Enhanced in v2.7.0)*

- **Catalog File**: `data/technologies.json` - Centralized technology database
- **60+ Technologies**: Expanded catalog across 18+ categories including new Agentic AI category
- **Rich Metadata**: Name, description, category, tags, maturity, license, alternatives, integrations, use cases
- **Automatic Updates**: LLM-suggested technologies auto-added with smart categorization
- **Enhanced Management UI**: Complete CRUD interface with advanced filtering, bulk operations, and analytics
- **Performance**: 90% faster startup vs pattern file scanning
- **Backup Safety**: Automatic backups before any catalog modifications
- **New Categories**: Agentic AI & Multi-Agent Systems, Enhanced AI & ML, Infrastructure & DevOps

## Security Architecture

### Advanced Prompt Defense Components

- **`app/security/advanced_prompt_defender.py`**: Main security orchestrator
- **`app/security/overt_injection_detector.py`**: Direct prompt manipulation detection
- **`app/security/covert_injection_detector.py`**: Hidden attack detection (base64, markdown, zero-width)
- **`app/security/multilingual_attack_detector.py`**: Multi-language attack detection
- **`app/security/context_attack_detector.py`**: Buried instructions and lorem ipsum detection
- **`app/security/data_egress_detector.py`**: System prompt and environment variable protection
- **`app/security/business_logic_protector.py`**: Configuration access protection
- **`app/security/protocol_tampering_detector.py`**: JSON validation and format protection
- **`app/security/scope_validator.py`**: Business domain validation

### Security Infrastructure

- **`app/security/security_event_logger.py`**: Structured security event logging
- **`app/security/user_education.py`**: Contextual user guidance system
- **`app/security/performance_optimizer.py`**: Security performance optimization
- **`app/security/deployment_config.py`**: Gradual rollout and feature management
- **`app/security/rollback_manager.py`**: Automatic rollback capabilities
- **`app/security/attack_pack_manager.py`**: Attack pattern version management

### Technology Categories *(Expanded in v2.7.0)*

- **Agentic AI & Multi-Agent Systems**: LangChain, CrewAI, Microsoft Semantic Kernel, AutoGen, LangGraph
- **AI & Machine Learning**: OpenAI, Claude, HuggingFace, spaCy, Dialogflow, GPT-4o Reasoning, Azure Cognitive Services
- **Languages**: Python, Node.js, Java, TypeScript
- **Web Frameworks & APIs**: FastAPI, Django, Express, Spring
- **Databases & Storage**: PostgreSQL, MongoDB, Redis, ElasticSearch, SQLite, Neo4j
- **Cloud & Infrastructure**: AWS, Azure, GCP, Lambda, Functions
- **Communication & Integration**: Twilio, IMAP, AWS SES, Slack API, Jira API
- **Infrastructure & DevOps**: Docker, Kubernetes, GitHub Actions
- **Automation & Testing**: Selenium, Pega Workflow
- **Security**: OAuth2, Microsoft Presidio, OpenPGP
- **Data Processing & ORM**: SQLAlchemy, Pandas, NumPy
- **And 7 more specialized categories...

## Configuration

- **YAML Config**: `config.yaml` for application settings
- **Environment Variables**: `.env` file for API keys and overrides
- **Pydantic Settings**: Type-safe configuration management
- **Technology Catalog**: `data/technologies.json` for technology metadata

## Docker Support

```bash
docker-compose up  # Start all services with Redis
```

## Testing Strategy

- **100% Test Coverage**: TDD approach with deterministic fakes
- **Unit Tests**: `app/tests/unit/`
- **Integration Tests**: `app/tests/integration/`
- **E2E Tests**: `app/tests/e2e/`
- **Pytest Configuration**: `pytest.ini` with coverage requirements