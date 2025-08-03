# Core Services and Shared Utilities for Enhanced RAG Clair System

import os
import json
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import google.auth
from google.cloud import storage, aiplatform
from google.oauth2 import service_account
from googleapiclient.discovery import build
from openai import OpenAI
from dotenv import load_dotenv
from config import *

# Load environment variables
load_dotenv()

# Global state management
class GlobalState:
    def __init__(self):
        self.sync_state = {
            "is_syncing": False,
            "last_sync": None,
            "last_sync_results": None,
            "next_auto_sync": None
        }
        self.debug_mode = False
        self.request_count = 0
        self.startup_time = datetime.utcnow()
        self.function_calls = {}
        self.performance_metrics = {}
        self.api_calls = 0
        self.files_found = 0
        self._lock = threading.Lock()
        
        # Initialize persistent state restoration
        self._initialize_persistent_state()
        
        # Circuit breaker for request overload protection
        self.circuit_breaker = {
            "is_open": False,
            "failure_count": 0,
            "last_failure_time": None,
            "success_count": 0,
            "total_requests": 0,
            "success_rate": 1.0
        }
    
    def track_request(self, success: bool = True):
        with self._lock:
            self.request_count += 1
            self.circuit_breaker["total_requests"] += 1
            
            if success:
                self.circuit_breaker["success_count"] += 1
                self.circuit_breaker["failure_count"] = max(0, self.circuit_breaker["failure_count"] - 1)
            else:
                self.circuit_breaker["failure_count"] += 1
                self.circuit_breaker["last_failure_time"] = datetime.utcnow()
            
            # Update success rate
            total = self.circuit_breaker["total_requests"]
            if total > 0:
                self.circuit_breaker["success_rate"] = self.circuit_breaker["success_count"] / total
            
            # Open circuit breaker if success rate drops below 50% with significant sample size
            if (total >= 10 and 
                self.circuit_breaker["success_rate"] < 0.5 and 
                self.circuit_breaker["failure_count"] >= 5):
                self.circuit_breaker["is_open"] = True
                log_debug("Circuit breaker opened due to low success rate", {
                    "success_rate": self.circuit_breaker["success_rate"],
                    "total_requests": total,
                    "failure_count": self.circuit_breaker["failure_count"]
                })
    
    def track_function_call(self, function_name: str):
        with self._lock:
            if function_name not in self.function_calls:
                self.function_calls[function_name] = 0
            self.function_calls[function_name] += 1
    
    def track_api_call(self):
        with self._lock:
            self.api_calls += 1
    
    def update_files_found(self, count: int):
        with self._lock:
            self.files_found = count
    
    def check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows requests"""
        with self._lock:
            if not self.circuit_breaker["is_open"]:
                return True
            
            # Auto-reset circuit breaker after 60 seconds if failure count decreases
            if self.circuit_breaker["last_failure_time"]:
                time_since_failure = datetime.utcnow() - self.circuit_breaker["last_failure_time"]
                if time_since_failure.total_seconds() > 60:
                    self.circuit_breaker["is_open"] = False
                    self.circuit_breaker["failure_count"] = 0
                    log_debug("Circuit breaker auto-reset after timeout")
                    return True
            
            return False
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker"""
        with self._lock:
            self.circuit_breaker["is_open"] = False
            self.circuit_breaker["failure_count"] = 0
            self.circuit_breaker["success_count"] = 0
            self.circuit_breaker["total_requests"] = 0
            self.circuit_breaker["success_rate"] = 1.0
            log_debug("Circuit breaker manually reset")
    
    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            uptime = datetime.utcnow() - self.startup_time
            return {
                "uptime_seconds": uptime.total_seconds(),
                "total_requests": self.request_count,
                "function_calls": self.function_calls.copy(),
                "sync_state": self.sync_state.copy(),
                "debug_mode": self.debug_mode,
                "api_calls": self.api_calls,
                "files_found": self.files_found,
                "circuit_breaker": self.circuit_breaker.copy()
            }
    
    def _initialize_persistent_state(self):
        """Restore sync state from GCS on startup"""
        try:
            # Get bucket reference if available
            from google.cloud import storage
            if PROJECT_ID and BUCKET_NAME:
                storage_client = storage.Client(project=PROJECT_ID)
                bucket = storage_client.bucket(BUCKET_NAME)
                
                state_blob = bucket.blob("system_state.json")
                if state_blob.exists():
                    stored_state = json.loads(state_blob.download_as_text())
                    if "sync_state" in stored_state:
                        self.sync_state.update(stored_state["sync_state"])
                        log_debug("Restored sync state from persistent storage", {
                            "last_sync": self.sync_state.get("last_sync"),
                            "restored_keys": list(stored_state["sync_state"].keys())
                        })
        except Exception as e:
            log_debug("Could not restore sync state, using defaults", {"error": str(e)})
    
    def persist_sync_state(self):
        """Persist sync state to GCS immediately"""
        try:
            # Get global bucket reference
            if bucket:
                state_data = {
                    "sync_state": self.sync_state,
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0"
                }
                state_blob = bucket.blob("system_state.json")
                state_blob.upload_from_string(json.dumps(state_data, indent=2))
                log_debug("Persisted sync state to GCS", {
                    "last_sync": self.sync_state.get("last_sync"),
                    "is_syncing": self.sync_state.get("is_syncing")
                })
        except Exception as e:
            log_debug("Failed to persist sync state", {"error": str(e)})
    
    def update_sync_completion(self, start_time: datetime, results: Dict):
        """Atomically update and persist sync completion"""
        with self._lock:
            self.sync_state.update({
                "last_sync": start_time.isoformat(),
                "last_sync_results": results,
                "next_auto_sync": (start_time + timedelta(hours=2)).isoformat(),
                "is_syncing": False
            })
            # Persist immediately after update
            self.persist_sync_state()
            log_debug("Sync completion updated and persisted", {
                "last_sync": self.sync_state["last_sync"],
                "files_updated": len(results.get("updated", [])) if results else 0
            })

# Global state instance
global_state = GlobalState()

# Service instances (initialized later)
storage_client = None
bucket = None
drive_service = None
index_endpoint = None
openai_client = None

def log_debug(message: str, data: Any = None):
    """Enhanced logging with structured output"""
    timestamp = datetime.utcnow().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "message": message,
        "data": data
    }
    
    if global_state.debug_mode:
        print(f"[DEBUG {timestamp}] {message}")
        if data:
            print(f"[DEBUG DATA] {json.dumps(data, indent=2, default=str)}")
    
    # In production, send to Cloud Logging
    return log_entry

def track_function_entry(function_name: str):
    """Track function call for monitoring"""
    global_state.track_function_call(function_name)
    log_debug(f"Function called: {function_name}")

def validate_environment() -> Dict[str, bool]:
    """Validate all required environment variables"""
    validation_results = {
        "PROJECT_ID": bool(PROJECT_ID),
        "BUCKET_NAME": bool(BUCKET_NAME),
        "INDEX_ENDPOINT_ID": bool(INDEX_ENDPOINT_ID),
        "DEPLOYED_INDEX_ID": bool(DEPLOYED_INDEX_ID),
        "GOOGLE_DRIVE_FOLDER_ID": bool(GOOGLE_DRIVE_FOLDER_ID),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY"))
    }
    
    all_valid = all(validation_results.values())
    log_debug("Environment validation", {
        "results": validation_results,
        "all_valid": all_valid
    })
    
    return validation_results

def initialize_storage_client():
    """Initialize Google Cloud Storage client"""
    global storage_client, bucket
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        
        # Test bucket access
        bucket.reload()
        log_debug("Storage client initialized successfully")
        return True
    except Exception as e:
        log_debug("Failed to initialize storage client", {"error": str(e)})
        return False

def initialize_drive_service():
    """Initialize Google Drive service"""
    global drive_service
    try:
        # Try file-based credentials first (for local development)
        if os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
            credentials = service_account.Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            log_debug("Using service account file for Google Drive")
        else:
            # Use default credentials (for Cloud Run)
            credentials, _ = google.auth.default(
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            log_debug("Using default credentials for Google Drive")
        
        drive_service = build('drive', 'v3', credentials=credentials)
        log_debug("Google Drive service initialized successfully")
        return True
        
    except Exception as e:
        log_debug("Failed to initialize Google Drive service", {"error": str(e)})
        drive_service = None
        return False

def initialize_vertex_ai():
    """Initialize Vertex AI services"""
    global index_endpoint
    try:
        aiplatform.init(project=PROJECT_ID, location=REGION)
        
        index_endpoint_resource_name = f"projects/{PROJECT_ID}/locations/{REGION}/indexEndpoints/{INDEX_ENDPOINT_ID}"
        index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=index_endpoint_resource_name
        )
        
        log_debug("Vertex AI initialized successfully")
        return True
    except Exception as e:
        log_debug("Failed to initialize Vertex AI", {"error": str(e)})
        index_endpoint = None
        return False

def initialize_openai_client():
    """Initialize OpenAI client"""
    global openai_client
    try:
        openai_client = OpenAI()
        log_debug("OpenAI client initialized successfully")
        return True
    except Exception as e:
        log_debug("Failed to initialize OpenAI client", {"error": str(e)})
        return False

def initialize_all_services() -> Dict[str, bool]:
    """Initialize all external services and return status"""
    track_function_entry("initialize_all_services")
    
    # Validate environment first
    env_validation = validate_environment()
    if not all(env_validation.values()):
        log_debug("Environment validation failed", env_validation)
    
    # Initialize services
    initialization_results = {
        "environment": all(env_validation.values()),
        "storage": initialize_storage_client(),
        "drive": initialize_drive_service(),
        "vertex_ai": initialize_vertex_ai(),
        "openai": initialize_openai_client()
    }
    
    log_debug("Service initialization completed", initialization_results)
    return initialization_results

def get_service_status() -> Dict[str, Any]:
    """Get current status of all services"""
    return {
        "storage_available": storage_client is not None and bucket is not None,
        "drive_available": drive_service is not None,
        "vertex_ai_available": index_endpoint is not None,
        "openai_available": openai_client is not None,
        "bucket_name": BUCKET_NAME,
        "project_id": PROJECT_ID,
        "region": REGION
    }

def health_check() -> Dict[str, Any]:
    """Comprehensive health check of all services"""
    track_function_entry("health_check")
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": get_service_status(),
        "global_state": global_state.get_status()
    }
    
    # Check if critical services are available
    critical_services = ["storage_available", "openai_available"]
    critical_status = all(
        health_status["services"].get(service, False) 
        for service in critical_services
    )
    
    if not critical_status:
        health_status["status"] = "degraded"
    
    return health_status

def emergency_reset():
    """Emergency reset of app state and services (does NOT touch Vertex AI knowledge base)
    
    This function only clears:
    - Local app state and caches
    - Service connections 
    - Session data and metrics
    
    It does NOT:
    - Delete or modify any documents in Vertex AI
    - Remove any indexed files or chunks
    - Touch the knowledge base content
    
    After reset, the app will reload file structure from Vertex AI and restore normal operation.
    """
    track_function_entry("emergency_reset")
    
    try:
        # Reset only local app state - NOT Vertex AI data
        global_state.sync_state = {
            "is_syncing": False,
            "last_sync": None,
            "last_sync_results": None,
            "next_auto_sync": None
        }
        global_state.request_count = 0
        global_state.function_calls = {}
        global_state.performance_metrics = {}
        global_state.api_calls = 0
        global_state.files_found = 0
        global_state.reset_circuit_breaker()
        
        # Reinitialize service connections (not data)
        initialization_results = initialize_all_services()
        
        log_debug("Emergency reset completed - app state cleared, Vertex AI knowledge base preserved", initialization_results)
        return {
            "status": "reset_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "reinitialization": initialization_results,
            "message": "App state reset successfully - knowledge base preserved"
        }
    except Exception as e:
        log_debug("Emergency reset failed", {"error": str(e)})
        return {
            "status": "reset_failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Utility functions for common operations
def get_current_metrics() -> Dict[str, Any]:
    """Get current system metrics"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "global_state": global_state.get_status(),
        "services": get_service_status(),
        "environment": {
            "project_id": PROJECT_ID,
            "region": REGION,
            "bucket_name": BUCKET_NAME
        }
    }

def toggle_debug_mode(enabled: bool = None) -> bool:
    """Toggle or set debug mode"""
    if enabled is not None:
        global_state.debug_mode = enabled
    else:
        global_state.debug_mode = not global_state.debug_mode
    
    log_debug(f"Debug mode {'enabled' if global_state.debug_mode else 'disabled'}")
    return global_state.debug_mode

# Initialize services on module import
if __name__ != "__main__":
    initialize_all_services()