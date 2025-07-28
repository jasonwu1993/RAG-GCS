#!/bin/bash
echo "🚀 Deploying to production..."

# Build and push Docker image
PROJECT_ID=${GCP_PROJECT_ID}
IMAGE_NAME="gcr.io/${PROJECT_ID}/clair-backend"

# Build image
docker build -t ${IMAGE_NAME} .

# Push to Google Container Registry
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
gcloud run deploy clair-backend \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=${GCP_PROJECT_ID} \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10

echo "✅ Deployment complete!"
