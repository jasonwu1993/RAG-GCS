# Enhanced RAG Clair System - Graceful Startup for Cloud Run
"""
Cloud Run compatible version that handles service initialization failures gracefully
"""

import os
import asyncio
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback

# System identification
VERSION = "6.0-GRACEFUL-STARTUP"
BUILD_DATE = "2025-08-03"

# Global state for service availability
service_availability = {
    "storage": False,
    "drive": False,
    "vertex_ai": False,
    "openai": False,
    "startup_errors": []
}

print(f"🚀 Starting Enhanced RAG Clair System {VERSION} - Built {BUILD_DATE}")
print("🏗️ Cloud Run Compatible with Graceful Service Initialization")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced lifespan management with graceful error handling"""
    print("🔧 Initializing Enhanced RAG Clair System...")
    
    try:
        # Try to initialize services, but don't fail if they're not available
        from shared.utils.core_utils import initialize_all_services
        initialization_results = initialize_all_services()
        
        print("📊 Service Initialization Results:")
        for service, status in initialization_results.items():
            status_icon = "✅" if status else "⚠️"
            service_availability[service] = status
            print(f"   {status_icon} {service}: {'OK' if status else 'UNAVAILABLE'}")
            
    except Exception as e:
        error_msg = f"Service initialization error: {str(e)}"
        service_availability["startup_errors"].append(error_msg)
        print(f"⚠️ {error_msg}")
        print("🔄 Continuing with limited functionality...")
    
    # Try to start auto-sync if available
    try:
        if service_availability.get("drive", False):
            print("🔄 Starting auto-sync background task...")
            from api.v1.routes.documents_router import auto_sync_loop
            asyncio.create_task(auto_sync_loop())
        else:
            print("⚠️ Auto-sync disabled - Google Drive service unavailable")
    except Exception as e:
        service_availability["startup_errors"].append(f"Auto-sync setup error: {str(e)}")
        print(f"⚠️ Auto-sync setup failed: {e}")
    
    print("🎯 Enhanced RAG Clair System ready for requests!")
    yield
    
    print("🛑 Shutting down Enhanced RAG Clair System...")

# Create FastAPI app with graceful lifespan management
app = FastAPI(
    title="Enhanced RAG Clair System - Cloud Run Ready",
    description="SOTA Life Insurance RAG System with Graceful Service Initialization",
    version=VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to include routers, but handle gracefully if they fail
routers_loaded = {"documents": False, "search": False, "chat": False, "admin": False}

try:
    from api.v1.routes.documents_router import router as documents_router
    app.include_router(documents_router)
    routers_loaded["documents"] = True
    print("✅ Documents router loaded")
except Exception as e:
    print(f"⚠️ Documents router failed to load: {e}")

try:
    from api.v1.routes.search_router import router as search_router  
    app.include_router(search_router)
    routers_loaded["search"] = True
    print("✅ Search router loaded")
except Exception as e:
    print(f"⚠️ Search router failed to load: {e}")

try:
    from api.v1.routes.chat_router import router as chat_router
    app.include_router(chat_router)
    routers_loaded["chat"] = True
    print("✅ Chat router loaded")
except Exception as e:
    print(f"⚠️ Chat router failed to load: {e}")

try:
    from api.v1.routes.admin_router import router as admin_router
    app.include_router(admin_router)
    routers_loaded["admin"] = True
    print("✅ Admin router loaded")
except Exception as e:
    print(f"⚠️ Admin router failed to load: {e}")

# Enhanced root endpoint with service status
@app.get("/")
async def enhanced_root():
    """Enhanced root endpoint with comprehensive system information"""
    return {
        "message": "Enhanced RAG Clair System - Cloud Run Ready",
        "version": VERSION,
        "build_date": BUILD_DATE,
        "status": "running",
        "container_health": "healthy",
        
        # Service availability
        "services": service_availability,
        "routers_loaded": routers_loaded,
        
        # Environment info
        "environment": {
            "mode": os.getenv("ENVIRONMENT", "unknown"),
            "project_id": os.getenv("GCP_PROJECT_ID", "not_set"),
            "region": os.getenv("GCP_REGION", "not_set")
        },
        
        "timestamp": datetime.utcnow().isoformat()
    }

# Enhanced health endpoint
@app.get("/health")
async def enhanced_health():
    """Enhanced health check that always reports healthy if container is running"""
    return {
        "status": "healthy",  # Always healthy if the container responds
        "version": VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "container_status": "running",
        "services": service_availability,
        "routers": routers_loaded
    }

# Service status endpoint
@app.get("/service-status")
async def get_service_status():
    """Detailed service status information"""
    return {
        "services": service_availability,
        "routers": routers_loaded,
        "environment_variables": {
            "GCP_PROJECT_ID": bool(os.getenv("GCP_PROJECT_ID")),
            "GCS_BUCKET_NAME": bool(os.getenv("GCS_BUCKET_NAME")),
            "INDEX_ENDPOINT_ID": bool(os.getenv("INDEX_ENDPOINT_ID")),
            "DEPLOYED_INDEX_ID": bool(os.getenv("DEPLOYED_INDEX_ID")),
            "GOOGLE_DRIVE_FOLDER_ID": bool(os.getenv("GOOGLE_DRIVE_FOLDER_ID")),
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY"))
        },
        "startup_errors": service_availability.get("startup_errors", []),
        "timestamp": datetime.utcnow().isoformat()
    }

# Fallback endpoints for when routers fail to load
@app.get("/fallback-chat")
async def fallback_chat():
    """Fallback chat endpoint when full chat service is unavailable"""
    return {
        "message": "Chat service is temporarily unavailable",
        "status": "limited_functionality",
        "available_services": [k for k, v in service_availability.items() if v],
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 8080))
        print(f"🌟 Starting Enhanced RAG Clair System on port {port}")
        print(f"🔗 Health check: http://localhost:{port}/health")
        print(f"📊 Service status: http://localhost:{port}/service-status")
        
        uvicorn.run(
            "main_graceful:app",
            host="0.0.0.0", 
            port=port,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Failed to start Enhanced RAG Clair System: {e}")
        traceback.print_exc()