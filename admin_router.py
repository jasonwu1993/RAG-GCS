# Admin Router - Debug, Monitoring, and Administrative Functions
# Preserves ALL original debug and admin functionality from main.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, List, Any
from datetime import datetime
import threading
import sys
import os
import json
from dotenv import load_dotenv

# Define fallback functions first
def log_debug(msg, data=None): 
    print(f"[DEBUG] {msg}")

def track_function_entry(name): 
    pass

class MockState:
    def __init__(self):
        self.sync_state = {"is_syncing": False, "last_sync": None}
        self.debug_mode = False
        
# Safe imports - only import core functions, services will be imported as needed
try:
    from core import log_debug, track_function_entry, global_state, health_check, emergency_reset, get_current_metrics, toggle_debug_mode
    core_imports_successful = True
except ImportError as e:
    print(f"⚠️ Core import failed in admin_router: {e}")
    core_imports_successful = False
    # Use fallback MockState
    global_state = MockState()
    def health_check(): return {"status": "degraded", "version": "6.4-CHAT-ENDPOINTS-CLAIR-AI"}
    def emergency_reset(): return {"status": "reset complete"}
    def get_current_metrics(): return {}
    def toggle_debug_mode(): return False
from config import *

router = APIRouter(prefix="/admin", tags=["admin"])

VERSION = "6.4-CHAT-ENDPOINTS-CLAIR-AI"  
BUILD_DATE = "2025-08-04"

def _get_service_status(service_name: str) -> bool:
    """Safely check service availability"""
    try:
        from core import bucket, drive_service, index_endpoint, openai_client
        services = {
            "bucket": bucket,
            "drive_service": drive_service, 
            "index_endpoint": index_endpoint,
            "openai_client": openai_client
        }
        return services.get(service_name) is not None
    except ImportError:
        return False

@router.get("/debug")
async def get_debug_info():
    """Complete debug information - preserved from original main.py"""
    track_function_entry("get_debug_info")
    
    try:
        debug_info = {
            "system": {
                "version": VERSION,
                "build_date": BUILD_DATE,
                "timestamp": datetime.utcnow().isoformat(),
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "active_threads": threading.active_count()
            },
            "environment": {
                "gcp_project_id": PROJECT_ID,
                "region": REGION,
                "bucket_name": BUCKET_NAME,
                "drive_folder_id": GOOGLE_DRIVE_FOLDER_ID,
                "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
                "port": int(os.environ.get("PORT", 8080))
            },
            "services": {
                "storage_available": _get_service_status("bucket"),
                "drive_available": _get_service_status("drive_service"),
                "vertex_ai_available": _get_service_status("index_endpoint"),
                "openai_available": _get_service_status("openai_client")
            },
            "sync_state": global_state.sync_state.copy(),
            "performance": get_current_metrics(),
            "configuration": {
                "similarity_threshold": SIMILARITY_THRESHOLD,
                "top_k_results": TOP_K,
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "embed_model": EMBED_MODEL,
                "gpt_model": GPT_MODEL
            },
            "features": {
                "modular_architecture": True,
                "intelligent_routing": True,
                "life_insurance_expertise": True,
                "ultra_resilient_sync": True,
                "circuit_breaker_protection": True,
                "advanced_entity_extraction": True,
                "intent_classification": True
            }
        }
        
        return debug_info
        
    except Exception as e:
        log_debug("ERROR getting debug info", {"error": str(e)})
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "minimal_info": {
                "version": VERSION,
                "status": "error_mode"
            }
        }

@router.get("/debug_env")
async def debug_environment_variables():
    """Emergency diagnostic endpoint to check environment variables and OpenAI configuration"""
    track_function_entry("debug_environment_variables")
    
    # SECURE ENVIRONMENT LOADING CHECK
    # LOCAL DEVELOPMENT: Check .env loading
    # PRODUCTION: Should NOT load .env (security requirement)
    environment = os.getenv("ENVIRONMENT", "development")
    dotenv_result = {"status": "unknown", "environment": environment}
    
    if environment == "development":
        # LOCAL DEVELOPMENT ONLY: Try loading .env
        try:
            load_dotenv()
            dotenv_result = {"status": "loaded_for_development", "environment": "development", "source": ".env_file"}
        except Exception as e:
            dotenv_result = {"status": f"failed: {str(e)}", "environment": "development", "source": ".env_file"}
    else:
        # PRODUCTION: Should use Google Secret Manager only
        dotenv_result = {"status": "disabled_for_security", "environment": "production", "source": "google_secret_manager"}

    # Check critical environment variables
    env_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT"),
        "GPT_MODEL": os.getenv("GPT_MODEL"),
        "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID"),
        "MAX_TOKENS": os.getenv("MAX_TOKENS"),
        "TEMPERATURE": os.getenv("TEMPERATURE")
    }
    
    env_status = {}
    for key, value in env_vars.items():
        if key == "OPENAI_API_KEY" and value:
            env_status[key] = {
                "set": True,
                "length": len(value),
                "preview": f"{value[:15]}..." if len(value) > 15 else value
            }
        elif value:
            env_status[key] = {"set": True, "value": value}
        else:
            env_status[key] = {"set": False, "value": None}

    # Test OpenAI client
    openai_test = {"status": "unknown", "error": None, "response": None}
    try:
        from openai import OpenAI
        client = OpenAI()
        openai_test["client_created"] = True
        
        # Try a simple API call
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=10
        )
        openai_test["status"] = "success"
        openai_test["response"] = response.choices[0].message.content
        
    except Exception as e:
        openai_test["status"] = "failed"
        openai_test["error"] = str(e)
        openai_test["client_created"] = False
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "dotenv_loading": dotenv_result,
        "environment_variables": env_status,
        "openai_test": openai_test,
        "system_info": {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "environment_type": "production" if os.getenv("ENVIRONMENT") == "production" else "development"
        }
    }

@router.get("/debug_live")
async def get_live_debug_data():
    """Live debug data with real-time metrics - preserved from original main.py"""
    track_function_entry("get_live_debug_data")
    
    try:
        from google_drive import ultra_sync
        
        # Create the sync_progress structure that the frontend expects
        sync_progress = {
            "current_operation": "monitoring" if not global_state.sync_state["is_syncing"] else "syncing",
            "files_found": global_state.files_found,
            "api_calls": global_state.api_calls,
            "folder_stack": [],  # Can be enhanced later if needed
            "sync_steps": {},
            "recursive_stats": {}
        }
        
        live_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_health": health_check(),
            "real_time_metrics": {
                "active_threads": threading.active_count(),
                "total_requests": global_state.request_count,
                "function_call_counts": global_state.function_calls.copy(),
                "uptime_seconds": (datetime.utcnow() - global_state.startup_time).total_seconds()
            },
            "sync_system": {
                "current_state": global_state.sync_state.copy(),
                "ultra_sync_status": ultra_sync.get_sync_status(),
                "is_syncing": global_state.sync_state["is_syncing"],
                "last_sync": global_state.sync_state.get("last_sync"),
                "next_auto_sync": global_state.sync_state.get("next_auto_sync")
            },
            "memory_usage": {
                "debug_mode": global_state.debug_mode,
                "performance_metrics": global_state.performance_metrics.copy()
            },
            "ai_service": {
                "intelligent_routing_active": True,
                "domain_expertise": "life_insurance",
                "supported_intents": len(ENHANCED_INSURANCE_CONFIG["ADVANCED_INTENTS"]),
                "supported_products": len(ENHANCED_INSURANCE_CONFIG["PRODUCT_TYPES"])
            },
            # Add the sync_progress at the top level for frontend compatibility
            "sync_progress": sync_progress,
            # Also keep it in debug_info for backward compatibility
            "debug_info": {
                "sync_progress": sync_progress,
                "errors": [],  # Can be enhanced with error tracking
                "performance_metrics": global_state.performance_metrics.copy()
            }
        }
        
        return live_data
        
    except Exception as e:
        log_debug("ERROR getting live debug data", {"error": str(e)})
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "basic_status": "error_mode"
        }

@router.post("/emergency_reset")
async def perform_emergency_reset():
    """Emergency app reset - clears app state and reloads from Vertex AI (preserves knowledge base)"""
    track_function_entry("perform_emergency_reset")
    
    try:
        log_debug("EMERGENCY RESET initiated by admin request")
        
        # Perform emergency reset (app state only, preserves Vertex AI)
        reset_result = emergency_reset()
        
        # Additional modular system reset
        global_state.debug_mode = False
        global_state.performance_metrics.clear()
        
        log_debug("EMERGENCY RESET completed successfully - triggering app reinitialization")
        
        # The frontend will handle reloading documents and auto-selection after this response
        return {
            "message": "Emergency reset completed - app will reload from Vertex AI",
            "reset_result": reset_result,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "system_reset_complete",
            "next_steps": "App will now reload file structure from Vertex AI and auto-select all files"
        }
        
    except Exception as e:
        log_debug("EMERGENCY RESET failed", {"error": str(e)})
        return {
            "message": "Emergency reset failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "reset_failed"
        }

@router.post("/test_background_task")
async def test_background_task_endpoint(background_tasks: BackgroundTasks):
    """Test background task functionality - preserved from original main.py"""
    track_function_entry("test_background_task_endpoint")
    
    def test_task():
        """Background test task"""
        import time
        log_debug("Background task started")
        time.sleep(2)  # Simulate work
        log_debug("Background task completed")
        global_state.track_function_call("background_test_task")
    
    try:
        background_tasks.add_task(test_task)
        
        return {
            "message": "Background task started successfully",
            "task_type": "test_task",
            "estimated_duration": "2 seconds",
            "timestamp": datetime.utcnow().isoformat(),
            "active_threads": threading.active_count()
        }
        
    except Exception as e:
        log_debug("ERROR starting background task", {"error": str(e)})
        return {
            "message": "Failed to start background task",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/features")
async def get_available_features():
    """Get available features based on service status - preserved from original"""
    track_function_entry("get_available_features")
    
    try:
        from core import get_service_status
        service_status = get_service_status()
        
        return {
            "available_features": {
                "modular_architecture": True,
                "intelligent_ai_routing": True,
                "life_insurance_expertise": True,
                "ultra_resilient_sync": True,
                "advanced_search": True,
                "entity_extraction": True,
                "intent_classification": True,
                "circuit_breaker_protection": True,
                "vector_search": service_status["vertex_ai_available"],
                "document_sync": service_status["drive_available"],
                "ai_responses": service_status["openai_available"]
            },
            "service_status": service_status,
            "sync_capabilities": {
                "recursive_sync": True,
                "ultra_resilient": True,
                "exponential_backoff": True,
                "rate_limiting": True,
                "circuit_breaker": True
            },
            "ai_capabilities": {
                "domain_expertise": "life_insurance",
                "intent_types": len(ENHANCED_INSURANCE_CONFIG["ADVANCED_INTENTS"]),
                "product_types": len(ENHANCED_INSURANCE_CONFIG["PRODUCT_TYPES"]),
                "entity_types": len(ENHANCED_INSURANCE_CONFIG["ENTITY_RECOGNITION"]),
                "response_strategies": 8
            },
            "version": VERSION,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_debug("ERROR getting features", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not get features: {str(e)}")

@router.get("/config")
async def get_system_config():
    """Get system configuration and limits - preserved from original"""
    track_function_entry("get_system_config")
    
    try:
        return {
            "version": VERSION,
            "build_date": BUILD_DATE,
            "architecture": "modular_sota",
            "configuration": {
                "ai_service": {
                    "model": GPT_MODEL,
                    "max_tokens": MAX_TOKENS,
                    "temperature": TEMPERATURE,
                    "embed_model": EMBED_MODEL
                },
                "search": {
                    "similarity_threshold": SIMILARITY_THRESHOLD,
                    "top_k": TOP_K,
                    "semantic_weight": SEARCH_CONFIG["semantic_weight"],
                    "keyword_weight": SEARCH_CONFIG["keyword_weight"]
                },
                "environment": {
                    "project_id": PROJECT_ID,
                    "region": REGION,
                    "bucket_name": BUCKET_NAME,
                    "drive_folder_id": GOOGLE_DRIVE_FOLDER_ID
                }
            },
            "features": {
                "modular_architecture": True,
                "intelligent_routing": True,
                "life_insurance_domain": True,
                "ultra_resilient_sync": True,
                "circuit_breaker_protection": True,
                "comprehensive_error_handling": True,
                "thread_safe_operations": True
            },
            "container_info": {
                "port": int(os.environ.get("PORT", 8080)),
                "working_directory": os.getcwd(),
                "python_version": sys.version,
                "active_threads": threading.active_count()
            },
            "domain_expertise": {
                "product_types": list(ENHANCED_INSURANCE_CONFIG["PRODUCT_TYPES"].keys()),
                "intent_categories": list(ENHANCED_INSURANCE_CONFIG["ADVANCED_INTENTS"].keys()),
                "entity_types": list(ENHANCED_INSURANCE_CONFIG["ENTITY_RECOGNITION"].keys())
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_debug("ERROR getting system config", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not get config: {str(e)}")

@router.get("/status")
async def get_admin_status():
    """Get comprehensive admin status"""
    track_function_entry("get_admin_status")
    
    try:
        return {
            "system_status": "operational",
            "version": VERSION,
            "build_date": BUILD_DATE,
            "health_check": health_check(),
            "current_metrics": get_current_metrics(),
            "debug_mode": global_state.debug_mode,
            "admin_capabilities": {
                "emergency_reset": True,
                "debug_information": True,
                "live_monitoring": True,
                "background_tasks": True,
                "system_configuration": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_debug("ERROR getting admin status", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not get admin status: {str(e)}")

@router.post("/toggle_debug")
async def toggle_system_debug():
    """Toggle debug mode on/off"""
    track_function_entry("toggle_system_debug")
    
    try:
        new_state = toggle_debug_mode()
        
        return {
            "message": f"Debug mode {'enabled' if new_state else 'disabled'}",
            "debug_mode": new_state,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_debug("ERROR toggling debug mode", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not toggle debug: {str(e)}")

# Legacy compatibility endpoints
@router.get("/api/health")
async def api_health():
    """Alternative health endpoint for different routing - backward compatibility"""
    health_data = health_check()
    return health_data

@router.get("/api/status") 
async def api_status():
    """Alternative status endpoint - backward compatibility"""
    return await get_admin_status()