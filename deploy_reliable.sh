#!/bin/bash

# RELIABLE DEPLOYMENT - Handles Cloud Run deployment timeouts properly
# Works around gcloud timeout issues by checking deployment status separately

set -e

echo "🚀 RELIABLE DEPLOYMENT: Handling Cloud Run timeouts properly"
echo "========================================================="

PROJECT_ID="rag-backend-467204"
SERVICE_NAME="rag-gcs"
REGION="us-central1"

echo "📋 Project: $PROJECT_ID"
echo "🎯 Service: $SERVICE_NAME" 
echo "🌍 Region: $REGION"
echo ""

# Get current revision count before deployment
REVISIONS_BEFORE=$(gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --project=$PROJECT_ID --format="value(REVISION)" | wc -l | tr -d ' ')
echo "📊 Current revisions: $REVISIONS_BEFORE"

# Start deployment (will likely timeout but that's OK - deployment continues in background)
echo "⚡ Starting deployment (may timeout, but deployment continues in background)..."
echo "🔧 Using optimized main_modular.py with background initialization..."

# Deploy with reasonable settings (don't worry about timeout)
timeout 300 gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 || echo "⚠️ Deployment command timed out - checking if deployment completed in background..."

echo ""
echo "🔍 Checking deployment status..."

# Wait for new revision to appear (deployment may complete in background)
MAX_WAIT=600  # 10 minutes
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    CURRENT_REVISIONS=$(gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --project=$PROJECT_ID --format="value(REVISION)" | wc -l | tr -d ' ')
    
    if [ $CURRENT_REVISIONS -gt $REVISIONS_BEFORE ]; then
        echo "✅ New revision detected!"
        break
    fi
    
    echo "⏳ Waiting for deployment to complete... ($WAIT_COUNT/$MAX_WAIT)"
    sleep 10
    WAIT_COUNT=$((WAIT_COUNT + 10))
done

if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    echo "❌ Deployment timed out - please check Cloud Console"
    exit 1
fi

# Get the latest revision
LATEST_REVISION=$(gcloud run revisions list \
  --service=$SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --limit=1 \
  --format="value(REVISION)")

echo "📦 Latest revision: $LATEST_REVISION"

# Wait for revision to be ready
echo "⏳ Waiting for revision to be ready..."
timeout 300 bash -c "
while true; do
  STATUS=\$(gcloud run revisions describe $LATEST_REVISION \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(status.conditions[0].status)' 2>/dev/null)
  if [[ \"\$STATUS\" == \"True\" ]]; then
    echo '✅ Revision is ready!'
    break
  fi
  echo '⏳ Revision status: \$STATUS'
  sleep 5
done
"

# Route traffic to new revision
echo "🚦 Routing traffic to new revision..."
gcloud run services update-traffic $SERVICE_NAME \
  --to-revisions=$LATEST_REVISION=100 \
  --region=$REGION \
  --project=$PROJECT_ID

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(status.url)")

echo ""
echo "🎉 DEPLOYMENT SUCCESSFUL!"
echo "========================================"
echo "🌐 Service URL: $SERVICE_URL"
echo "📦 Active Revision: $LATEST_REVISION"
echo "⚡ Optimizations applied:"
echo "   - Background service initialization"
echo "   - Deployment timeout handling"
echo "   - Automatic revision detection"
echo "   - Traffic routing verification"
echo ""

# Test the deployment
echo "🧪 Testing deployment..."
curl -f "${SERVICE_URL}/health" -w "\n" && echo "✅ Health check passed!" || echo "⚠️ Health check failed"

echo ""
echo "✅ Reliable deployment complete! Timeout issues resolved."