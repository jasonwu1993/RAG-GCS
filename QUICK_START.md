# Clair RAG Quick Start Guide

## 🚨 UPDATED DIRECTORY STRUCTURE 

**NEW CLEAN ENTERPRISE STRUCTURE:**

```
clair-rag-enterprise/
├── 📁 src/                                    # Source code
│   ├── 📁 api/                               # API layer
│   │   └── 📁 v1/                           # API versioning
│   │       ├── routes/                       # API endpoints
│   │       │   ├── chat_router.py           # Chat endpoints
│   │       │   ├── documents_router.py      # Document management
│   │       │   ├── search_router.py         # Search endpoints
│   │       │   └── admin_router.py          # Admin endpoints
│   │       ├── middleware/                   # API middleware
│   │       └── schemas/                      # Request/response models
│   │
│   ├── 📁 core/                             # Core business logic
│   │   ├── 📁 ai/                          # AI services
│   │   │   ├── intelligence/                # AI intelligence
│   │   │   │   └── ai_service.py           # Enhanced AI service
│   │   │   ├── knowledge/                  # Domain knowledge
│   │   │   ├── learning/                   # Self-learning
│   │   │   └── models/                     # AI models
│   │   ├── 📁 search/                      # Search services
│   │   │   ├── engines/                    # Search engines
│   │   │   │   └── enhanced_search.py      # Enhanced search
│   │   │   ├── indexing/                   # Document indexing
│   │   │   ├── ranking/                    # Result ranking
│   │   │   └── retrieval/                  # Information retrieval
│   │   ├── 📁 data/                        # Data management
│   │   │   ├── processing/                 # Document processing
│   │   │   │   └── enhanced_file_processor.py
│   │   │   ├── storage/                    # Data storage
│   │   │   │   └── cache_service.py        # Caching system
│   │   │   ├── pipeline/                   # ETL operations
│   │   │   └── sync/                       # External sync
│   │   │       └── google_drive_sync.py    # Google Drive sync
│   │   ├── 📁 analytics/                   # Analytics and monitoring
│   │   │   ├── metrics/                    # Performance metrics
│   │   │   ├── monitoring/                 # System monitoring
│   │   │   │   └── performance_monitor.py  # Performance tracking
│   │   │   └── reporting/                  # Analytics reporting
│   │   └── 📁 security/                    # Security services
│   │       ├── authentication/             # Auth services
│   │       ├── authorization/              # Access control
│   │       ├── encryption/                 # Data encryption
│   │       └── audit/                      # Audit logging
│   │
│   ├── 📁 shared/                          # Shared utilities
│   │   ├── 📁 config/                      # Configuration
│   │   │   ├── base_config.py             # Main configuration
│   │   │   └── Clair-sys-prompt.txt       # Clair system prompt
│   │   ├── 📁 utils/                       # Utility functions
│   │   │   └── core_utils.py              # Core utilities
│   │   ├── 📁 exceptions/                  # Custom exceptions
│   │   │   └── error_handler.py           # Error handling
│   │   └── 📁 constants/                   # System constants
│   │
│   ├── 📁 domain/                          # Domain-specific logic
│   │   └── 📁 life_insurance/              # Life insurance domain
│   │       ├── models/                     # Domain models
│   │       ├── services/                   # Domain services
│   │       ├── knowledge/                  # Domain knowledge
│   │       └── workflows/                  # Business workflows
│   │
│   └── main.py                             # Main application
│
├── 📁 tests/                               # Test suites
│   ├── unit/                              # Unit tests
│   ├── integration/                       # Integration tests
│   ├── e2e/                              # End-to-end tests
│   └── performance/                       # Performance tests
│
├── 📁 infrastructure/                      # Infrastructure as code
│   ├── terraform/                         # Terraform configs
│   ├── kubernetes/                        # K8s manifests
│   ├── docker/                           # Docker configs
│   │   ├── Dockerfile                    # Production Dockerfile
│   │   └── docker-compose.yml            # Local development
│   └── scripts/                          # Automation scripts
│
├── 📁 docs/                               # Documentation
│   ├── api/                              # API documentation
│   ├── architecture/                     # Architecture docs
│   ├── domain/                           # Domain documentation
│   ├── deployment/                       # Deployment guides
│   └── user_guides/                      # User documentation
│
├── 📁 data/                               # Data files
│   ├── knowledge_base/                   # Knowledge base
│   ├── training/                         # Training data
│   └── reference/                        # Reference data
│
├── 📁 monitoring/                         # Monitoring configs
│   ├── prometheus/                       # Prometheus configs
│   ├── grafana/                         # Grafana dashboards
│   ├── alerting/                        # Alert configurations
│   └── logging/                         # Logging configurations
│
├── 📁 migrations/                         # Database migrations
│   ├── versions/                         # Migration versions
│   └── seeds/                           # Seed data
│
├── 📁 scripts/                           # Utility scripts
│   ├── development/                      # Development scripts
│   ├── testing/                         # Testing scripts
│   └── deployment/                      # Deployment scripts
│
├── 📁 rag-frontend-vercel/               # Frontend application
│   ├── components/                       # React components
│   │   ├── chat/                        # Chat components
│   │   │   ├── ChatArea.js              # Main chat interface
│   │   │   └── TypingIndicator.js       # Animated typing dots
│   │   ├── layout/                      # Layout components
│   │   ├── sync/                        # Sync components
│   │   └── ui/                          # UI components
│   ├── hooks/                           # React hooks
│   ├── pages/                           # Next.js pages
│   ├── services/                        # API services
│   ├── styles/                          # Styling
│   └── utils/                           # Frontend utilities
│
├── 📄 run_server.py                      # Server runner script
├── 📄 requirements.txt                   # Python dependencies
├── 📄 requirements-dev.txt               # Development dependencies
├── 📄 QUICK_START.md                     # This file
├── 📄 README.md                          # Project overview
├── 📄 CLAUDE.md                          # Claude Code instructions
├── 📄 .env.example                       # Environment template
└── 📄 .gitignore                         # Git ignore rules
```

## 🚀 Quick Start Steps

### 1. **Environment Setup**
```bash
# Clone the repository
git clone <repository-url>
cd clair-rag-enterprise

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### 2. **Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. **Start Development Server**
```bash
# Run from root directory - uses new enterprise structure
python run_server.py

# Alternative: Direct uvicorn (must be in src/ directory)
cd src && uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### 4. **Start Frontend (in separate terminal)**
```bash
cd rag-frontend-vercel
npm install
npm run dev    # Runs on port 3001
```

### 5. **Access Application**
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

## 🏗️ Architecture Overview

### Technology Stack
- **Backend**: FastAPI (Python 3.8+)
- **Frontend**: Next.js (React 18+)
- **AI**: OpenAI GPT-4o + Custom Intelligence
- **Search**: Google Vertex AI + Hybrid Search
- **Storage**: Google Cloud Storage + Caching
- **Deployment**: Google Cloud Run + Docker

### Key Features
- **🤖 Intelligent AI Assistant**: Clair - Expert financial advisor
- **🔍 Hybrid Search**: Vertex AI + Internet + Reasoning
- **⚡ Real-time Chat**: Animated typing indicators
- **📁 Document Management**: Google Drive sync
- **🔒 Enterprise Security**: Authentication + Audit
- **📊 Advanced Analytics**: Performance monitoring
- **🌐 Scalable Architecture**: Microservices ready

## 🔧 Development Commands

**All commands run from root directory:**

### Backend Commands
```bash
# Start development server
python run_server.py

# Run with debug mode
DEBUG=true python run_server.py

# Run specific component tests
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/e2e/

# Format code
black src/
isort src/

# Type checking
mypy src/

# Security scan
bandit -r src/
```

### Frontend Commands
```bash
cd rag-frontend-vercel

npm run dev                    # Start development server (port 3001)
npm run build                  # Build for production
npm run start                  # Start production server
npm run lint                   # Run ESLint
npm test                       # Run Jest tests
npm run test:e2e               # Run Playwright E2E tests
```

### Infrastructure Commands
```bash
# Docker development
docker-compose -f infrastructure/docker/docker-compose.yml up

# Build Docker image
docker build -f infrastructure/docker/Dockerfile -t clair-rag .

# Kubernetes deployment (when ready)
kubectl apply -f infrastructure/kubernetes/
```

## 🔥 Google Cloud Configuration

### Project Setup
```bash
# Set project
gcloud config set project rag-backend-467204

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable drive.googleapis.com
```

### Environment Variables

#### Development (.env)
```bash
# Google Cloud
GCP_PROJECT_ID=rag-backend-467204
GCS_BUCKET_NAME=rag-clair-2025
GOOGLE_DRIVE_FOLDER_ID=1pMiyyfk8hEoVVSsxMmRmobe6dmdm5sjI

# Vertex AI
INDEX_ENDPOINT_ID=1251545498595098624
DEPLOYED_INDEX_ID=rag_index_1753602198270

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Application
DEBUG=true
PORT=8080
ENVIRONMENT=development
```

#### Production (Cloud Run)
```bash
# Deployed automatically via secrets manager
OPENAI_API_KEY=$(gcloud secrets versions access latest --secret=openai-api-key)
GCP_PROJECT_ID=rag-backend-467204
GCS_BUCKET_NAME=rag-clair-2025
# ... other production configs
```

### Database Schema
```yaml
# Google Cloud Storage Structure
rag-clair-2025/
├── documents/           # Original documents
├── chunks/             # Processed text chunks
├── embeddings/         # Vector embeddings
├── metadata/           # Document metadata
└── cache/             # Cached results

# Vertex AI Index
- Index ID: rag_index_1753602198270
- Endpoint ID: 1251545498595098624
- Dimensions: 1536 (text-embedding-3-small)
- Distance: Cosine similarity
```

### Authentication Setup

#### Service Account
```bash
# Create service account
gcloud iam service-accounts create rag-service-account

# Grant permissions
gcloud projects add-iam-policy-binding rag-backend-467204 \
    --member="serviceAccount:rag-service-account@rag-backend-467204.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Download key (development only)
gcloud iam service-accounts keys create service-account.json \
    --iam-account=rag-service-account@rag-backend-467204.iam.gserviceaccount.com
```

## ☁️ Google Cloud Deployment

### Cloud Run Configuration

#### Build and Deploy
```bash
# Deploy directly from source
gcloud run deploy rag-gcs \
  --source . \
  --platform managed \
  --region us-central1 \
  --project rag-backend-467204 \
  --allow-unauthenticated \
  --cpu-boost \
  --memory 2Gi \
  --timeout 1000 \
  --cpu 2 \
  --concurrency 10 \
  --max-instances 3 \
  --port 8080 \
  --set-env-vars "OPENAI_API_KEY=$(gcloud secrets versions access latest --secret=openai-api-key --project=718538538469),GCP_PROJECT_ID=rag-backend-467204,GCS_BUCKET_NAME=rag-clair-2025,GOOGLE_DRIVE_FOLDER_ID=1pMiyyfk8hEoVVSsxMmRmobe6dmdm5sjI,DEPLOYED_INDEX_ID=rag_index_1753602198270,INDEX_ENDPOINT_ID=1251545498595098624, ENVIRONMENT=production,DEBUG=false,GPT_MODEL=gpt-4o,EMBED_MODEL=text-embedding-3-small,MAX_TOKENS=1000,TEMPERATURE=0.3,SIMILARITY_THRESHOLD=0.75,TOP_K=3, GCP_REGION=us-central1"


```

#### Alternative: Docker Deploy
```bash
# Build and push to Container Registry
docker build -f infrastructure/docker/Dockerfile -t gcr.io/rag-backend-467204/clair-rag .
docker push gcr.io/rag-backend-467204/clair-rag

# Deploy from image
gcloud run deploy clair-rag \
  --image gcr.io/rag-backend-467204/clair-rag \
  --platform managed \
  --region us-central1
```

### Environment Variables (Production)
```bash
# Core configuration
GCP_PROJECT_ID=rag-backend-467204
GCS_BUCKET_NAME=rag-clair-2025
ENVIRONMENT=production
PORT=8080

# AI Services
OPENAI_API_KEY=$(gcloud secrets versions access latest --secret=openai-api-key)
INDEX_ENDPOINT_ID=1251545498595098624
DEPLOYED_INDEX_ID=rag_index_1753602198270

# Google Drive
GOOGLE_DRIVE_FOLDER_ID=1pMiyyfk8hEoVVSsxMmRmobe6dmdm5sjI

# Performance
DEBUG=false
LOG_LEVEL=INFO
MAX_WORKERS=4
```

## 📁 Key Directories & Files

### Application Structure
```bash
src/main.py                 # Main FastAPI application
src/api/v1/routes/          # API endpoint definitions
src/core/ai/intelligence/   # AI services and intelligence
src/core/search/engines/    # Search and retrieval engines
src/core/data/storage/      # Data storage and caching
src/shared/config/          # Configuration management
src/shared/utils/           # Shared utility functions
```

### Configuration Files
```bash
src/shared/config/base_config.py      # Main configuration
src/shared/config/Clair-sys-prompt.txt # Clair's system prompt
.env                                   # Environment variables
requirements.txt                       # Python dependencies
run_server.py                         # Server runner script
```

### Frontend Structure
```bash
rag-frontend-vercel/
├── components/chat/ChatArea.js       # Main chat interface
├── components/chat/TypingIndicator.js # Animated typing dots
├── hooks/useChat.js                  # Chat functionality
├── services/apiClient.js             # API client
└── pages/index.js                    # Main application page
```

## 🔗 Essential URLs

- **Development Frontend**: http://localhost:3001
- **Development Backend**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health
- **Production**: https://clair-rag-<hash>-uc.a.run.app

## 🛠️ Essential Scripts

### Development Scripts
```bash
# Quick development start
./scripts/development/start-dev.sh

# Database setup
./scripts/development/setup-db.sh

# Reset development environment
./scripts/development/reset-env.sh
```

### Testing Scripts
```bash
# Run all tests
./scripts/testing/run-all-tests.sh

# Performance testing
./scripts/testing/performance-test.sh

# Security testing
./scripts/testing/security-scan.sh
```

### Deployment Scripts
```bash
# Deploy to staging
./scripts/deployment/deploy-staging.sh

# Deploy to production
./scripts/deployment/deploy-production.sh

# Rollback deployment
./scripts/deployment/rollback.sh
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Problem: ModuleNotFoundError
# Solution: Use run_server.py or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python -m main
```

#### 2. Google Cloud Authentication
```bash
# Problem: Authentication failed
# Solution: Set up application default credentials
gcloud auth application-default login
gcloud config set project rag-backend-467204
```

#### 3. Port Already in Use
```bash
# Problem: Port 8080 already in use
# Solution: Kill process or use different port
lsof -ti:8080 | xargs kill -9
# Or set PORT environment variable
PORT=8081 python run_server.py
```

#### 4. Memory Issues
```bash
# Problem: Out of memory during processing
# Solution: Increase memory limits or optimize batch size
# In .env:
MAX_CHUNK_SIZE=1000
BATCH_SIZE=10
```

#### 5. Vertex AI Connection Issues
```bash
# Problem: Cannot connect to Vertex AI
# Solution: Check endpoint and credentials
gcloud ai endpoints list --region=us-central1
gcloud auth list
```

## ✅ Success Checklist

### Development Setup
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (requirements.txt)
- [ ] Environment variables configured (.env)
- [ ] Google Cloud credentials set up
- [ ] Backend starts without errors (http://localhost:8080/health)
- [ ] Frontend starts and loads (http://localhost:3001)
- [ ] API documentation accessible (/docs)

### Google Cloud Setup
- [ ] Project configured (rag-backend-467204)
- [ ] APIs enabled (Cloud Run, Storage, Vertex AI, Drive)
- [ ] Service account created with proper permissions
- [ ] Vertex AI index accessible
- [ ] Google Drive folder accessible
- [ ] Secrets configured in Secret Manager

### Application Testing
- [ ] Health check returns 200 (/health)
- [ ] Document sync works (/sync_drive)
- [ ] Chat functionality works (/chat/ask)
- [ ] Greeting message displays correctly
- [ ] File listing works (/list_files)
- [ ] Search functionality operational

### Production Deployment
- [ ] Cloud Run service deployed successfully
- [ ] Environment variables set correctly
- [ ] Application accessible via Cloud Run URL
- [ ] No critical errors in logs
- [ ] Performance metrics within acceptable range

## 🚨 IMMEDIATE ACTIONS FOR NEW CHAT SESSIONS

### First Time Setup
1. **Clone and Setup**:
   ```bash
   git clone <repo>
   cd clair-rag-enterprise
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start Services**:
   ```bash
   # Terminal 1: Backend
   python run_server.py
   
   # Terminal 2: Frontend
   cd rag-frontend-vercel && npm run dev
   ```

4. **Verify Setup**:
   ```bash
   curl http://localhost:8080/health
   curl http://localhost:8080/chat/greeting
   ```

### Development Workflow
1. **Code Changes**: Edit files in `src/` directory
2. **Auto-reload**: Server automatically reloads on changes
3. **Testing**: Run tests with `python -m pytest tests/`
4. **Frontend**: Changes auto-reload on http://localhost:3001

### Quick Deploy to Production
```bash
gcloud run deploy clair-rag --source . --region us-central1
```

## 📚 Documentation

### Architecture Documentation
- **ENTERPRISE_FILE_STRUCTURE.md**: Complete project structure
- **IMPLEMENTATION_ROADMAP.md**: 6-phase development plan
- **INTELLIGENT_ROUTING_SYSTEM.md**: Multi-source routing architecture
- **ADVANCED_RAG_FEATURES.md**: SOTA RAG capabilities

### API Documentation
- **Interactive Docs**: http://localhost:8080/docs
- **OpenAPI Spec**: http://localhost:8080/openapi.json
- **Endpoint Reference**: docs/api/endpoints/

### Developer Guides
- **Setup Guide**: This document
- **Component Library**: docs/components/
- **Deployment Guide**: docs/deployment/
- **Troubleshooting**: docs/troubleshooting/

## 🔑 Authentication

**Demo Account**: Use development mode for testing

**Production Access**: 
- Google Cloud IAM for backend
- Service account authentication
- Frontend authentication (when implemented)

## 🌐 Clair Features

### AI Capabilities
- **Expert Financial Advisor**: Specializes in life insurance and wealth planning
- **Intelligent Greeting**: "Hello, I'm Clair, your trusted and always-on AI financial advisor..."
- **Multi-modal Processing**: Text, images, documents, charts
- **Temporal Reasoning**: Time-aware analysis and recommendations
- **Self-learning**: Continuous improvement from user feedback

### Search & Retrieval
- **Hybrid Search**: Vertex AI + Internet + Reasoning
- **Intelligent Routing**: Automatically chooses best information sources
- **Context-aware**: Understands conversation history and user intent
- **Real-time**: Fast response times with animated loading indicators

### Enterprise Features
- **Scalable Architecture**: Microservices-ready design
- **Security**: Enterprise-grade authentication and audit
- **Monitoring**: Comprehensive performance and health monitoring
- **Compliance**: Life insurance industry compliance features

---

**💡 KEY SUCCESS FACTORS:**
1. **Enterprise Structure**: Clean separation of concerns
2. **Intelligent AI**: Clair's expert financial advisor persona
3. **Hybrid Search**: Best of internal knowledge + internet
4. **Real-time UX**: Animated indicators and fast responses
5. **Production Ready**: Docker + Google Cloud deployment
6. **Self-learning**: Continuous improvement capabilities

**📋 For Complete Technical Details**: Reference architecture documentation in `docs/` directory

**🚀 Ready to Start**: Run `python run_server.py` and visit http://localhost:3001