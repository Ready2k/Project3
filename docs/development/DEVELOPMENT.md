# Development Guide

Complete guide for developers working on the Automated AI Assessment (AAA) system.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Testing Strategy](#testing-strategy)
5. [Code Quality](#code-quality)
6. [Architecture Patterns](#architecture-patterns)
7. [Contributing Guidelines](#contributing-guidelines)

## Development Setup

### Prerequisites

- **Python 3.10+**: Primary development language
- **Git**: Version control
- **Make**: Build automation (optional but recommended)
- **Docker**: Containerization (optional)
- **IDE**: VS Code, PyCharm, or similar with Python support

### Local Development Environment

#### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd agentic_or_not

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install
# or
pip install -r requirements.txt
```

#### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
# Add other required keys
```

#### 3. Verify Installation

```bash
# Run tests to verify setup
make test

# Start development servers
make dev
```

### Development Tools

#### Make Commands

```bash
# Development
make dev          # Start both API and UI
make api          # Start FastAPI only
make streamlit    # Start Streamlit only
make ui           # Alias for streamlit

# Testing
make test         # Run all tests with coverage
make e2e          # Integration tests only
make coverage     # Generate HTML coverage report

# Code Quality
make fmt          # Format with black and ruff
make lint         # Lint with ruff and mypy

# Maintenance
make clean        # Clean cache and temp files
make install      # Install dependencies
make help         # Show all commands
```

#### Docker Development

```bash
# Development with live reloading
make docker-dev
# or
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production-like environment
make docker-up
# or
docker-compose up -d
```

## Project Structure

### Root Directory Structure

```
├── app/                    # Main application package
│   ├── api.py             # FastAPI application
│   ├── main.py            # Streamlit application
│   ├── config.py          # Configuration management
│   ├── core/              # Core system components
│   ├── services/          # Business logic services
│   ├── llm/               # LLM provider implementations
│   ├── pattern/           # Pattern management
│   ├── security/          # Security components
│   ├── ui/                # UI components
│   ├── utils/             # Utilities and helpers
│   └── tests/             # Test suite
├── data/                  # Data files and catalogs
├── docs/                  # Documentation
├── config.yaml           # Application configuration
├── requirements.txt       # Python dependencies
├── Makefile              # Build automation
└── docker-compose.yml    # Container orchestration
```

### Application Package Structure

```
app/
├── api.py                 # FastAPI REST API
├── main.py               # Streamlit UI application
├── config.py             # Pydantic settings
├── core/
│   ├── __init__.py
│   ├── dependencies.py   # Dependency injection
│   └── exceptions.py     # Custom exceptions
├── services/
│   ├── __init__.py
│   ├── pattern_service.py
│   ├── recommendation_service.py
│   ├── agentic_recommendation_service.py
│   ├── tech_stack_generator.py
│   └── jira.py
├── llm/
│   ├── __init__.py
│   ├── base.py           # Abstract base classes
│   ├── openai_provider.py
│   ├── bedrock_provider.py
│   ├── claude_provider.py
│   ├── internal_provider.py
│   └── fakes.py          # Test doubles
├── pattern/
│   ├── __init__.py
│   ├── loader.py         # Pattern loading
│   ├── matcher.py        # Pattern matching
│   └── schema_config.json
├── security/
│   ├── __init__.py
│   ├── advanced_prompt_defender.py
│   ├── input_preprocessor.py
│   └── [8 specialized detectors]
├── ui/
│   ├── __init__.py
│   ├── analysis_display.py
│   ├── pattern_management.py
│   └── system_config.py
├── utils/
│   ├── __init__.py
│   ├── logging.py        # Logging configuration
│   ├── audit.py          # Audit trail
│   └── pii_redaction.py  # PII handling
└── tests/
    ├── unit/             # Unit tests
    ├── integration/      # Integration tests
    └── e2e/              # End-to-end tests
```

## Development Workflow

### Feature Development Process

#### 1. Planning Phase
- Review requirements and acceptance criteria
- Design API and data structures
- Plan testing strategy
- Consider security implications

#### 2. Implementation Phase
- Create feature branch from main
- Implement core functionality
- Write comprehensive tests
- Update documentation

#### 3. Testing Phase
- Run full test suite
- Perform manual testing
- Security review
- Performance testing

#### 4. Review Phase
- Code review process
- Documentation review
- Integration testing
- Deployment preparation

### Branch Strategy

```bash
# Feature development
git checkout -b feature/new-feature-name
# Implement feature
git commit -m "feat: add new feature"
git push origin feature/new-feature-name
# Create pull request

# Bug fixes
git checkout -b fix/bug-description
# Fix bug
git commit -m "fix: resolve bug description"

# Documentation updates
git checkout -b docs/update-description
# Update docs
git commit -m "docs: update documentation"
```

### Commit Message Convention

Follow conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add session resume endpoint
fix(security): resolve prompt injection vulnerability
docs(guides): update user guide with new features
test(pattern): add comprehensive pattern matching tests
```

## Testing Strategy

### Test Structure

#### Unit Tests (`app/tests/unit/`)
- Test individual functions and classes
- Mock external dependencies
- Fast execution (< 1 second per test)
- High coverage (>95% target)

#### Integration Tests (`app/tests/integration/`)
- Test component interactions
- Use test databases and services
- Moderate execution time (< 10 seconds per test)
- Focus on critical paths

#### End-to-End Tests (`app/tests/e2e/`)
- Test complete workflows
- Use real or realistic services
- Longer execution time acceptable
- Cover user scenarios

### Testing Best Practices

#### Test Organization
```python
# test_pattern_service.py
import pytest
from unittest.mock import Mock, patch

from app.services.pattern_service import PatternService
from app.tests.fixtures import sample_patterns

class TestPatternService:
    """Test suite for PatternService."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.service = PatternService()
    
    def test_load_patterns_success(self):
        """Test successful pattern loading."""
        # Arrange
        expected_patterns = sample_patterns()
        
        # Act
        patterns = self.service.load_patterns()
        
        # Assert
        assert len(patterns) > 0
        assert all(p.pattern_id for p in patterns)
    
    @pytest.mark.asyncio
    async def test_match_patterns_async(self):
        """Test async pattern matching."""
        # Test implementation
        pass
```

#### Test Fixtures
```python
# app/tests/fixtures.py
import pytest
from app.models import Pattern, Requirements

@pytest.fixture
def sample_pattern():
    """Sample pattern for testing."""
    return Pattern(
        pattern_id="PAT-001",
        name="Test Pattern",
        description="Test pattern description",
        feasibility="Automatable",
        tech_stack=["Python", "FastAPI"],
        confidence_score=0.85
    )

@pytest.fixture
def sample_requirements():
    """Sample requirements for testing."""
    return Requirements(
        description="Test automation requirement",
        domain="testing",
        constraints=[]
    )
```

#### Mocking External Services
```python
# Test with mocked LLM provider
@patch('app.llm.openai_provider.OpenAIProvider.generate')
async def test_recommendation_generation(mock_generate):
    """Test recommendation generation with mocked LLM."""
    # Arrange
    mock_generate.return_value = "Mocked LLM response"
    service = RecommendationService()
    
    # Act
    result = await service.generate_recommendation(requirements)
    
    # Assert
    assert result is not None
    mock_generate.assert_called_once()
```

### Running Tests

```bash
# All tests with coverage
make test

# Specific test categories
pytest app/tests/unit/ -v
pytest app/tests/integration/ -v
pytest app/tests/e2e/ -v

# Specific test file
pytest app/tests/unit/test_pattern_service.py -v

# Specific test method
pytest app/tests/unit/test_pattern_service.py::TestPatternService::test_load_patterns -v

# Coverage report
make coverage
# Opens htmlcov/index.html in browser
```

### Test Configuration

#### pytest.ini
```ini
[tool:pytest]
testpaths = app/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=95
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

## Code Quality

### Code Formatting

#### Black Configuration
```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

#### Ruff Configuration
```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py310"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
]
```

### Type Checking

#### MyPy Configuration
```ini
# mypy.ini
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-tests.*]
disallow_untyped_defs = False
```

### Code Quality Commands

```bash
# Format code
make fmt
# or
black app/
ruff --fix app/

# Lint code
make lint
# or
ruff app/
mypy app/ --ignore-missing-imports

# Check all quality metrics
make fmt && make lint && make test
```

## Architecture Patterns

### Dependency Injection

```python
# app/core/dependencies.py
from functools import lru_cache
from app.config import Settings
from app.services.pattern_service import PatternService

@lru_cache()
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

def get_pattern_service() -> PatternService:
    """Get pattern service instance."""
    return PatternService()

# Usage in FastAPI
from fastapi import Depends
from app.core.dependencies import get_pattern_service

@app.get("/patterns")
async def get_patterns(
    service: PatternService = Depends(get_pattern_service)
):
    return await service.get_patterns()
```

### Async/Await Patterns

```python
# Async service methods
class RecommendationService:
    async def generate_recommendation(
        self, 
        requirements: Requirements
    ) -> Recommendation:
        """Generate recommendation asynchronously."""
        # Async LLM call
        analysis = await self.llm_provider.analyze(requirements)
        
        # Async pattern matching
        patterns = await self.pattern_service.match_patterns(requirements)
        
        # Combine results
        return self._build_recommendation(analysis, patterns)

# Async API endpoints
@app.post("/recommend")
async def recommend(
    request: RecommendRequest,
    service: RecommendationService = Depends(get_recommendation_service)
):
    """Generate recommendations endpoint."""
    try:
        recommendation = await service.generate_recommendation(request.requirements)
        return {"status": "success", "data": recommendation}
    except Exception as e:
        logger.error(f"Recommendation failed: {e}")
        raise HTTPException(status_code=500, detail="Recommendation failed")
```

### Error Handling Patterns

```python
# Custom exceptions
class AAException(Exception):
    """Base exception for AAA system."""
    pass

class PatternNotFoundError(AAException):
    """Pattern not found error."""
    pass

class LLMProviderError(AAException):
    """LLM provider error."""
    pass

# Error handling in services
class PatternService:
    async def get_pattern(self, pattern_id: str) -> Pattern:
        """Get pattern by ID with error handling."""
        try:
            pattern = await self._load_pattern(pattern_id)
            if not pattern:
                raise PatternNotFoundError(f"Pattern {pattern_id} not found")
            return pattern
        except FileNotFoundError:
            logger.error(f"Pattern file not found: {pattern_id}")
            raise PatternNotFoundError(f"Pattern {pattern_id} not found")
        except Exception as e:
            logger.error(f"Unexpected error loading pattern {pattern_id}: {e}")
            raise AAException(f"Failed to load pattern: {e}")

# Error handling in API
@app.exception_handler(PatternNotFoundError)
async def pattern_not_found_handler(request: Request, exc: PatternNotFoundError):
    """Handle pattern not found errors."""
    return JSONResponse(
        status_code=404,
        content={"error": "Pattern not found", "detail": str(exc)}
    )
```

### Configuration Management

```python
# app/config.py
from pydantic import BaseSettings, Field
from typing import Optional, List

class Settings(BaseSettings):
    """Application settings."""
    
    # LLM Configuration
    provider: str = Field(default="openai", env="PROVIDER")
    model: str = Field(default="gpt-4o", env="MODEL")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # System Configuration
    pattern_library_path: str = "./data/patterns"
    technology_catalog_path: str = "./data/technologies.json"
    export_path: str = "./exports"
    
    # Performance Configuration
    llm_timeout: int = 30
    cache_ttl: int = 3600
    max_concurrent_requests: int = 10
    
    # Security Configuration
    enable_security_defense: bool = True
    security_log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Usage
settings = Settings()
```

### Logging Patterns

```python
# app/utils/logging.py
import logging
from loguru import logger
import sys

def setup_logging(level: str = "INFO"):
    """Setup application logging."""
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # Add file handler
    logger.add(
        "logs/app.log",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="30 days"
    )

# Usage in modules
from loguru import logger

class PatternService:
    def load_patterns(self):
        """Load patterns with logging."""
        logger.info("Loading patterns from library")
        try:
            patterns = self._load_from_files()
            logger.info(f"Loaded {len(patterns)} patterns successfully")
            return patterns
        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
            raise
```

## Contributing Guidelines

### Code Standards

#### Python Style Guide
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Write docstrings for all public methods
- Keep functions focused and small (< 50 lines)
- Use meaningful variable and function names

#### Documentation Standards
- Update documentation for new features
- Include code examples in docstrings
- Write clear commit messages
- Update CHANGELOG.md for significant changes

#### Security Standards
- Validate all user inputs
- Use parameterized queries for database operations
- Implement proper error handling
- Follow security best practices for API design

### Pull Request Process

#### Before Submitting
1. **Code Quality**: Run `make fmt && make lint`
2. **Tests**: Ensure `make test` passes with >95% coverage
3. **Documentation**: Update relevant documentation
4. **Security**: Review for security implications

#### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] Security implications considered
```

### Development Best Practices

#### Performance Considerations
- Use async/await for I/O operations
- Implement caching for expensive operations
- Monitor memory usage and optimize as needed
- Profile code for performance bottlenecks

#### Security Considerations
- Validate and sanitize all inputs
- Use secure coding practices
- Implement proper authentication and authorization
- Regular security reviews and updates

#### Maintainability
- Write clean, readable code
- Use consistent naming conventions
- Implement proper error handling
- Maintain comprehensive test coverage

#### Scalability
- Design for horizontal scaling
- Use stateless architecture patterns
- Implement proper resource management
- Monitor and optimize performance

### Getting Help

#### Resources
- **Documentation**: Comprehensive guides in `docs/`
- **Code Examples**: Reference implementations in codebase
- **Test Examples**: Test patterns in `app/tests/`
- **Architecture Guide**: System design documentation

#### Communication
- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub discussions for questions and ideas
- **Code Review**: Participate in pull request reviews
- **Documentation**: Contribute to documentation improvements