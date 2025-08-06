#\!/bin/bash

# DEPLOYMENT SCRIPT - Always uses correct service names from CLAUDE_CONTEXT.md
# This prevents any mistakes with service names

# FIXED CONSTANTS - DO NOT CHANGE (from CLAUDE_CONTEXT.md)
SERVICE_NAME="rag-gcs"
PROJECT_ID="rag-backend-467204" 
PROJECT_NUMBER="718538538469"
REGION="us-central1"

echo "🚀 DEPLOYING TO CORRECT SERVICE"
echo "Service: $SERVICE_NAME"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# COMPLETE DEPLOYMENT COMMAND FROM CLAUDE_CONTEXT.md
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --cpu-boost \
  --memory 4Gi \
  --timeout 3600 \
  --cpu 2 \
  --concurrency 10 \
  --max-instances 3 \
  --port 8080 \
  --set-env-vars "OPENAI_API_KEY=$(gcloud secrets versions access latest --secret=openai-api-key --project=$PROJECT_NUMBER),GCP_PROJECT_ID=$PROJECT_ID,GCS_BUCKET_NAME=rag-clair-2025,GOOGLE_DRIVE_FOLDER_ID=1pMiyyfk8hEoVVSsxMmRmobe6dmdm5sjI,DEPLOYED_INDEX_ID=rag_index_1753602198270,INDEX_ENDPOINT_ID=1251545498595098624,ENVIRONMENT=production,DEBUG=false,GPT_MODEL=gpt-4o-2024-08-06,EMBED_MODEL=text-embedding-3-small,MAX_TOKENS=2000,TEMPERATURE=0.9,SIMILARITY_THRESHOLD=0.9,TOP_K=3,GCP_REGION=$REGION"

echo ""
echo "📋 Checking deployment status (deployments often timeout but succeed)..."
sleep 15

# Get the latest revision
LATEST_REVISION=$(gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --project=$PROJECT_ID --limit=1 --format="value(REVISION)")
echo "📦 Latest revision: $LATEST_REVISION"

# Route 100% traffic to latest revision  
echo "🔄 Routing traffic to latest revision..."
gcloud run services update-traffic $SERVICE_NAME --to-revisions=$LATEST_REVISION=100 --region=$REGION --project=$PROJECT_ID

echo ""
echo "📋 Final revision status:"
gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --project=$PROJECT_ID --limit=3

echo ""
echo "✅ Testing deployed service..."
sleep 5
curl -s "https://$SERVICE_NAME-$PROJECT_NUMBER.$REGION.run.app/health" | python3 -c "
import json, sys
try:
    data=json.loads(sys.stdin.read())
    print(f'Version: {data.get(\"version\", \"unknown\")}')
    print(f'Status: {data.get(\"status\", \"unknown\")}')
    print(f'Timestamp: {data.get(\"timestamp\", \"unknown\")}')
except:
    print('Health check failed or invalid JSON')
"

echo ""
echo "🎯 Deployment completed\!"
SCRIPT_END < /dev/null