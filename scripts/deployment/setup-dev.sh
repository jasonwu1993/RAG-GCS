#!/bin/bash
echo "🔧 Setting up development environment..."

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env file. Please configure with your values."
fi

echo "✅ Development environment ready!"
echo "📋 Next steps:"
echo "1. Configure .env with your values"
echo "2. Place service-account.json in root directory"
echo "3. Run: python main.py"
