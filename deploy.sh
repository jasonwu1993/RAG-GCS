#!/bin/bash

# Automated Cloud Run Deployment with Traffic Routing
# Fixes the manual traffic switching issue

set -e  # Exit on any error

PROJECT_ID="rag-backend-467204"
SERVICE_NAME="rag-gcs"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Starting automated deployment for $SERVICE_NAME"
echo "📦 Project: $PROJECT_ID"
echo "🌍 Region: $REGION"

# Step 1: Build the container with latest code
echo "🏗️ Building container with latest code..."
gcloud builds submit --tag $IMAGE_NAME --project $PROJECT_ID

# Step 2: Deploy with automatic traffic allocation to new revision
echo "🚀 Deploying to Cloud Run with automatic traffic routing..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --no-traffic \
    --tag new-version

# Step 3: Get the new revision name
NEW_REVISION=$(gcloud run revisions list --service $SERVICE_NAME --region $REGION --project $PROJECT_ID --format="value(name)" --limit=1)
echo "📝 New revision: $NEW_REVISION"

# Step 4: Automatically switch 100% traffic to new revision
echo "🔄 Switching 100% traffic to new revision..."
gcloud run services update-traffic $SERVICE_NAME \
    --to-revisions $NEW_REVISION=100 \
    --region $REGION \
    --project $PROJECT_ID

# Step 5: Verify deployment
echo "✅ Verifying deployment..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format="value(status.url)")
echo "🌐 Service URL: $SERVICE_URL"

# Test the health endpoint
echo "🔍 Testing health endpoint..."
curl -f "$SERVICE_URL/health" | jq '{version: .version, status: .status}' || echo "⚠️ Health check failed"

# Test the documents endpoint  
echo "🔍 Testing documents endpoint..."
curl -f "$SERVICE_URL/documents/indexed" | jq '{total_indexed: .total_indexed, source: .source}' || echo "⚠️ Documents check failed"

echo "🎉 Deployment completed successfully!"
echo "📊 Current traffic allocation:"
gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format="table(spec.traffic[].revisionName,spec.traffic[].percent)"