#!/bin/bash
# Comprehensive testing script for Clair RAG System

echo "🧪 Running Clair RAG System Test Suite..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

echo "📋 Test Configuration:"
echo "  - Python Path: $(pwd)/src"
echo "  - Test Directory: tests/"
echo "  - Coverage Report: htmlcov/"

# Run unit tests
echo "🔬 Running Unit Tests..."
python -m pytest tests/unit/ -v --tb=short

# Run integration tests
echo "🔗 Running Integration Tests..."
python -m pytest tests/integration/ -v --tb=short

# Run with coverage
echo "📊 Running Tests with Coverage..."
python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Type checking
echo "🔍 Running Type Checking..."
mypy src/ --ignore-missing-imports

# Security scanning
echo "🔒 Running Security Scan..."
bandit -r src/ -f json -o security-report.json || true

# Code quality
echo "✨ Checking Code Quality..."
flake8 src/ --max-line-length=100 --ignore=E203,W503

echo "✅ Test Suite Complete!"
echo "📊 Coverage report available in htmlcov/index.html"
echo "🔒 Security report available in security-report.json"