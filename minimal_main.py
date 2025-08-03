#!/usr/bin/env python3
"""
Minimal Clair Backend for Cloud Run Deployment Testing
This version starts quickly without complex initialization
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Create minimal FastAPI app
app = FastAPI(
    title="Clair RAG System - Minimal Mode",
    description="Minimal version for deployment testing",
    version="6.0-MINIMAL"
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
    """Basic root endpoint"""
    return {
        "message": "Clair RAG System - Minimal Mode",
        "status": "running",
        "version": "6.0-MINIMAL",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "port": os.getenv("PORT", "8080")
    }

@app.get("/health")
async def health():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "6.0-MINIMAL"
    }

@app.get("/env-check")
async def env_check():
    """Check environment variables"""
    env_vars = {
        "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID", "missing"),
        "GCS_BUCKET_NAME": os.getenv("GCS_BUCKET_NAME", "missing"),
        "INDEX_ENDPOINT_ID": os.getenv("INDEX_ENDPOINT_ID", "missing"),
        "DEPLOYED_INDEX_ID": os.getenv("DEPLOYED_INDEX_ID", "missing"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "missing"),
        "PORT": os.getenv("PORT", "missing"),
        "OPENAI_API_KEY": "set" if os.getenv("OPENAI_API_KEY") else "missing"
    }
    
    return {
        "environment_variables": env_vars,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Starting Clair RAG System - Minimal Mode on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )