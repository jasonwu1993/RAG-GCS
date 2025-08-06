#!/bin/bash
echo "🚀 Deploying RAG Clair Modular Backend to Google Cloud Run..."

# Set project ID (use current gcloud config)
PROJECT_ID=$(gcloud config get-value project)
echo "📋 Using project: $PROJECT_ID"

# Set image name
IMAGE_NAME="gcr.io/${PROJECT_ID}/rag-gcs"
echo "🐳 Image: $IMAGE_NAME"

# Build image
echo "🔨 Building Docker image..."
docker build -t ${IMAGE_NAME} .

# Configure Docker for GCR
echo "🔐 Configuring Docker authentication..."
gcloud auth configure-docker --quiet

# Push to Google Container Registry
echo "📤 Pushing to Google Container Registry..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run with all environment variables
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy rag-gcs \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --timeout 300 \
  --port 8080 \
  --set-env-vars GCP_PROJECT_ID=${PROJECT_ID} \
  --set-env-vars GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json

# Get the service URL
SERVICE_URL=$(gcloud run services describe rag-gcs --region=us-central1 --format='value(status.url)')
echo ""
echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo "🔗 Health check: $SERVICE_URL/health"
echo ""
echo "📝 Next steps:"
echo "1. Update frontend API_CONFIG.BASE_URL to: $SERVICE_URL"
echo "2. Test the health endpoint"
echo "3. Verify Vertex AI integration"
