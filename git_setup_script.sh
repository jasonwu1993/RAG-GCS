#!/bin/bash

# 🚀 Complete Git Setup Script for Clair Backend
# This script sets up a Git repository with proper security practices

echo "🚀 Setting up Clair Backend Git Repository..."

# Step 1: Initialize Git repository
echo "📁 Initializing Git repository..."
git init

# Step 2: Create .gitignore file
echo "🔒 Creating .gitignore for security..."
cat > .gitignore << 'EOF'
# Environment variables and secrets
.env
*.env
!.env.example

# Google Cloud credentials
service-account.json
*.json
!package.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env/
.venv/
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Testing
.coverage
.pytest_cache/
.tox/

# Jupyter Notebook
.ipynb_checkpoints

# Docker
.dockerignore
docker-compose.override.yml

# Temporary files
*.tmp
*.temp
temp/
tmp/

# Database
*.db
*.sqlite
*.sqlite3

# Backup files
*.bak
*.backup
EOF

# Step 3: Create README.md
echo "📚 Creating README.md..."
cat > README.md << 'EOF'
# 🤖 Clair - AI Financial Advisor Backend

Clair (随时守护您财富的智能专家) is an intelligent AI financial advisor that syncs with Google Drive to analyze your financial documents and provide personalized advice.

## 🎯 Features

- 🔄 **Google Drive Sync** - Automatic document synchronization
- 🧠 **AI Analysis** - Powered by OpenAI GPT-4 and Vertex AI
- 📊 **Vector Search** - Intelligent document retrieval
- 🔒 **Secure** - Enterprise-grade security and privacy
- ⚡ **Real-time** - Live sync status and updates

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud Project with Vertex AI enabled
- OpenAI API key
- Google Drive folder access

### Installation
```bash
# Clone repository
git clone <your-repo-url>
cd rag-gcs

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your values

# Add Google Cloud credentials
# Place service-account.json in root directory

# Run application
python main.py
```

### Environment Variables
Copy `.env.example` to `.env` and configure:

- `GCP_PROJECT_ID` - Your Google Cloud Project ID
- `GCS_BUCKET_NAME` - Storage bucket for documents
- `GOOGLE_DRIVE_FOLDER_ID` - Shared Google Drive folder ID
- `OPENAI_API_KEY` - OpenAI API key for AI responses
- `INDEX_ENDPOINT_ID` - Vertex AI index endpoint
- `DEPLOYED_INDEX_ID` - Vertex AI deployed index ID

## 📡 API Endpoints

- `GET /health` - Health check and system status
- `POST /sync_drive` - Trigger Google Drive sync
- `GET /sync_status` - Get current sync status
- `GET /list_files` - List all synced documents
- `POST /ask` - Ask questions about documents
- `POST /feedback` - Submit user feedback

## 🐳 Docker Deployment

```bash
# Build image
docker build -t rag-gcs .

# Run container
docker run -p 8000:8000 --env-file .env rag-gcs
```

## 🚀 Production Deployment

### Google Cloud Run
```bash
# Deploy to Cloud Run
gcloud run deploy rag-gcs \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🔒 Security

- ✅ Service account with minimal permissions
- ✅ Environment variables for all secrets
- ✅ No credentials in code
- ✅ HTTPS only in production
- ✅ Input validation and sanitization

## 📊 Monitoring

- Health checks at `/health`
- Sync status monitoring via `/sync_status`
- Comprehensive error logging
- Performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, please check:
1. Health endpoint: `/health`
2. Application logs
3. Environment configuration
4. Google Drive permissions

---
Built with ❤️ for intelligent financial management
EOF

# Step 4: Create deployment directory structure
echo "📁 Creating project structure..."
mkdir -p docs
mkdir -p scripts
mkdir -p tests

# Step 5: Create docker-compose for development
echo "🐳 Creating docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  rag-gcs:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./service-account.json:/app/service-account.json:ro
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Add a reverse proxy for production
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - rag-gcs
    profiles:
      - production
EOF

# Step 6: Create development scripts
echo "🛠️ Creating development scripts..."

# Development setup script
cat > scripts/setup-dev.sh << 'EOF'
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
EOF

# Production deployment script
cat > scripts/deploy-prod.sh << 'EOF'
#!/bin/bash
echo "🚀 Deploying to production..."

# Build and push Docker image
PROJECT_ID=${GCP_PROJECT_ID}
IMAGE_NAME="gcr.io/${PROJECT_ID}/rag-gcs"

# Build image
docker build -t ${IMAGE_NAME} .

# Push to Google Container Registry
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
gcloud run deploy rag-gcs \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=${GCP_PROJECT_ID} \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10

echo "✅ Deployment complete!"
EOF

# Make scripts executable
chmod +x scripts/*.sh

# Step 7: Create basic tests
echo "🧪 Creating test structure..."
cat > tests/test_health.py << 'EOF'
import pytest
import requests
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    """Test that health endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"

def test_sync_status_endpoint():
    """Test sync status endpoint"""
    response = client.get("/sync_status")
    assert response.status_code == 200
    assert "is_syncing" in response.json()
EOF

# Step 8: Create requirements-dev.txt for development dependencies
cat > requirements-dev.txt << 'EOF'
# Include production requirements
-r requirements.txt

# Development dependencies
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
mypy==1.7.1
pre-commit==3.5.0

# Testing
httpx==0.25.2
pytest-cov==4.1.0
EOF

# Step 9: Add all files to Git
echo "📦 Adding files to Git..."
git add .gitignore
git add README.md
git add requirements.txt
git add requirements-dev.txt
git add .env.example
git add main.py
git add Dockerfile
git add docker-compose.yml
git add scripts/
git add tests/
git add docs/

# Step 10: Create initial commit
echo "💾 Creating initial commit..."
git commit -m "🎉 Initial commit: Clair AI Financial Advisor Backend

✨ Features:
- Google Drive sync integration
- Vertex AI vector search
- OpenAI GPT-4 powered responses
- Real-time sync status
- Docker containerization
- Production-ready deployment

🔒 Security:
- Environment variables for secrets
- Service account authentication
- Proper .gitignore for credentials

🚀 Ready for deployment to Google Cloud Run"

# Step 11: Set up remote repository
echo "🌐 Setting up remote repository..."
git branch -M main
git remote add origin https://github.com/jasonwu1993/RAG-GCS.git

# Check if we can push (repository might already exist)
echo "📡 Pushing to GitHub..."
if git push -u origin main 2>/dev/null; then
    echo "✅ Successfully pushed to GitHub!"
else
    echo "⚠️  Repository might already exist. Trying to pull and merge..."
    git pull origin main --allow-unrelated-histories
    git push origin main
fi

# Step 12: Create commit script for ongoing development
echo "📝 Creating commit script for future updates..."
cat > commit-changes.sh << 'EOF'
#!/bin/bash

# 🚀 Clair Backend - Quick Commit Script
# Usage: ./commit-changes.sh "Your commit message"

set -e  # Exit on any error

echo "🔍 Checking repository status..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check for unstaged changes
if ! git diff-index --quiet HEAD --; then
    echo "📝 Found unstaged changes"
else
    echo "ℹ️  No changes to commit"
    exit 0
fi

# Show current status
echo "📊 Current repository status:"
git status --short

echo ""
echo "📁 Changed files:"
git diff --name-only

echo ""
echo "🔍 Security check - ensuring no secrets are being committed..."

# Check for potential secrets
SECRETS_FOUND=false

# Check for .env files (except .env.example)
if git diff --cached --name-only | grep -E '\.env
EOF

chmod +x git_setup_script.sh > /dev/null; then
    echo "⚠️  WARNING: .env file detected in commit!"
    SECRETS_FOUND=true
fi

# Check for service account files
if git diff --cached --name-only | grep -E 'service-account.*\.json
EOF

chmod +x git_setup_script.sh > /dev/null; then
    echo "⚠️  WARNING: service-account.json detected in commit!"
    SECRETS_FOUND=true
fi

# Check for API keys in code
if git diff --cached | grep -iE '(api[_-]?key|secret|password|token).*[=:]\s*["\'][^"\']{10,}' > /dev/null; then
    echo "⚠️  WARNING: Potential API key or secret detected in code!"
    SECRETS_FOUND=true
fi

if [ "$SECRETS_FOUND" = true ]; then
    echo ""
    echo "🛑 SECURITY ALERT: Potential secrets detected!"
    echo "Please review your changes and remove any sensitive information."
    echo "Use environment variables instead of hardcoded secrets."
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Commit cancelled for security reasons"
        exit 1
    fi
fi

# Get commit message
if [ -n "$1" ]; then
    COMMIT_MSG="$1"
else
    echo ""
    echo "💬 Enter commit message:"
    read -r COMMIT_MSG
    
    if [ -z "$COMMIT_MSG" ]; then
        echo "❌ Error: Commit message cannot be empty"
        exit 1
    fi
fi

# Stage all changes
echo "📦 Staging changes..."
git add .

# Show what will be committed
echo ""
echo "📋 Files to be committed:"
git diff --cached --name-only

echo ""
echo "🔍 Preview of changes:"
git diff --cached --stat

# Confirm commit
echo ""
read -p "🚀 Commit and push these changes? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "❌ Commit cancelled"
    git reset
    exit 0
fi

# Create commit with timestamp and emoji
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
FORMATTED_MSG="🔄 $COMMIT_MSG

📅 Updated: $TIMESTAMP
🏷️  Auto-commit via script"

echo "💾 Creating commit..."
git commit -m "$FORMATTED_MSG"

# Push to remote
echo "📡 Pushing to GitHub..."
if git push origin main; then
    echo "✅ Successfully pushed to https://github.com/jasonwu1993/RAG-GCS"
    echo ""
    echo "🎉 Commit complete!"
    echo "📊 Repository status:"
    git log --oneline -3
else
    echo "❌ Failed to push. You may need to pull first:"
    echo "   git pull origin main"
    echo "   git push origin main"
fi

echo ""
echo "🔗 View on GitHub: https://github.com/jasonwu1993/RAG-GCS"
EOF

chmod +x commit-changes.sh

# Step 13: Create a development workflow script
echo "🛠️ Creating development workflow script..."
cat > dev-workflow.sh << 'EOF'
#!/bin/bash

# 🔧 Clair Backend - Development Workflow Script

show_help() {
    echo "🛠️  Clair Backend Development Workflow"
    echo ""
    echo "Usage: ./dev-workflow.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Set up development environment"
    echo "  run       - Run the backend server"
    echo "  test      - Run tests"
    echo "  lint      - Check code style"
    echo "  sync      - Test Google Drive sync"
    echo "  commit    - Commit and push changes"
    echo "  deploy    - Deploy to production"
    echo "  status    - Show git and service status"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./dev-workflow.sh setup"
    echo "  ./dev-workflow.sh run"
    echo "  ./dev-workflow.sh commit \"Fix sync bug\""
}

setup_dev() {
    echo "🔧 Setting up development environment..."
    
    # Check if .env exists
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            echo "📝 Created .env from template. Please configure with your values."
        else
            echo "❌ No .env.example found"
            exit 1
        fi
    fi
    
    # Check if service account exists
    if [ ! -f service-account.json ]; then
        echo "⚠️  service-account.json not found. Please add your Google Cloud credentials."
    fi
    
    # Install dependencies
    if [ -f requirements.txt ]; then
        echo "📦 Installing dependencies..."
        pip install -r requirements.txt
    fi
    
    echo "✅ Development environment ready!"
}

run_server() {
    echo "🚀 Starting Clair backend server..."
    
    # Check environment
    if [ ! -f .env ]; then
        echo "❌ .env file not found. Run: ./dev-workflow.sh setup"
        exit 1
    fi
    
    # Load environment variables
    source .env
    
    # Run server
    python main.py
}

test_sync() {
    echo "🔄 Testing Google Drive sync..."
    
    # Health check
    echo "🩺 Health check..."
    curl -s http://localhost:8000/health | jq .
    
    echo ""
    echo "🔄 Triggering sync..."
    curl -s -X POST http://localhost:8000/sync_drive | jq .
    
    echo ""
    echo "📊 Sync status..."
    curl -s http://localhost:8000/sync_status | jq .
}

commit_changes() {
    if [ -n "$2" ]; then
        ./commit-changes.sh "$2"
    else
        ./commit-changes.sh
    fi
}

show_status() {
    echo "📊 Clair Backend Status"
    echo "======================"
    echo ""
    echo "📁 Git Status:"
    git status --short
    echo ""
    echo "🌐 Remote Repository:"
    git remote -v
    echo ""
    echo "📈 Recent Commits:"
    git log --oneline -5
    echo ""
    echo "🔧 Environment Check:"
    if [ -f .env ]; then
        echo "✅ .env file exists"
    else
        echo "❌ .env file missing"
    fi
    
    if [ -f service-account.json ]; then
        echo "✅ service-account.json exists"
    else
        echo "❌ service-account.json missing"
    fi
    
    if [ -f main.py ]; then
        echo "✅ main.py exists"
    else
        echo "❌ main.py missing"
    fi
}

# Main script logic
case "$1" in
    setup)
        setup_dev
        ;;
    run)
        run_server
        ;;
    test)
        echo "🧪 Running tests..."
        pytest tests/ -v
        ;;
    lint)
        echo "🎨 Checking code style..."
        flake8 main.py
        black --check main.py
        ;;
    sync)
        test_sync
        ;;
    commit)
        commit_changes "$@"
        ;;
    deploy)
        echo "🚀 Deploying to production..."
        ./scripts/deploy-prod.sh
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -z "$1" ]; then
            show_help
        else
            echo "❌ Unknown command: $1"
            echo ""
            show_help
            exit 1
        fi
        ;;
esac
EOF

chmod +x dev-workflow.sh

# Step 14: Show next steps
echo ""
echo "🎉 Git repository setup complete for RAG-GCS!"
echo ""
echo "📋 Next steps:"
echo "1. 🔧 Configure .env file with your values:"
echo "   cp .env.example .env"
echo "   # Edit .env with your actual configuration"
echo ""
echo "2. 📁 Add your service-account.json file"
echo "   # Place in root directory (already in .gitignore)"
echo ""
echo "3. 🧪 Test locally:"
echo "   ./dev-workflow.sh run"
echo ""
echo "4. 🚀 For future commits, use:"
echo "   ./commit-changes.sh \"Your commit message\""
echo "   # or"
echo "   ./dev-workflow.sh commit \"Your commit message\""
echo ""
echo "🛠️  Development Commands:"
echo "   ./dev-workflow.sh setup    # Setup development environment"
echo "   ./dev-workflow.sh run      # Run the server"
echo "   ./dev-workflow.sh sync     # Test Google Drive sync"
echo "   ./dev-workflow.sh status   # Show repository status"
echo "   ./dev-workflow.sh help     # Show all commands"
echo ""
echo "📁 Repository structure:"
tree -a -I '.git|__pycache__|venv|.env'
echo ""
echo "🔗 Your repository: https://github.com/jasonwu1993/RAG-GCS"
echo ""
echo "🎊 Your Clair backend is ready for development!"
EOF

chmod +x git_setup_script.sh