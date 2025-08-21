.PHONY: fmt lint test e2e up dev clean install api ui streamlit coverage docker-build docker-up docker-dev docker-down docker-logs docker-test

# Format code
fmt:
	black app/
	ruff --fix app/

# Lint code
lint:
	ruff app/
	mypy app/ --ignore-missing-imports

# Run tests
test:
	python3 -m pytest app/tests/ -v --cov=app --cov-report=html --cov-report=term

# Run e2e tests
e2e:
	python3 -m pytest app/tests/integration/ -v

# Start services (API + Streamlit) - Local development
up:
	@echo "🚀 Starting both FastAPI backend and Streamlit UI..."
	@echo "🔧 API will be available at: http://localhost:8000"
	@echo "📱 Streamlit UI will be available at: http://localhost:8501"
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
	@echo "📱 The app will open in your browser at: http://localhost:8501"
	@echo "🔧 Make sure the FastAPI backend is running at: http://localhost:8000"
	@echo "🤖 NEW: Includes dedicated Agent Solution tab for agentic AI designs!"
	@echo ""
	python3 run_streamlit.py

# Run NEW interface directly (bypass run_streamlit.py)
new-ui:
	@echo "🚀 Starting NEW Streamlit UI directly..."
	@echo "📱 The app will open in your browser at: http://localhost:8501"
	@echo "🔧 Make sure the FastAPI backend is running at: http://localhost:8000"
	@echo "🤖 NEW: Includes dedicated Agent Solution tab for agentic AI designs!"
	@echo ""
	python3 -m streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0 --browser.serverAddress localhost

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
	@echo "📱 Streamlit UI will be available at: http://localhost:8501"
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
	@echo "  make streamlit  - Start Streamlit UI only (http://localhost:8501)"
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
	@echo "  make e2e        - Run integration tests"
	@echo "  make coverage   - Generate and open coverage report"
	@echo ""
	@echo "🔧 Code Quality:"
	@echo "  make fmt        - Format code with black and ruff"
	@echo "  make lint       - Lint code with ruff and mypy"
	@echo ""
	@echo "📦 Setup:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make clean      - Clean cache and temp files"
	@echo ""
	@echo "💡 Quick Start (Local):"
	@echo "  1. make install"
	@echo "  2. make dev"
	@echo "  3. Open http://localhost:8501 in your browser"
	@echo ""
	@echo "💡 Quick Start (Docker):"
	@echo "  1. make docker-build"
	@echo "  2. make docker-up"
	@echo "  3. Open http://localhost:8501 in your browser"