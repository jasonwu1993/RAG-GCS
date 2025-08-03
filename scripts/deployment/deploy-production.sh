#!/bin/bash
# Production deployment script for Clair RAG System

echo "🚀 Deploying Clair RAG System to Production..."

# Configuration
PROJECT_ID="rag-backend-467204"
SERVICE_NAME="clair-rag"
REGION="us-central1"

# Set Google Cloud project
gcloud config set project $PROJECT_ID

echo "📊 Deployment Configuration:"
echo "  - Project: $PROJECT_ID"
echo "  - Service: $SERVICE_NAME"
echo "  - Region: $REGION"
echo "  - Source: Current directory"

# Build and deploy
echo "🔨 Building and deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --cpu-boost \
  --memory 2Gi \
  --timeout 1000 \
  --cpu 2 \
  --concurrency 10 \
  --max-instances 3 \
  --port 8080 \
  --set-env-vars "OPENAI_API_KEY=$(gcloud secrets versions access latest --secret=openai-api-key --project=718538538469),GCP_PROJECT_ID=rag-backend-467204,GCS_BUCKET_NAME=rag-clair-2025,GOOGLE_DRIVE_FOLDER_ID=1pMiyyfk8hEoVVSsxMmRmobe6dmdm5sjI,DEPLOYED_INDEX_ID=rag_index_1753602198270,INDEX_ENDPOINT_ID=1251545498595098624,ENVIRONMENT=production"

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
    
    echo "🌐 Service URL: $SERVICE_URL"
    echo "📊 Health Check: $SERVICE_URL/health"
    echo "📚 API Docs: $SERVICE_URL/docs"
    
    # Test deployment
    echo "🧪 Testing deployment..."
    curl -f "$SERVICE_URL/health" > /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Health check passed!"
    else
        echo "❌ Health check failed!"
        exit 1
    fi
    
    echo "🎉 Production deployment complete!"
else
    echo "❌ Deployment failed!"
    exit 1
fi