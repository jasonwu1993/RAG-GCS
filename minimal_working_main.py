"""
Minimal working main.py to ensure routers are loaded correctly
This file is designed to work in Docker containers with minimal dependencies
"""
import os
import sys
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Version information
VERSION = "6.1-PROFESSIONAL"
BUILD_DATE = "2025-08-03"

print(f"🚀 Starting Enhanced RAG Clair System {VERSION} - Built {BUILD_DATE}")
print(f"📁 Working directory: {os.getcwd()}")
print(f"📋 Python path: {sys.path[:3]}")

# Load system prompt
try:
    with open("Clair-sys-prompt.txt", "r", encoding="utf-8") as f:
        CLAIR_SYSTEM_PROMPT = f.read()
    print("✅ Loaded Clair system prompt successfully")
except:
    CLAIR_SYSTEM_PROMPT = "You are Clair, an AI financial advisor."
    print("⚠️ Using fallback system prompt")

# Load greeting from system prompt (first paragraph)
CLAIR_GREETING = CLAIR_SYSTEM_PROMPT.split('\n\n')[0] if CLAIR_SYSTEM_PROMPT else "Hello! I'm Clair."

# Mock state for minimal functionality
class MinimalState:
    def __init__(self):
        self.startup_time = datetime.utcnow()
        self.request_count = 0
        self.sync_state = {"is_syncing": False, "last_sync": None}
        self.debug_mode = False
        
    def track_request(self, success=True):
        self.request_count += 1

global_state = MinimalState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Minimal lifespan manager"""
    print("🔧 Initializing Enhanced RAG Clair System...")
    yield
    print("🛑 Shutting down Enhanced RAG Clair System...")

# Create FastAPI app
app = FastAPI(
    title="Enhanced RAG Clair System - SOTA Life Insurance AI",
    description="State-of-the-Art Life Insurance RAG System",
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

# Minimal routers with inline definitions
from fastapi import APIRouter

# Documents router
documents_router = APIRouter(prefix="/documents", tags=["documents"])

@documents_router.get("/indexed")
async def list_indexed_documents():
    """List indexed documents - minimal implementation"""
    return {
        "files": [],
        "total": 0,
        "message": "Document service initializing"
    }

@documents_router.get("/sync_status")
async def get_sync_status():
    """Get sync status - minimal implementation"""
    return {
        "is_syncing": False,
        "last_sync": None,
        "next_auto_sync": None,
        "files_found": 0,
        "files_processed": 0
    }

# Admin router
admin_router = APIRouter(prefix="/admin", tags=["admin"])

@admin_router.get("/debug_live")
async def debug_live():
    """Live debug endpoint"""
    return {
        "status": "operational",
        "version": VERSION,
        "build_date": BUILD_DATE,
        "uptime_seconds": (datetime.utcnow() - global_state.startup_time).total_seconds(),
        "total_requests": global_state.request_count
    }

# Chat router
chat_router = APIRouter(prefix="/chat", tags=["chat"])

@chat_router.get("/greeting")
async def get_greeting():
    """Get Clair greeting"""
    return {
        "greeting": CLAIR_GREETING,
        "system_prompt_loaded": len(CLAIR_SYSTEM_PROMPT) > 100
    }

@chat_router.post("/")
async def chat(request: dict):
    """Chat endpoint - minimal implementation"""
    return {
        "response": f"Hello! I'm Clair (v{VERSION}). Chat functionality is being initialized.",
        "conversation_id": request.get("conversation_id", "default"),
        "message_count": 1
    }

# Include routers
app.include_router(documents_router)
app.include_router(admin_router)
app.include_router(chat_router)

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Enhanced RAG Clair System - SOTA Life Insurance AI",
        "version": VERSION,
        "build_date": BUILD_DATE,
        "greeting": CLAIR_GREETING,
        "status": "operational"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "greeting": CLAIR_GREETING[:50] + "..."
    }

# Request tracking middleware
@app.middleware("http")
async def track_requests(request: Request, call_next):
    global_state.track_request()
    response = await call_next(request)
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🌟 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)