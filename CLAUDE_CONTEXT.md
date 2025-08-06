# CLAUDE_CONTEXT.md - Essential Context for Claude Code Sessions

**This is a focused context file for Claude Code sessions. Always read this when troubleshooting complex issues.**

## 🏗️ PROJECT IDENTIFIERS (MEMORIZE THIS!)

```bash
# SAME PROJECT - Different Identifiers
Project ID: rag-backend-467204          # Use for ALL gcloud commands
Project Number: 718538538469            # Used in service URLs only

# Service Name
SERVICE_NAME: rag-gcs                   # NOT clair-rag

# URLs
Production URL: https://rag-gcs-718538538469.us-central1.run.app
```

## 📋 ESSENTIAL CONFIGURATION

```bash
# Google Cloud
GCP_PROJECT_ID=rag-backend-467204
GCP_REGION=us-central1
GCS_BUCKET_NAME=rag-clair-2025

# Vertex AI Search
INDEX_ENDPOINT_ID=1251545498595098624
DEPLOYED_INDEX_ID=rag_index_1753602198270
INDEX_ID=3923640229067489280

# Google Drive
GOOGLE_DRIVE_FOLDER_ID=1pMiyyfk8hEoVVSsxMmRmobe6dmdm5sjI
GOOGLE_SERVICE_ACCOUNT_FILE=gcp-credentials.json

# Service Account
rag-backend-runner@rag-backend-467204.iam.gserviceaccount.com
```

## 🚀 DEPLOYMENT COMMANDS

```bash
# Standard deployment (RELIABLE - ignore timeout messages)
gcloud run deploy rag-gcs \
  --source . \
  --platform managed \
  --region us-central1 \
  --project rag-backend-467204 \
  --allow-unauthenticated \
  --cpu-boost \
  --memory 4Gi \
  --timeout 3600 \
  --cpu 2 \
  --concurrency 10 \
  --max-instances 3 \
  --port 8080 \
  --set-env-vars "OPENAI_API_KEY=$(gcloud secrets versions access latest --secret=openai-api-key --project=718538538469),GCP_PROJECT_ID=rag-backend-467204,GCS_BUCKET_NAME=rag-clair-2025,GOOGLE_DRIVE_FOLDER_ID=1pMiyyfk8hEoVVSsxMmRmobe6dmdm5sjI,DEPLOYED_INDEX_ID=rag_index_1753602198270,INDEX_ENDPOINT_ID=1251545498595098624,ENVIRONMENT=production,DEBUG=false,GPT_MODEL=gpt-4o-2024-08-06,EMBED_MODEL=text-embedding-3-small,MAX_TOKENS=2000,TEMPERATURE=0.9,SIMILARITY_THRESHOLD=0.9,TOP_K=3,GCP_REGION=us-central1"

# Check if deployment succeeded (after timeout)
gcloud run revisions list --service=rag-gcs --region=us-central1 --project=rag-backend-467204 --limit=3

# Route traffic if needed
LATEST_REVISION=$(gcloud run revisions list --service=rag-gcs --region=us-central1 --project=rag-backend-467204 --limit=1 --format="value(REVISION)")
gcloud run services update-traffic rag-gcs --to-revisions=$LATEST_REVISION=100 --region=us-central1 --project=rag-backend-467204
```

## 🧪 TESTING COMMANDS

```bash
# Health check
curl "https://rag-gcs-718538538469.us-central1.run.app/health"

# Test Chinese language consistency
curl -X POST "https://rag-gcs-718538538469.us-central1.run.app/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "您都代理哪些产品", "session_id": "test"}'
```

## ⚠️ CRITICAL REMINDERS

1. **Deployment Timeouts**: NOT failures! Check revision list, deployment likely succeeded
2. **Project Confusion**: Always use Project ID `rag-backend-467204` for gcloud commands
3. **Service Name**: Use `rag-gcs` (NOT clair-rag) 
4. **Production URL**: Uses project number `718538538469` in domain
5. **Environment**: .env for LOCAL ONLY, production uses Google Secret Manager
6. **OpenAI Key**: NEVER in .env for production, use: `$(gcloud secrets versions access latest --secret=openai-api-key)`

## ✅ RESOLVED ISSUES

1. **Deployment Reliability**: Background initialization in main_modular.py
2. **Language Consistency**: Lazy AI service initialization
3. **Project Confusion**: Clear documentation above
4. **ai_service Errors**: get_ai_service() with fallbacks
5. **Version Inconsistency**: Single VERSION variable pattern implemented
6. **Circular Imports**: Simplified imports and GPT-native architecture

## 🎯 SUCCESS VALIDATION

- New revision created → Check with `gcloud run revisions list`
- Health endpoint returns 200 → Test with curl
- Chinese queries return Chinese → Test with example above
- No "technical difficulties" → AI service working
- Version consistency → `/health` and `/` return same version
- GPT-native hotkeys → Dynamic, context-aware suggestions working

## 🛠️ DEPLOYMENT BEST PRACTICES & TROUBLESHOOTING

### **Preferred Deployment Method**
```bash
# BEST: Use --source . (atomic build+deploy)
gcloud run deploy rag-gcs --source . --platform managed --region us-central1 --project rag-backend-467204

# AVOID: Separate build + deploy (requires manual traffic routing)
gcloud builds submit --tag gcr.io/rag-backend-467204/rag-gcs:v6.x
gcloud run deploy rag-gcs --image gcr.io/rag-backend-467204/rag-gcs:v6.x
```

### **Version Management Pattern**
```python
# ✅ CORRECT: Single source of truth
# main_modular.py
VERSION = "6.x-DESCRIPTION"

# core.py  
try:
    from main_modular import VERSION, BUILD_DATE
except ImportError:
    VERSION = "***"  # Generic fallback only
```

### **Dockerfile Best Practices**
```dockerfile
# ✅ CORRECT: Copy all, then remove unwanted
COPY . ./
RUN rm -rf rag-frontend-vercel/ tests/ *.md src/ || true

# ❌ AVOID: Individual file copies (misses dependencies)
COPY main_modular.py .
COPY config.py .
```

### **Common Issues & Solutions**

**1. Version Inconsistency**
- **Symptom**: Frontend shows different version than expected
- **Cause**: Multiple version definitions in different files
- **Solution**: Single VERSION variable with import pattern
- **Test**: `curl /health` and `curl /` should return same version

**2. Deployment Timeouts**
- **Symptom**: gcloud deploy times out after 2-3 minutes
- **Reality**: Deployment often succeeds despite timeout message
- **Action**: Check `gcloud run revisions list` to verify new revision
- **Note**: Cloud Run build timeout ≠ deployment failure

**3. Circular Import Errors**
- **Symptom**: `cannot import name 'X' from 'X'` errors
- **Cause**: Complex cross-module dependencies
- **Solution**: Simplify imports, use lazy loading, GPT-native patterns
- **Architecture**: Let OpenAI handle intelligence, minimize custom processing

**4. Traffic Not Routing**
- **Symptom**: New revision created but old version still serving
- **Cause**: Traffic not automatically routed to latest revision
- **Solution**: Use `--source .` deployment (auto-routes) or manual traffic update
- **Command**: `gcloud run services update-traffic rag-gcs --to-revisions=$LATEST=100`

**5. Cloud Build Not Triggering**
- **Symptom**: Source uploaded but no build starts
- **Cause**: Storage quota issues, permissions, or caching
- **Solution**: Clear storage buckets, use direct `gcloud builds submit`
- **Prevention**: Monitor storage usage, use deploy.sh script

### **Production Deployment Checklist**
- [ ] VERSION updated in main_modular.py
- [ ] Dockerfile cache-bust comment updated  
- [ ] Use `./deploy.sh` or `gcloud run deploy --source .`
- [ ] Verify new revision created: `gcloud run revisions list`
- [ ] Test version consistency: `curl /health` and `curl /`
- [ ] Verify GPT functionality: Test /chat/ask with hotkeys
- [ ] Check logs for errors: `gcloud logging read`

### **Emergency Deployment Recovery**
```bash
# If deployment fails completely
1. Check last working revision: gcloud run revisions list
2. Route traffic back: gcloud run services update-traffic rag-gcs --to-revisions=rag-gcs-XXXXX-yyy=100
3. Debug locally: docker build . && docker run -p 8080:8080 <image>
4. Fix issues and redeploy with cache bust
```

---
**For detailed information, see QUICK_START.md**