.PHONY: fmt lint test e2e up dev clean install api ui streamlit coverage docker-build docker-up docker-dev docker-down docker-logs docker-test

# Format code
fmt:
	black app/
	ruff check --fix app/

# Lint code
lint:
	ruff check app/
	mypy --config-file mypy.ini

# Comprehensive code quality check
quality:
	@echo "🔍 Running comprehensive code quality checks..."
	@echo "📝 Formatting with black..."
	black --check app/
	@echo "🔧 Linting with ruff..."
	ruff check app/
	@echo "🔍 Type checking with mypy..."
	mypy --config-file mypy.ini
	@echo "✅ All quality checks passed!"

# Type check with mypy
typecheck:
	mypy --config-file mypy.ini

# Type check with detailed output
typecheck-verbose:
	mypy --config-file mypy.ini --show-error-codes --pretty --show-column-numbers

# Check type coverage
type-coverage:
	python3 scripts/check_type_coverage.py app/

# Run type checking tests only
test-types:
	python3 -m pytest app/tests/test_type_checking.py -v -m typecheck

# Run tests (includes type checking)
test:
	python3 -m pytest app/tests/ -v --cov=app --cov-report=html --cov-report=term

# Run all tests including type checking
test-all:
	python3 -m pytest app/tests/ -v --cov=app --cov-report=html --cov-report=term -m "not slow"
	make typecheck

# Run e2e tests
e2e:
	python3 -m pytest app/tests/integration/ -v

# Catalog management commands
catalog-help:
	@echo "📚 Catalog Management Commands:"
	@echo "  make catalog-overview    - Show catalog overview dashboard"
	@echo "  make catalog-list        - List all technologies"
	@echo "  make catalog-stats       - Show catalog statistics"
	@echo "  make catalog-validate    - Validate catalog consistency"
	@echo "  make catalog-health      - Show detailed health report"
	@echo "  make catalog-backup      - Create catalog backup"
	@echo "  make catalog-example     - Run catalog management examples"
	@echo ""
	@echo "For detailed CLI help: python -m app.cli.main --help"

# Show catalog overview
catalog-overview:
	python3 -m app.cli.main dashboard overview

# List all technologies
catalog-list:
	python3 -m app.cli.main catalog list

# Show catalog statistics
catalog-stats:
	python3 -m app.cli.main catalog stats

# Validate catalog
catalog-validate:
	python3 -m app.cli.main catalog validate --detailed

# Show health report
catalog-health:
	python3 -m app.cli.main dashboard health

# Show quality report
catalog-quality:
	python3 -m app.cli.main dashboard quality

# Show trends
catalog-trends:
	python3 -m app.cli.main dashboard trends

# List pending reviews
catalog-reviews:
	python3 -m app.cli.main review list --verbose

# Create backup
catalog-backup:
	python3 -m app.cli.main bulk backup

# Export catalog to JSON
catalog-export:
	python3 -m app.cli.main bulk export catalog_export.json
	@echo "Catalog exported to catalog_export.json"

# Run catalog management examples
catalog-example:
	python3 examples/catalog_management_example.py

# CLI tool shortcuts
cli:
	python3 -m app.cli.main $(ARGS)

catalog:
	python3 -m app.cli.main catalog $(ARGS)

review:
	python3 -m app.cli.main review $(ARGS)

bulk:
	python3 -m app.cli.main bulk $(ARGS)

dashboard:
	python3 -m app.cli.main dashboard $(ARGS)
	python3 -m pytest app/tests/integration/ -v

# Start services (API + Streamlit) - Local development
up:
	@echo "🚀 Starting both FastAPI backend and Streamlit UI..."
	@echo "🔧 API will be available at: http://localhost:8000"
	@echo "📱 Streamlit UI will be available at: http://localhost:8500"
	@echo ""
	python3 -m uvicorn app.api:app --reload --host 0.0.0.0 --port 8000 &
	sleep 3
	python3 run_streamlit.py

# Start everything (alias for up)
dev:
	make up

# Install dependencies
install:
	python3 -m pip install -r requirements.txt

# Clean cache and temp files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf cache/
	docker system prune -f

# Run API server only
api:
	python3 -m uvicorn app.api:app --reload --host 0.0.0.0 --port 8000

# Run Streamlit UI only (NEW interface with Agent Solution tab)
ui:
	python3 run_streamlit.py

# Run Streamlit in browser (same as ui)
streamlit:
	@echo "🚀 Starting NEW Streamlit UI with Agent Solution tab..."
	@echo "📱 The app will open in your browser at: http://localhost:8500"
	@echo "🔧 Make sure the FastAPI backend is running at: http://localhost:8000"
	@echo "🤖 NEW: Includes dedicated Agent Solution tab for agentic AI designs!"
	@echo ""
	python3 run_streamlit.py

# Run NEW interface directly (bypass run_streamlit.py)
new-ui:
	@echo "🚀 Starting NEW Streamlit UI directly..."
	@echo "📱 The app will open in your browser at: http://localhost:8500"
	@echo "🔧 Make sure the FastAPI backend is running at: http://localhost:8000"
	@echo "🤖 NEW: Includes dedicated Agent Solution tab for agentic AI designs!"
	@echo ""
	python3 -m streamlit run app/main.py --server.port 8500 --server.address 0.0.0.0 --browser.serverAddress localhost

# Test coverage
coverage:
	python3 -m pytest app/tests/ --cov=app --cov-report=html
	open htmlcov/index.html

# Docker Commands
docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose build

docker-up:
	@echo "🐳 Starting services with Docker Compose..."
	@echo "🔧 API will be available at: http://localhost:8000"
	@echo "📱 Streamlit UI will be available at: http://localhost:8500"
	@echo "🗄️  Redis will be available at: localhost:6379"
	docker-compose up -d
	@echo "✅ Services started! Check status with: make docker-logs"

docker-dev:
	@echo "🐳 Starting development environment with Docker..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

docker-prod:
	@echo "🐳 Starting production environment with Docker..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

docker-down:
	@echo "🐳 Stopping Docker services..."
	docker-compose down

docker-logs:
	@echo "🐳 Showing Docker service logs..."
	docker-compose logs -f

docker-test:
	@echo "🐳 Running tests in Docker container..."
	docker-compose run --rm api python3 -m pytest app/tests/ -v

docker-shell:
	@echo "🐳 Opening shell in API container..."
	docker-compose exec api /bin/bash

# Show help
help:
	@echo "🤖 Automated AI Assessment (AAA) - Available Commands:"
	@echo ""
	@echo "🚀 Local Development:"
	@echo "  make dev        - Start both API and Streamlit UI (recommended for local dev)"
	@echo "  make up         - Same as dev"
	@echo "  make api        - Start FastAPI backend only (http://localhost:8000)"
	@echo "  make streamlit  - Start Streamlit UI only (http://localhost:8500)"
	@echo "  make ui         - Same as streamlit"
	@echo ""
	@echo "🐳 Docker Development:"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start services with Docker Compose (production-like)"
	@echo "  make docker-dev    - Start development environment with live reloading"
	@echo "  make docker-prod   - Start production environment"
	@echo "  make docker-down   - Stop Docker services"
	@echo "  make docker-logs   - Show service logs"
	@echo "  make docker-test   - Run tests in Docker"
	@echo "  make docker-shell  - Open shell in API container"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test       - Run all unit tests with coverage"
	@echo "  make test-all   - Run all tests including type checking"
	@echo "  make test-types - Run type checking tests only"
	@echo "  make e2e        - Run integration tests"
	@echo "  make coverage   - Generate and open coverage report"
	@echo ""
	@echo "🔧 Code Quality:"
	@echo "  make fmt            - Format code with black and ruff"
	@echo "  make lint           - Lint code with ruff and mypy"
	@echo "  make quality        - Comprehensive code quality check"
	@echo "  make typecheck      - Run type checking with mypy"
	@echo "  make typecheck-verbose - Detailed type checking output"
	@echo "  make type-coverage  - Check type hint coverage"
	@echo ""
	@echo "📦 Setup:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make clean      - Clean cache and temp files"
	@echo ""
	@echo "💡 Quick Start (Local):"
	@echo "  1. make install"
	@echo "  2. make dev"
	@echo "  3. Open http://localhost:8500 in your browser"
	@echo ""
	@echo "💡 Quick Start (Docker):"
	@echo "  1. make docker-build"
	@echo "  2. make docker-up"
	@echo "  3. Open http://localhost:8500 in your browser"