# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Development mode (legacy monolithic)
python main.py

# Production mode (modular architecture - recommended)
python main_modular.py

# With uvicorn
uvicorn main_modular:app --host 0.0.0.0 --port 8080 --reload
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_health.py

# Test with coverage
pytest --cov=. tests/
```

### Docker Development
```bash
# Build image
docker build -t clair-backend .

# Run container
docker run -p 8080:8080 --env-file .env clair-backend

# Deploy to Google Cloud Run
gcloud run deploy clair-backend --source . --platform managed --region us-central1
```

### Environment Setup
- Copy `.env.example` to `.env` and configure all required variables
- Place `service-account.json` in root directory for Google Cloud authentication
- Ensure Google Drive folder permissions are correctly set

## Architecture Overview

### Core System Design
This is a **modular RAG (Retrieval Augmented Generation) system** for financial document analysis with Google Drive integration. The system has evolved from a monolithic architecture (`main.py`) to a modular one (`main_modular.py`) while maintaining 100% backward compatibility.

### Key Architectural Components

#### 1. **Modular Router Architecture**
- **`main_modular.py`**: Main application entry point with FastAPI app setup
- **`documents_router.py`**: Google Drive sync, file management, PDF processing
- **`search_router.py`**: Vector search and document retrieval endpoints
- **`chat_router.py`**: AI chat interface and conversation management  
- **`admin_router.py`**: Administrative functions and system management

#### 2. **Core Services Layer**
- **`core.py`**: Shared utilities, global state management, service initialization
- **`config.py`**: Environment configuration and SOTA life insurance domain knowledge
- **`ai_service.py`**: OpenAI integration, query classification, intelligent routing
- **`google_drive.py`**: Ultra-resilient Google Drive sync with circuit breaker pattern

#### 3. **Data Flow Architecture**
```
Google Drive → Sync Service → PDF Processing → Text Extraction → 
Vector Embedding → Vertex AI Index → Search/Retrieval → AI Response
```

### Service Dependencies

#### External Services
- **Google Cloud Storage**: Document storage and metadata
- **Vertex AI**: Vector indexing and similarity search
- **OpenAI GPT-4**: AI responses and query classification
- **Google Drive API**: Document synchronization

#### Authentication Flow
- Service account credentials for Google Cloud services
- Google Drive readonly scope for document access
- Environment-based API key management

### State Management
- **`GlobalState` class**: Thread-safe state management for sync status, metrics, and performance tracking
- **Sync State**: Tracks Google Drive synchronization status, last sync time, and results
- **Performance Metrics**: Request counting, function call tracking, startup time monitoring

### Critical Integration Points

#### Google Drive Sync
- **Ultra-resilient sync**: Circuit breaker pattern with exponential backoff
- **Metadata tracking**: SHA256 checksums for change detection
- **Background processing**: Async task queue for non-blocking operations
- **Auto-sync**: Scheduled background synchronization every 10 minutes

#### AI Query Processing
- **Intent classification**: Automatic routing based on query analysis
- **Domain expertise**: Enhanced life insurance knowledge base
- **Context-aware responses**: Document-grounded answer generation
- **Feedback loop**: User feedback collection for model improvement

## Development Notes

### Commit Standards
- Use clean, professional commit messages without AI attribution
- No automatic copyright or "Generated with Claude Code" messages
- Focus on describing the actual changes and their business value

### Entry Points
- **Production**: Use `main_modular.py` (modular architecture)
- **Legacy**: `main.py` available for backward compatibility
- **Docker**: Configured to use `main_modular.py` via symlink

### Key Environment Variables
All configuration in `config.py` loaded from environment:
- `GCP_PROJECT_ID`, `GCS_BUCKET_NAME`: Google Cloud configuration
- `INDEX_ENDPOINT_ID`, `DEPLOYED_INDEX_ID`: Vertex AI search index
- `GOOGLE_DRIVE_FOLDER_ID`: Source folder for document sync
- `OPENAI_API_KEY`: AI service authentication

### Router Organization
Each router handles distinct functional domains:
- **Documents**: `/documents/*` - File operations, sync management
- **Search**: `/search/*` - Vector search, document retrieval
- **Chat**: `/chat/*` - AI conversations, query processing  
- **Admin**: `/admin/*` - System administration, health checks

### Error Handling Strategy
- **Circuit breaker pattern**: Prevents cascade failures in Google Drive sync
- **Comprehensive logging**: `log_debug()` function with structured data
- **Graceful degradation**: System continues operating with partial service failures
- **Health monitoring**: `/health` endpoint with dependency checks

### Performance Considerations
- **Async processing**: Background tasks for sync operations
- **Caching strategy**: Local metadata caching to minimize API calls
- **Resource monitoring**: Request counting and performance metrics
- **Thread safety**: Proper locking for shared state management