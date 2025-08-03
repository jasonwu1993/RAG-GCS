#!/bin/bash
# Development startup script for Clair RAG System

echo "🚀 Starting Clair RAG Development Environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Check environment file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from template..."
    cp .env.example .env
    echo "✏️  Please edit .env with your configuration"
fi

# Start the development server
echo "🎯 Starting development server..."
echo "📍 Backend will be available at: http://localhost:8080"
echo "📍 API docs will be available at: http://localhost:8080/docs"
echo "📍 Health check: http://localhost:8080/health"

python run_server.py