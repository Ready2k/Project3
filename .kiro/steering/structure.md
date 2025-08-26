# Project Structure & Organization

## Root Directory

```
├── app/                    # Main application package
├── data/                   # Pattern library and technology catalog
├── exports/                # Generated export files
├── cache/                  # Diskcache storage
├── scripts/                # Utility scripts (cleanup, maintenance)
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

### Domain Packages *(Enhanced in v2.7.0)*
- `config/` - Enhanced configuration management with system configuration and environment handling
- `core/` - Core system components including dependency injection
- `diagrams/` - Dynamic component mapping and infrastructure diagram generation
- `embeddings/` - Text embedding and FAISS indexing with enhanced performance
- `exporters/` - Result export in JSON/Markdown/HTML formats with comprehensive reporting
- `health/` - System health monitoring and diagnostics
- `llm/` - LLM provider implementations with enhanced model discovery
- `middleware/` - Rate limiting and request processing middleware
- `monitoring/` - Performance monitoring and metrics collection
- `pattern/` - Enhanced pattern loading, matching, schema management, and agentic pattern support
- `qa/` - LLM-powered question generation with robust caching and enhanced templates
- `services/` - Enhanced business logic with agentic services, multi-agent design, and advanced recommendations
- `state/` - Session state management with multi-layer caching
- `ui/` - Enhanced UI components with advanced pattern management and system configuration
- `utils/` - Enhanced utilities (logging, audit, PII redaction, error boundaries)
- `validation/` - Advanced validation components for agent display and system integrity
- `security/` - Advanced prompt defense system with 8 specialized detectors

### Security Package (`app/security/`)
- `advanced_prompt_defender.py` - Main security orchestrator and coordinator
- `overt_injection_detector.py` - Direct prompt manipulation detection
- `covert_injection_detector.py` - Hidden attack detection (base64, markdown, zero-width)
- `multilingual_attack_detector.py` - Multi-language attack detection (6 languages)
- `context_attack_detector.py` - Buried instructions and lorem ipsum detection
- `data_egress_detector.py` - System prompt and environment variable protection
- `business_logic_protector.py` - Configuration access and safety toggle protection
- `protocol_tampering_detector.py` - JSON validation and format manipulation protection
- `scope_validator.py` - Business domain validation and enforcement
- `security_event_logger.py` - Structured security event logging with PII redaction
- `user_education.py` - Contextual user guidance and educational messaging
- `performance_optimizer.py` - Security performance optimization and caching
- `deployment_config.py` - Gradual rollout and feature flag management
- `rollback_manager.py` - Automatic rollback capabilities and triggers
- `attack_pack_manager.py` - Attack pattern version management and validation
- `defense_config.py` - Security configuration management
- `attack_patterns.py` - Attack pattern definitions and validation
- `input_preprocessor.py` - Input sanitization and preprocessing

### Testing Structure (`app/tests/`) *(Enhanced in v2.7.0)*
- `unit/` - Unit tests for individual components with enhanced coverage
- `integration/` - Integration tests across components with agentic service testing
- `e2e/` - End-to-end workflow tests with comprehensive scenarios
- `performance/` - Performance testing for system optimization
- `fixtures/` - Test fixtures and data for consistent testing

## Data Organization (`data/`) *(Enhanced in v2.7.0)*

### Pattern Library (`data/patterns/`)
- **Traditional Patterns**: PAT-001.json through PAT-006.json with enhanced metadata
- **Agentic Patterns**: APAT-001.json through APAT-005.json for autonomous agent solutions
- **Traditional Automation**: TRAD-AUTO-001.json for traditional automation patterns
- **Enhanced Schema**: pattern_id, name, description, feasibility, tech_stack, autonomy_assessment, reasoning_types
- **Rich Metadata**: Includes agentic capabilities, multi-agent design, and enhanced technical details
- Used for intelligent pattern matching and agentic recommendations

### Technology Catalog (`data/technologies.json`) *(Expanded)*
- Centralized database of 60+ technologies with rich metadata across 18+ categories
- **Enhanced Schema**: name, category, description, tags, maturity, license, alternatives, integrations, use_cases, agentic_capabilities
- **New Categories**: Agentic AI & Multi-Agent Systems, Enhanced Infrastructure & DevOps
- Automatic backup creation (`technologies.json.backup`) with versioning
- Used for LLM context, tech stack recommendations, and agentic technology selection

### Additional Data Files
- `agentic_technologies.json` - Specialized agentic AI technology catalog
- `component_mapping_rules.json` - Dynamic component mapping rules for diagrams
- `attack_packs/` - Security attack pattern definitions for testing

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

## Utility Scripts (`scripts/`)

### Maintenance Scripts
- `cleanup.sh` - Repository cleanup script for removing temporary files, old backups, and cache files
- Removes Python cache files, temporary files, old coverage files
- Cleans old export files (30+ days) and backup files (7+ days)
- Preserves operational files like technology catalog backup

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