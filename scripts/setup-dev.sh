#!/bin/bash

# Development setup script for Automated AI Assessment (AAA)

set -e

echo "🚀 Setting up development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pip install pre-commit
pre-commit install

# Run initial checks
echo "✅ Running initial code quality checks..."
make fmt
make lint

echo "🎉 Development environment setup complete!"
echo ""
echo "Available commands:"
echo "  make dev        - Start development server"
echo "  make test       - Run tests"
echo "  make lint       - Run linting"
echo "  make typecheck  - Run type checking"
echo "  make fmt        - Format code"
echo ""
echo "Pre-commit hooks are now installed and will run automatically on commit."