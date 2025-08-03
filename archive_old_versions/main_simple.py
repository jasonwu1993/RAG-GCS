#!/usr/bin/env python3
"""
Minimal RAG Clair System - Test Deployment
"""

import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# System identification
VERSION = "6.0-MODULAR-PROFESSIONAL-ADVISOR-MINIMAL"
BUILD_DATE = "2025-08-03"

print(f"🚀 Starting Minimal RAG Clair System {VERSION} - Built {BUILD_DATE}")
print("🎯 Testing deployment pipeline with correct environment variables")

# Environment variable check
env_vars = {
    "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID", "NOT_SET"),
    "GCS_BUCKET_NAME": os.getenv("GCS_BUCKET_NAME", "NOT_SET"), 
    "INDEX_ENDPOINT_ID": os.getenv("INDEX_ENDPOINT_ID", "NOT_SET"),
    "DEPLOYED_INDEX_ID": os.getenv("DEPLOYED_INDEX_ID", "NOT_SET"),
    "GOOGLE_DRIVE_FOLDER_ID": os.getenv("GOOGLE_DRIVE_FOLDER_ID", "NOT_SET"),
}

print("📊 Environment Variables:")
for key, value in env_vars.items():
    print(f"   {key}: {value}")

# Load system prompt
try:
    with open("Clair-sys-prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()
        print(f"✅ System prompt loaded: {len(system_prompt)} characters")
        CLAIR_GREETING = "Hello, I'm Clair, your trusted and always-on AI financial advisor in wealth planning. How may I assist you today?"
except Exception as e:
    print(f"❌ System prompt loading failed: {e}")
    CLAIR_GREETING = "Hello! I'm Clair, your AI assistant. How may I help you?"

# Create minimal FastAPI app
app = FastAPI(
    title="RAG Clair System - Minimal Test",
    description="Minimal deployment test for professional financial advisor",
    version=VERSION
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Clair System - Minimal Test Deployment",
        "version": VERSION,
        "status": "running",
        "environment_variables": env_vars,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")  
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "container_status": "running",
        "environment_check": {
            "all_vars_set": all(v != "NOT_SET" for v in env_vars.values()),
            "critical_vars": {k: v for k, v in env_vars.items() if v != "NOT_SET"}
        }
    }

@app.get("/chat/greeting")
async def get_greeting():
    """Get Clair's greeting message"""
    return {
        "greeting": CLAIR_GREETING,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"🌟 Starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)