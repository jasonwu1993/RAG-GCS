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

# Step 2: Deploy new revision (without traffic initially)
echo "🚀 Deploying new revision to Cloud Run (no traffic initially)..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --cpu-boost \
    --memory 4Gi \
    --timeout 1000 \
    --cpu 2 \
    --concurrency 10 \
    --max-instances 3 \
    --port 8080 \
    --no-traffic \
    --set-env-vars "OPENAI_API_KEY=$(gcloud secrets versions access latest --secret=openai-api-key --project=718538538469),GCP_PROJECT_ID=rag-backend-467204,GCS_BUCKET_NAME=rag-clair-2025,GOOGLE_DRIVE_FOLDER_ID=1pMiyyfk8hEoVVSsxMmRmobe6dmdm5sjI,DEPLOYED_INDEX_ID=rag_index_1753602198270,INDEX_ENDPOINT_ID=1251545498595098624,ENVIRONMENT=production,DEBUG=false,GPT_MODEL=gpt-4o-2024-08-06,EMBED_MODEL=text-embedding-3-small,MAX_TOKENS=2000,TEMPERATURE=0.9,SIMILARITY_THRESHOLD=0.75,TOP_K=3,GCP_REGION=us-central1"

echo "✅ New revision deployed successfully"

# Step 3: Get the latest revision name and switch traffic
echo "🔄 Switching 100% traffic to new revision..."
LATEST_REVISION=$(gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --project=$PROJECT_ID --limit=1 --format="value(metadata.name)")
echo "📝 Latest revision: $LATEST_REVISION"

gcloud run services update-traffic $SERVICE_NAME \
    --to-revisions=$LATEST_REVISION=100 \
    --region=$REGION \
    --project=$PROJECT_ID

echo "✅ Traffic successfully switched to new revision"

# Step 4: Verify deployment
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