.PHONY: fmt lint test e2e up dev clean install api ui streamlit coverage

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

# Start services (API + Streamlit)
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

# Run API server only
api:
	python3 -m uvicorn app.api:app --reload --host 0.0.0.0 --port 8000

# Run Streamlit UI only
ui:
	python3 run_streamlit.py

# Run Streamlit in browser (same as ui)
streamlit:
	@echo "🚀 Starting Streamlit UI..."
	@echo "📱 The app will open in your browser at: http://localhost:8501"
	@echo "🔧 Make sure the FastAPI backend is running at: http://localhost:8000"
	@echo ""
	python3 run_streamlit.py

# Test coverage
coverage:
	python3 -m pytest app/tests/ --cov=app --cov-report=html
	open htmlcov/index.html

# Show help
help:
	@echo "🤖 AgenticOrNot v1.3.2 - Available Commands:"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make dev        - Start both API and Streamlit UI (recommended for local dev)"
	@echo "  make up         - Same as dev"
	@echo "  make api        - Start FastAPI backend only (http://localhost:8000)"
	@echo "  make streamlit  - Start Streamlit UI only (http://localhost:8501)"
	@echo "  make ui         - Same as streamlit"
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
	@echo "💡 Quick Start:"
	@echo "  1. make install"
	@echo "  2. make dev"
	@echo "  3. Open http://localhost:8501 in your browser"