# Technology Stack & Build System

## Core Technologies

- **Python 3.10+**: Primary language
- **FastAPI**: Async REST API framework with robust caching
- **Streamlit**: Interactive web UI framework with enhanced components
- **Streamlit-Mermaid**: Native Mermaid diagram rendering
- **Pydantic**: Data validation and settings management
- **FAISS**: Vector similarity search (faiss-cpu)
- **Sentence Transformers**: Text embeddings
- **SQLAlchemy**: Database ORM
- **Diskcache/Redis**: Session state management with multi-layer caching

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

## Technology Catalog System

- **Catalog File**: `data/technologies.json` - Centralized technology database
- **55+ Technologies**: Comprehensive catalog across 17 categories
- **Rich Metadata**: Name, description, category, tags, maturity, license, alternatives, integrations
- **Automatic Updates**: LLM-suggested technologies auto-added with smart categorization
- **Management UI**: Complete CRUD interface in Streamlit "Technology Catalog" tab
- **Performance**: 90% faster startup vs pattern file scanning
- **Backup Safety**: Automatic backups before any catalog modifications

### Technology Categories

- **Languages**: Python, Node.js, Java
- **Frameworks**: FastAPI, Django, Express, Spring
- **Databases**: PostgreSQL, MongoDB, Redis, ElasticSearch
- **Cloud**: AWS, Azure, GCP, Lambda, Functions
- **AI/ML**: OpenAI, Claude, HuggingFace, spaCy, Dialogflow
- **Security**: OAuth2, Microsoft Presidio, OpenPGP
- **Integration**: REST API, Microsoft Graph, Salesforce API
- **Infrastructure**: Docker, Kubernetes
- **And 9 more specialized categories...

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