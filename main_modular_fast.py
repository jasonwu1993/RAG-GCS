# OPTIMIZED MAIN MODULE FOR FAST CLOUD RUN STARTUP
# Fixes deployment timeout issues by deferring heavy initialization

import os
import asyncio
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# System identification
VERSION = "6.4-FAST-STARTUP-OPTIMIZED"
BUILD_DATE = "2025-08-06"

# OPTIMIZATION 1: Minimal essential imports only during startup
print("🚀 FAST STARTUP: Loading essential components only...")

# Essential fallback functions (always available)
def log_debug(msg, data=None): 
    print(f"[DEBUG] {msg}")

def track_function_entry(name): 
    pass

class MockState: 
    def __init__(self): 
        self.startup_time = datetime.utcnow()
        self.request_count = 0
        self.debug_mode = False
        self.sync_state = {"is_syncing": False, "last_sync": None}
        self.function_calls = {}
        self.performance_metrics = {}
        self.api_calls = 0
        self.files_found = 0
    def track_request(self, success=True): 
        self.request_count += 1
    def track_function_call(self, name):
        self.function_calls[name] = self.function_calls.get(name, 0) + 1

# Initialize with mock state immediately
global_state = MockState()

# OPTIMIZATION 2: Lazy loading of heavy components
_heavy_components_loaded = False
_routers_cache = {}

def load_heavy_components():
    """Load heavy components on first request, not at startup"""
    global _heavy_components_loaded, _routers_cache
    
    if _heavy_components_loaded:
        return _routers_cache
    
    print("🔄 Loading heavy components on demand...")
    
    try:
        from core import initialize_all_services, health_check, global_state as core_global_state
        _routers_cache['core'] = {'initialize_all_services': initialize_all_services, 'health_check': health_check, 'global_state': core_global_state}
        print("✅ Core components loaded")
    except Exception as e:
        print(f"⚠️ Core components not available: {e}")
        _routers_cache['core'] = {'initialize_all_services': lambda: {"error": "Core not available"}, 'health_check': lambda: {"status": "degraded", "version": VERSION}, 'global_state': global_state}
    
    try:
        from documents_router import router as documents_router, auto_sync_loop
        _routers_cache['documents'] = {'router': documents_router, 'auto_sync_loop': auto_sync_loop}
        print("✅ Documents router loaded")
    except Exception as e:
        print(f"⚠️ Documents router not available: {e}")
        _routers_cache['documents'] = None
    
    try:
        from search_router import router as search_router  
        _routers_cache['search'] = {'router': search_router}
        print("✅ Search router loaded")
    except Exception as e:
        print(f"⚠️ Search router not available: {e}")
        _routers_cache['search'] = None
    
    try:
        from chat_router import router as chat_router
        _routers_cache['chat'] = {'router': chat_router}
        print("✅ Chat router loaded")
    except Exception as e:
        print(f"⚠️ Chat router not available: {e}")
        _routers_cache['chat'] = None
    
    try:
        from admin_router import router as admin_router
        _routers_cache['admin'] = {'router': admin_router}
        print("✅ Admin router loaded")
    except Exception as e:
        print(f"⚠️ Admin router not available: {e}")
        _routers_cache['admin'] = None
    
    _heavy_components_loaded = True
    return _routers_cache

# OPTIMIZATION 3: Minimal config loading
CLAIR_GREETING = "Hello! I'm Clair, your financial advisor specializing in life insurance."
try:
    from config import CLAIR_GREETING
    print("✅ Config loaded successfully")
except Exception as e:
    print(f"⚠️ Using fallback config: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """OPTIMIZED lifespan - minimal startup, deferred initialization"""
    print("🚀 FAST STARTUP: Enhanced RAG Clair System starting...")
    print("⚡ Heavy components will load on first request")
    
    # OPTIMIZATION: Don't initialize heavy services during startup
    # Let Cloud Run startup probe succeed quickly
    
    print("🎯 FAST STARTUP: System ready for requests!")
    yield
    
    print("🛑 Shutting down Enhanced RAG Clair System...")

# OPTIMIZATION 4: Create FastAPI app with minimal startup time
app = FastAPI(
    title="Enhanced RAG Clair System - Fast Startup",
    description="Optimized for fast Cloud Run deployment",
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

# OPTIMIZATION 5: Fast health check that doesn't require heavy components
@app.get("/health")
async def fast_health_check():
    """Ultra-fast health check for startup probes"""
    return {
        "status": "healthy",
        "version": VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "startup_mode": "fast",
        "heavy_components_loaded": _heavy_components_loaded
    }

# OPTIMIZATION 6: Lazy router mounting middleware
@app.middleware("http")
async def lazy_router_loader(request: Request, call_next):
    """Load routers on first request to specific paths"""
    
    # Check if we need to load components for this request
    path = request.url.path
    
    if not _heavy_components_loaded and path not in ["/health", "/docs", "/openapi.json"]:
        components = load_heavy_components()
        
        # Mount routers after loading
        if components.get('documents') and components['documents'].get('router'):
            app.include_router(components['documents']['router'])
        if components.get('search') and components['search'].get('router'):
            app.include_router(components['search']['router'])  
        if components.get('chat') and components['chat'].get('router'):
            app.include_router(components['chat']['router'])
        if components.get('admin') and components['admin'].get('router'):
            app.include_router(components['admin']['router'])
        
        # Update global_state if available
        if components.get('core', {}).get('global_state'):
            global global_state
            global_state = components['core']['global_state']
        
        print("🔄 All routers mounted successfully")
    
    response = await call_next(request)
    return response

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - fast response"""
    return {
        "message": "Enhanced RAG Clair System - Fast Startup Mode",
        "version": VERSION,
        "status": "operational",
        "startup_optimization": "enabled",
        "heavy_components_loaded": _heavy_components_loaded,
        "greeting": CLAIR_GREETING,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting optimized server on port {port}")
    
    uvicorn.run(
        "main_modular_fast:app",
        host="0.0.0.0", 
        port=port,
        timeout_keep_alive=30,
        timeout_graceful_shutdown=30
    )