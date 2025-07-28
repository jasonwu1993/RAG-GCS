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
cd clair-backend

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
docker build -t clair-backend .

# Run container
docker run -p 8000:8000 --env-file .env clair-backend
```

## 🚀 Production Deployment

### Google Cloud Run
```bash
# Deploy to Cloud Run
gcloud run deploy clair-backend \
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
