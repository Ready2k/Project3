# Project Structure & Organization

## Root Directory

```
├── app/                    # Main application package
├── data/                   # Pattern library and static data
├── exports/                # Generated export files
├── cache/                  # Diskcache storage
├── config.yaml            # Application configuration
├── requirements.txt        # Python dependencies
├── Makefile               # Build and development commands
├── pytest.ini            # Test configuration
├── docker-compose.yml     # Container orchestration
└── streamlit_app.py       # Streamlit UI entry point
```

## Application Structure (`app/`)

### Core Modules
- `api.py` - FastAPI application and endpoints
- `main.py` - Streamlit UI application
- `config.py` - Pydantic settings and configuration management

### Domain Packages
- `embeddings/` - Text embedding and FAISS indexing
- `exporters/` - Result export in JSON/Markdown/HTML formats
- `llm/` - LLM provider implementations and abstractions
- `pattern/` - Pattern loading, matching, and schema
- `qa/` - LLM-powered question generation with robust caching
- `services/` - Business logic, recommendations, and Jira integration
- `state/` - Session state management with multi-layer caching
- `utils/` - Utilities (logging, audit, PII redaction)
- `security/` - Input validation and security measures

### Testing Structure (`app/tests/`)
- `unit/` - Unit tests for individual components
- `integration/` - Integration tests across components
- `e2e/` - End-to-end workflow tests

## Data Organization (`data/`)

### Pattern Library (`data/patterns/`)
- JSON files with pattern definitions (PAT-001.json, etc.)
- Schema: pattern_id, name, description, feasibility, tech_stack
- Used for pattern matching and recommendations

## Configuration Files

### Application Config (`config.yaml`)
- Provider settings (OpenAI, Bedrock, Claude)
- Model configurations
- Timeouts and constraints
- Logging and audit settings

### Environment Variables (`.env`)
- API keys for LLM providers
- Jira integration credentials
- Configuration overrides

## Code Organization Patterns

### Async/Await
- All I/O operations use async/await
- FastAPI endpoints are async
- LLM provider calls are async

### Dependency Injection
- Services injected via FastAPI Depends()
- Global instances managed in api.py
- Clean separation of concerns

### Error Handling
- HTTPException for API errors
- Comprehensive logging with loguru
- PII redaction in logs and audit trails

### Testing Conventions
- Test files prefixed with `test_`
- Fixtures for common test setup
- Mocks for external dependencies
- 100% coverage requirement

## Import Conventions

```python
# Standard library first
import os
from pathlib import Path

# Third-party packages
import fastapi
import streamlit as st
from pydantic import BaseModel

# Local application imports
from app.config import Settings
from app.llm.base import LLMProvider
```

## File Naming Conventions

- **Snake case** for Python files: `pattern_matcher.py`
- **Kebab case** for config files: `docker-compose.yml`
- **UPPERCASE** for constants: `README.md`, `LICENSE`
- **Pattern IDs**: PAT-001, PAT-002 format