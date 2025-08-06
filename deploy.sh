#!/bin/bash

# Automated Cloud Run Deployment with Traffic Routing
# Fixes the manual traffic switching issue

set -e  # Exit on any error

# PRODUCTION PROJECT: Where the actual Cloud Run service lives (use project ID, not number)
PROD_PROJECT_ID="rag-backend-467204"  
# Same project for both resources (Project ID: rag-backend-467204, Project Number: 718538538469)
SA_PROJECT_ID="rag-backend-467204"
SERVICE_NAME="rag-gcs"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROD_PROJECT_ID/$SERVICE_NAME"

echo "🚀 Starting automated deployment for $SERVICE_NAME"
echo "📦 Production Project: $PROD_PROJECT_ID" 
echo "🔐 Service Account Project: $SA_PROJECT_ID"
echo "🌍 Region: $REGION"

# Deploy directly from source (modern approach)
echo "🚀 Deploying new revision to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --project $PROD_PROJECT_ID \
    --allow-unauthenticated \
    --cpu-boost \
    --memory 4Gi \
    --timeout 1000 \
    --cpu 2 \
    --concurrency 10 \
    --max-instances 3 \
    --port 8080 \
    --no-traffic \
    --set-env-vars "OPENAI_API_KEY=$(gcloud secrets versions access latest --secret=openai-api-key --project=718538538469),GCP_PROJECT_ID=rag-backend-467204,GCS_BUCKET_NAME=rag-clair-2025,GOOGLE_DRIVE_FOLDER_ID=1pMiyyfk8hEoVVSsxMmRmobe6dmdm5sjI,DEPLOYED_INDEX_ID=rag_index_1753602198270,INDEX_ENDPOINT_ID=1251545498595098624,ENVIRONMENT=production,DEBUG=false,GPT_MODEL=gpt-4o-2024-08-06,EMBED_MODEL=text-embedding-3-small,MAX_TOKENS=2000,TEMPERATURE=0.3,SIMILARITY_THRESHOLD=0.9,TOP_K=3,GCP_REGION=us-central1"

echo "✅ New revision deployed successfully"

# Step 3: Get the latest revision name and switch traffic
echo "🔄 Switching 100% traffic to new revision..."
LATEST_REVISION=$(gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --project=$PROD_PROJECT_ID --limit=1 --format="value(metadata.name)")
echo "📝 Latest revision: $LATEST_REVISION"

gcloud run services update-traffic $SERVICE_NAME \
    --to-revisions=$LATEST_REVISION=100 \
    --region=$REGION \
    --project=$PROD_PROJECT_ID

echo "✅ Traffic successfully switched to new revision"

# Step 4: Verify deployment
echo "✅ Verifying deployment..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --project $PROD_PROJECT_ID --format="value(status.url)")
echo "🌐 Service URL: $SERVICE_URL"

# Test the health endpoint
echo "🔍 Testing health endpoint..."
curl -f "$SERVICE_URL/health" | jq '{version: .version, status: .status}' || echo "⚠️ Health check failed"

# Test the documents endpoint  
echo "🔍 Testing documents endpoint..."
curl -f "$SERVICE_URL/documents/indexed" | jq '{total_indexed: .total_indexed, source: .source}' || echo "⚠️ Documents check failed"

# Test Chinese language fix
echo "🇨🇳 Testing Chinese language consistency fix..."
curl -X POST "$SERVICE_URL/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "您都有什么样的保险", "session_id": "deploy_test_'$(date +%s)'"}' \
  -s | python3 -c "import json, sys; data=json.load(sys.stdin); print('Answer preview:', data.get('answer', 'No answer')[:100] + ('...' if len(data.get('answer', '')) > 100 else '')); print('Language:', '中文' if any('\\u4e00' <= c <= '\\u9fff' for c in data.get('answer', '')) else 'English')" || echo "⚠️ Chinese query test failed"

echo "🎉 Deployment completed successfully!"
echo "📊 Current traffic allocation:"
gcloud run services describe $SERVICE_NAME --region $REGION --project $PROD_PROJECT_ID --format="table(spec.traffic[].revisionName,spec.traffic[].percent)"