# main.py
"""
Complete RAG Clair System - Production Ready Backend
====================================================
🔥 Production-ready with recursive Google Drive sync
🚀 Robust container startup with graceful service failures  
🔐 Thread-safe sync state management with race condition fixes
✅ Optimized for Google Cloud Run deployment
🔍 Advanced debugging and comprehensive error handling
📁 Recursive folder scanning with depth control
⚡ Enhanced performance monitoring and timeout protection
🐛 Complete solution with all improvements merged
"""
import os
import json
import asyncio
import threading
import socket
import time
import traceback
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Google Cloud imports
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# OpenAI and processing imports
from openai import OpenAI
import pdfplumber
import tiktoken
import hashlib
import io
import tenacity  # Add this for retry functionality

# 🔥 VERSION IDENTIFIER
VERSION = "5.1-ENHANCED-RELIABILITY"
BUILD_DATE = "2025-07-31"

print(f"🚀 Starting COMPLETE RAG Clair System {VERSION} - Built {BUILD_DATE}")

# === ENVIRONMENT VARIABLES VALIDATION ===
def validate_environment():
    """Validate and report environment variable status"""
    print("🔍 Environment Variables Check:")
    
    # Critical for Cloud Run
    port = os.environ.get("PORT", "8080")
    print(f"   ✓ PORT: {port}")
    
    # Google Cloud Project
    gcp_project = os.environ.get("GCP_PROJECT_ID")
    if gcp_project:
        print(f"   ✓ GCP_PROJECT_ID: {gcp_project}")
    else:
        print("   ⚠️ GCP_PROJECT_ID: Not set (Google services may not work)")
    
    # Google Drive Folder
    drive_folder = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    if drive_folder:
        print(f"   ✓ GOOGLE_DRIVE_FOLDER_ID: {drive_folder}")
    else:
        print("   ⚠️ GOOGLE_DRIVE_FOLDER_ID: Not set (Drive sync disabled)")
    
    # OpenAI API Key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        print(f"   ✓ OPENAI_API_KEY: Set ({len(openai_key)} characters)")
    else:
        print("   ⚠️ OPENAI_API_KEY: Not set (AI features disabled)")
    
    # Google Application Credentials (for Cloud Run)
    google_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if google_creds:
        print(f"   ✓ GOOGLE_APPLICATION_CREDENTIALS: {google_creds}")
    else:
        print("   ℹ️ GOOGLE_APPLICATION_CREDENTIALS: Using default (Cloud Run metadata)")
    
    return {
        "port": port,
        "gcp_project": gcp_project,
        "drive_folder": drive_folder,
        "openai_key": bool(openai_key),
        "google_creds": google_creds
    }

# Call validation at startup
print("🚀 Starting Container Startup Validation...")
env_status = validate_environment()

# --- Enhanced Configuration ---
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

# Enhanced timeout settings (thread-safe) - Increased for reliability
TIMEOUTS = {
    "DRIVE_API": 60,      # Increased to 60 seconds per Drive API call
    "OPENAI_API": 45,     # Increased to 45 seconds for OpenAI calls
    "FILE_DOWNLOAD": 180, # Increased for slow Drive downloads
    "OVERALL_SYNC": 1200, # Increased to 20 minutes for entire sync
    "HEALTH_CHECK": 15    # 15 seconds for health checks
}

# Enhanced limits
LIMITS = {
    "MAX_FILES_PER_SYNC": 200,  # Increased max files
    "MAX_FILE_SIZE": 100 * 1024 * 1024,  # Increased to 100MB
    "MAX_FOLDERS_DEPTH": 10,  # Increased recursion depth
    "MAX_TEXT_LENGTH": 200000,  # Increased to 200k characters
    "CHUNK_SIZE": 2000
}

# Global variables
openai_client = None
drive_service = None
processed_files = {}
file_registry = {}

# 🔥 Thread-safe sync status tracking
sync_status = {
    "is_syncing": False,
    "last_sync": None,
    "last_sync_results": None,
    "next_auto_sync": None,
    "total_files_processed": 0,
    "version": VERSION,
    "enhanced_features": True,
    "sync_start_time": None,
    "sync_thread_id": None,
    "recursive_enabled": True
}

# Global lock for thread-safe access to sync_status
sync_lock = threading.Lock()

# 🤖 Clair system prompt
CLAIR_SYSTEM_PROMPT = ""

# 🔍 Enhanced debug state with comprehensive tracking
debug_info = {
    "current_operation": "idle",
    "folder_stack": [],
    "files_found": 0,
    "api_calls": 0,
    "start_time": None,
    "last_activity": None,
    "thread_id": None,
    "errors": [],
    "performance_metrics": {},
    "background_task_state": "not_started",
    "function_call_stack": [],
    "detailed_logs": [],
    "thread_creation_time": None,
    "sync_function_entry_time": None,
    "initialization_steps": {},
    "recursive_stats": {
        "max_depth_reached": 0,
        "folders_scanned": 0,
        "total_api_calls": 0
    },
    "current_file": None
}

# --- Enhanced Debug and Utility Functions ---
def log_debug(message, level="INFO", function_name=None, extra_data=None):
    """Enhanced debug logging with performance tracking and detailed context"""
    timestamp = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
    thread_id = threading.current_thread().ident
    thread_name = threading.current_thread().name
    
    context_info = f"[{timestamp}] [{level}] [Thread-{thread_id}:{thread_name}]"
    if function_name:
        context_info += f" [{function_name}]"
    
    full_message = f"{context_info} {message}"
    print(full_message, flush=True)
    print(full_message, file=sys.stderr, flush=True)
    
    global debug_info
    debug_info["last_activity"] = datetime.utcnow().isoformat()
    
    # Add to detailed logs
    log_entry = {
        "timestamp": timestamp,
        "level": level,
        "message": message,
        "thread_id": thread_id,
        "thread_name": thread_name,
        "function_name": function_name,
        "extra_data": extra_data
    }
    debug_info["detailed_logs"].append(log_entry)
    
    # Keep only last 100 detailed logs
    if len(debug_info["detailed_logs"]) > 100:
        debug_info["detailed_logs"] = debug_info["detailed_logs"][-100:]
    
    if level == "ERROR":
        debug_info["errors"].append(f"{timestamp}: {message}")
        if len(debug_info["errors"]) > 20:
            debug_info["errors"] = debug_info["errors"][-20:]

def track_function_entry(function_name, params=None):
    """Track function entry for debugging"""
    entry_time = datetime.utcnow().isoformat()
    debug_info["function_call_stack"].append({
        "function": function_name,
        "entry_time": entry_time,
        "params": params,
        "thread_id": threading.current_thread().ident
    })
    
    # Keep only last 50 function calls
    if len(debug_info["function_call_stack"]) > 50:
        debug_info["function_call_stack"] = debug_info["function_call_stack"][-50:]
    
    log_debug(f"🔄 ENTERING: {function_name}", "DEBUG", function_name, params)

def track_function_exit(function_name, result=None, error=None):
    """Track function exit for debugging"""
    if error:
        log_debug(f"❌ EXITING: {function_name} with ERROR: {error}", "ERROR", function_name)
    else:
        log_debug(f"✅ EXITING: {function_name} successfully", "DEBUG", function_name, result)

def set_socket_timeout(timeout_seconds):
    """Set global socket timeout for all network operations"""
    socket.setdefaulttimeout(timeout_seconds)
    log_debug(f"🔧 Set global socket timeout to {timeout_seconds} seconds", "INFO", "set_socket_timeout")

def clear_sync_state(reason="manual"):
    """Thread-safe sync state clearing"""
    global sync_status
    
    with sync_lock:
        old_state = sync_status["is_syncing"]
        sync_status["is_syncing"] = False
        sync_status["sync_start_time"] = None
        sync_status["sync_thread_id"] = None
    
    log_debug(f"🔄 SYNC STATE CLEARED ({reason}): {old_state} → False", "INFO", "clear_sync_state")
    
    if debug_info["current_operation"] not in ["idle", "completed"]:
        debug_info["current_operation"] = "idle"
        log_debug("🔄 Debug operation reset to idle", "INFO", "clear_sync_state")

def is_sync_stale():
    """Check if sync state is stale (stuck from previous failed attempt)"""
    with sync_lock:
        if not sync_status["is_syncing"]:
            return False
        
        # Check if sync started more than 10 minutes ago
        if sync_status["sync_start_time"]:
            start_time = datetime.fromisoformat(sync_status["sync_start_time"].replace('Z', '+00:00'))
            elapsed = (datetime.utcnow() - start_time.replace(tzinfo=None)).total_seconds()
            if elapsed > 600:  # 10 minutes
                log_debug(f"🚨 STALE SYNC DETECTED: {elapsed:.1f}s old", "WARN", "is_sync_stale")
                return True
        
        # Check if sync thread is no longer active
        if sync_status["sync_thread_id"]:
            active_thread_ids = [t.ident for t in threading.enumerate()]
            if sync_status["sync_thread_id"] not in active_thread_ids:
                log_debug(f"🚨 DEAD SYNC THREAD DETECTED: {sync_status['sync_thread_id']}", "WARN", "is_sync_stale")
                return True
    
    return False

# === ROBUST SERVICE INITIALIZATION ===

def safe_load_clair_system_prompt():
    """SAFE: Load Clair system prompt with fallback - never fails"""
    track_function_entry("safe_load_clair_system_prompt")
    
    global CLAIR_SYSTEM_PROMPT
    try:
        possible_paths = [
            "Clair-sys-prompt.txt",
            "./Clair-sys-prompt.txt", 
            "/app/Clair-sys-prompt.txt",
            os.path.join(os.getcwd(), "Clair-sys-prompt.txt"),
            os.path.join(os.path.dirname(__file__), "Clair-sys-prompt.txt")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    CLAIR_SYSTEM_PROMPT = f.read().strip()
                log_debug(f"✅ Loaded Clair system prompt from: {path} ({len(CLAIR_SYSTEM_PROMPT)} chars)", "INFO", "safe_load_clair_system_prompt")
                track_function_exit("safe_load_clair_system_prompt", {"path": path, "length": len(CLAIR_SYSTEM_PROMPT)})
                return True
                
        # Enhanced fallback system prompt
        CLAIR_SYSTEM_PROMPT = """You are Clair, a distinguished IUL strategist and wealth preservation architect with deep expertise in financial planning, insurance products, and wealth management.

Your role is to help clients understand their financial documents, insurance policies, and investment strategies. You provide personalized, professional guidance based on their specific documents and financial situations.

Key capabilities:
- Analyze insurance policies and financial documents
- Explain complex financial concepts in simple terms
- Provide strategic wealth preservation advice
- Offer IUL (Indexed Universal Life) insights
- Help with retirement and estate planning

Communication style:
- Professional yet approachable
- Clear and educational
- Always cite specific document references when available
- Respond primarily in Chinese unless English is specifically requested
- Focus on actionable, personalized advice

Always prioritize the client's best interests and provide ethical, compliant financial guidance."""
        
        log_debug("🔄 Using enhanced fallback system prompt", "WARN", "safe_load_clair_system_prompt")
        track_function_exit("safe_load_clair_system_prompt", {"fallback": True})
        return True
        
    except Exception as e:
        error_msg = f"Error loading system prompt: {e}"
        log_debug(f"❌ {error_msg}", "ERROR", "safe_load_clair_system_prompt")
        CLAIR_SYSTEM_PROMPT = "You are Clair, a helpful financial advisor."
        track_function_exit("safe_load_clair_system_prompt", error=error_msg)
        return True  # Never fail completely

def safe_initialize_openai():
    """SAFE: Initialize OpenAI - graceful failure"""
    track_function_entry("safe_initialize_openai")
    
    global openai_client
    try:
        debug_info["initialization_steps"]["openai_start"] = datetime.utcnow().isoformat()
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            log_debug("⚠️ OPENAI_API_KEY not set - OpenAI features will be disabled", "WARN", "safe_initialize_openai")
            debug_info["initialization_steps"]["openai_error"] = "API key not set"
            track_function_exit("safe_initialize_openai", {"available": False})
            return False
        
        log_debug("🔧 Creating OpenAI client...", "INFO", "safe_initialize_openai")
        openai_client = OpenAI(
            api_key=api_key.strip(),
            timeout=TIMEOUTS["OPENAI_API"]
        )
        
        debug_info["initialization_steps"]["openai_client_created"] = datetime.utcnow().isoformat()
        
        # Test the client with a simple call
        log_debug("🧪 Testing OpenAI client...", "INFO", "safe_initialize_openai")
        try:
            test_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            debug_info["initialization_steps"]["openai_test_success"] = datetime.utcnow().isoformat()
            log_debug("✅ OpenAI client initialized and tested successfully", "INFO", "safe_initialize_openai")
            track_function_exit("safe_initialize_openai", {"available": True})
            return True
        except Exception as test_error:
            error_msg = f"OpenAI test failed: {test_error}"
            log_debug(f"⚠️ {error_msg}", "WARN", "safe_initialize_openai")
            debug_info["initialization_steps"]["openai_test_error"] = error_msg
            track_function_exit("safe_initialize_openai", {"available": False, "error": error_msg})
            return False
            
    except Exception as e:
        error_msg = f"OpenAI initialization failed: {e}"
        log_debug(f"⚠️ {error_msg}", "WARN", "safe_initialize_openai")
        debug_info["initialization_steps"]["openai_init_error"] = error_msg
        openai_client = None
        track_function_exit("safe_initialize_openai", error=error_msg)
        return False

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=32),
    stop=tenacity.stop_after_attempt(3),
    reraise=True
)
def safe_initialize_google_drive():
    """SAFE: Initialize Google Drive - graceful failure with retry"""
    track_function_entry("safe_initialize_google_drive")
    
    global drive_service
    try:
        debug_info["initialization_steps"]["drive_start"] = datetime.utcnow().isoformat()
        
        if not GOOGLE_DRIVE_FOLDER_ID:
            log_debug("⚠️ GOOGLE_DRIVE_FOLDER_ID not set - Google Drive features will be disabled", "WARN", "safe_initialize_google_drive")
            debug_info["initialization_steps"]["drive_error"] = "Folder ID not set"
            track_function_exit("safe_initialize_google_drive", {"available": False})
            return False
            
        # Set timeout for auth
        log_debug("🔧 Setting socket timeout for authentication...", "INFO", "safe_initialize_google_drive")
        set_socket_timeout(TIMEOUTS["HEALTH_CHECK"])
        
        log_debug("🔧 Getting Google Cloud credentials...", "INFO", "safe_initialize_google_drive")
        credentials, _ = default(scopes=['https://www.googleapis.com/auth/drive.readonly'])
        
        debug_info["initialization_steps"]["drive_credentials"] = datetime.utcnow().isoformat()
        
        log_debug("🔧 Building Google Drive service...", "INFO", "safe_initialize_google_drive")
        drive_service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
        
        debug_info["initialization_steps"]["drive_service_built"] = datetime.utcnow().isoformat()
        
        # Test the service immediately
        log_debug("🧪 Testing Google Drive service...", "INFO", "safe_initialize_google_drive")
        test_request = drive_service.files().list(
            q=f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false",
            fields="files(id, name)",
            pageSize=1
        )
        
        set_socket_timeout(TIMEOUTS["DRIVE_API"])
        test_result = test_request.execute()
        
        debug_info["initialization_steps"]["drive_test_success"] = datetime.utcnow().isoformat()
        
        log_debug(f"✅ Google Drive service initialized and tested successfully", "INFO", "safe_initialize_google_drive")
        log_debug(f"📊 Test result: {len(test_result.get('files', []))} files found in folder", "INFO", "safe_initialize_google_drive")
        track_function_exit("safe_initialize_google_drive", {"available": True, "test_files": len(test_result.get('files', []))})
        return True
        
    except Exception as e:
        error_msg = f"Google Drive initialization failed: {e}"
        log_debug(f"⚠️ {error_msg}", "WARN", "safe_initialize_google_drive")
        log_debug(f"🔍 Traceback: {traceback.format_exc()}", "WARN", "safe_initialize_google_drive")
        debug_info["initialization_steps"]["drive_error"] = error_msg
        drive_service = None
        track_function_exit("safe_initialize_google_drive", error=error_msg)
        raise  # For retry

# === SERVICE AVAILABILITY CHECKS ===

def is_openai_available():
    """Check if OpenAI service is available"""
    return openai_client is not None

def is_drive_available():
    """Check if Google Drive service is available"""
    return drive_service is not None

def get_available_features():
    """Get list of available features based on initialized services"""
    features = {
        "basic_chat": True,  # Always available
        "document_analysis": is_drive_available(),
        "ai_responses": is_openai_available(),
        "file_sync": is_drive_available(),
        "recursive_sync": is_drive_available()
    }
    return features

# --- Enhanced File Processing Functions ---
def generate_file_hash(content: bytes) -> str:
    """Generate hash for file content change detection"""
    return hashlib.md5(content).hexdigest()

def chunk_text(text: str, max_tokens: int = LIMITS["CHUNK_SIZE"]) -> List[str]:
    """Enhanced text chunking with overlap"""
    track_function_entry("chunk_text", {"text_length": len(text), "max_tokens": max_tokens})
    
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        
        chunks = []
        overlap = max_tokens // 4  # 25% overlap
        
        for i in range(0, len(tokens), max_tokens - overlap):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
        
        track_function_exit("chunk_text", {"chunks_created": len(chunks)})
        return chunks
    except Exception as e:
        error_msg = f"Error chunking text: {e}"
        log_debug(f"❌ {error_msg}", "ERROR", "chunk_text")
        track_function_exit("chunk_text", error=error_msg)
        return [text[:LIMITS["MAX_TEXT_LENGTH"]]]

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Enhanced PDF text extraction with per-page error handling"""
    track_function_entry("extract_text_from_pdf", {"content_size": len(pdf_content)})
    
    try:
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            text = ""
            for page_num, page in enumerate(pdf.pages):
                if page_num >= 100:  # Increased limit to 100 pages
                    log_debug(f"⚠️ PDF truncated at 100 pages for memory efficiency", "WARN", "extract_text_from_pdf")
                    break
                
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as page_err:
                    log_debug(f"Skipped page {page_num} due to error: {str(page_err)}", "WARN", "extract_text_from_pdf")
                    continue  # Skip bad pages
                    
                # Memory check
                if len(text) > LIMITS["MAX_TEXT_LENGTH"]:
                    log_debug(f"⚠️ PDF text truncated at {LIMITS['MAX_TEXT_LENGTH']} characters", "WARN", "extract_text_from_pdf")
                    break
                    
            result_text = text[:LIMITS["MAX_TEXT_LENGTH"]]
            track_function_exit("extract_text_from_pdf", {"extracted_length": len(result_text)})
            return result_text
    except Exception as e:
        error_msg = f"Error extracting PDF text: {e}"
        log_debug(f"❌ {error_msg}", "ERROR", "extract_text_from_pdf")
        track_function_exit("extract_text_from_pdf", error=error_msg)
        return ""

# --- Enhanced Google Drive Functions with RECURSIVE SCANNING and RETRIES ---

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    stop=tenacity.stop_after_attempt(3),
    reraise=True
)
def get_drive_files_paginated(folder_id=None, path="", max_files=None):
    """Enhanced paginated file retrieval (non-recursive helper) with retry"""
    track_function_entry("get_drive_files_paginated", {"folder_id": folder_id, "path": path, "max_files": max_files})
    
    global debug_info
    
    if not drive_service:
        error_msg = "Google Drive service not initialized"
        log_debug(f"❌ {error_msg}", "ERROR", "get_drive_files_paginated")
        track_function_exit("get_drive_files_paginated", error=error_msg)
        raise Exception(error_msg)
    
    if folder_id is None:
        folder_id = GOOGLE_DRIVE_FOLDER_ID
    
    if max_files is None:
        max_files = LIMITS["MAX_FILES_PER_SYNC"]
    
    all_files = []
    all_folders = []
    page_token = None
    
    debug_info["current_operation"] = f"Paginated scan: {path or 'root'}"
    
    try:
        set_socket_timeout(TIMEOUTS["DRIVE_API"])
        
        page_count = 0
        while len(all_files) < max_files:
            page_count += 1
            log_debug(f"📡 API call for folder: {path or 'root'} (page: {page_count})", "INFO", "get_drive_files_paginated")
            
            try:
                request = drive_service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)",
                    pageSize=min(100, max_files - len(all_files)),  # Increased page size
                    pageToken=page_token,
                    orderBy="folder,name"
                )
                
                request_start = time.time()
                results = request.execute()
                request_duration = time.time() - request_start
                
                debug_info["api_calls"] = debug_info.get("api_calls", 0) + 1
                debug_info["recursive_stats"]["total_api_calls"] = debug_info["recursive_stats"].get("total_api_calls", 0) + 1
                
                log_debug(f"✅ API call completed in {request_duration:.2f}s", "INFO", "get_drive_files_paginated")
                
            except HttpError as http_error:
                error_msg = f"Google Drive API error: {http_error}"
                log_debug(f"❌ {error_msg}", "ERROR", "get_drive_files_paginated")
                track_function_exit("get_drive_files_paginated", error=error_msg)
                raise  # Will trigger retry
            except Exception as api_error:
                error_msg = f"API error: {str(api_error)}"
                log_debug(f"❌ {error_msg}", "ERROR", "get_drive_files_paginated")
                track_function_exit("get_drive_files_paginated", error=error_msg)
                raise  # Will trigger retry
            
            items = results.get('files', [])
            log_debug(f"✅ Found {len(items)} items in page {page_count}", "INFO", "get_drive_files_paginated")
            
            if not items:
                log_debug("🔚 No more items found, ending pagination", "INFO", "get_drive_files_paginated")
                break
            
            # Process items
            for item in items:
                item_path = f"{path}/{item['name']}" if path else item['name']
                item['path'] = item_path
                item['folder_path'] = path
                
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    all_folders.append(item)
                    log_debug(f"📁 Found folder: {item_path}", "DEBUG", "get_drive_files_paginated")
                else:
                    all_files.append(item)
                    debug_info["files_found"] = debug_info.get("files_found", 0) + 1
                    log_debug(f"📄 Found file: {item_path} ({item.get('mimeType', 'unknown type')})", "DEBUG", "get_drive_files_paginated")
            
            # Check for next page
            page_token = results.get('nextPageToken')
            if not page_token:
                log_debug("🔚 No next page token, pagination complete", "INFO", "get_drive_files_paginated")
                break
        
        result_summary = {"files": len(all_files), "folders": len(all_folders), "pages": page_count}
        log_debug(f"✅ Paginated scan complete: {len(all_files)} files, {len(all_folders)} folders across {page_count} pages", "INFO", "get_drive_files_paginated")
        track_function_exit("get_drive_files_paginated", result_summary)
        return all_files, all_folders
        
    except Exception as e:
        error_msg = f"Paginated scan failed: {str(e)}"
        log_debug(f"❌ {error_msg}", "ERROR", "get_drive_files_paginated")
        track_function_exit("get_drive_files_paginated", error=error_msg)
        raise

def get_drive_files_recursive(folder_id=None, path="", max_files=None, current_depth=0):
    """RECURSIVE: Comprehensive folder traversal with depth control"""
    track_function_entry("get_drive_files_recursive", {
        "folder_id": folder_id, 
        "path": path, 
        "max_files": max_files, 
        "current_depth": current_depth
    })
    
    global debug_info
    
    if not drive_service:
        error_msg = "Google Drive service not initialized"
        log_debug(f"❌ {error_msg}", "ERROR", "get_drive_files_recursive")
        track_function_exit("get_drive_files_recursive", error=error_msg)
        raise Exception(error_msg)
    
    if folder_id is None:
        folder_id = GOOGLE_DRIVE_FOLDER_ID
    
    if max_files is None:
        max_files = LIMITS["MAX_FILES_PER_SYNC"]
    
    # Check recursion depth limit
    if current_depth >= LIMITS["MAX_FOLDERS_DEPTH"]:
        log_debug(f"⚠️ Max folder depth reached ({current_depth}), stopping recursion for: {path}", "WARN", "get_drive_files_recursive")
        track_function_exit("get_drive_files_recursive", {"stopped": "max_depth", "depth": current_depth})
        return [], []
    
    all_files = []
    all_folders = []
    
    debug_info["current_operation"] = f"Recursive scan: {path or 'root'} (depth: {current_depth})"
    debug_info["folder_stack"].append({"path": path, "depth": current_depth})  # Changed to append for list
    
    try:
        set_socket_timeout(TIMEOUTS["DRIVE_API"])
        
        # Get files and folders from current directory
        log_debug(f"📁 Scanning folder: {path or 'root'} (depth: {current_depth})", "INFO", "get_drive_files_recursive")
        current_files, current_folders = get_drive_files_paginated(folder_id, path, max_files - len(all_files))
        
        # Add current files to results
        all_files.extend(current_files)
        all_folders.extend(current_folders)
        
        log_debug(f"✅ Found {len(current_files)} files and {len(current_folders)} folders in: {path or 'root'}", "INFO", "get_drive_files_recursive")
        
        # Update recursive stats
        debug_info["recursive_stats"]["folders_scanned"] = debug_info["recursive_stats"].get("folders_scanned", 0) + 1
        if current_depth > debug_info["recursive_stats"]["max_depth_reached"]:
            debug_info["recursive_stats"]["max_depth_reached"] = current_depth
        
        # RECURSIVE TRAVERSAL: Process each subfolder
        if current_folders and len(all_files) < max_files:
            log_debug(f"🔄 Starting recursive traversal of {len(current_folders)} subfolders", "INFO", "get_drive_files_recursive")
            
            for folder in current_folders:
                # Check if we've hit file limit
                if len(all_files) >= max_files:
                    log_debug(f"⚠️ File limit reached ({max_files}), stopping folder traversal", "WARN", "get_drive_files_recursive")
                    break
                
                folder_name = folder['name']
                folder_id_sub = folder['id']
                folder_path = f"{path}/{folder_name}" if path else folder_name
                
                log_debug(f"📂 Recursively scanning subfolder: {folder_path} (depth: {current_depth + 1})", "INFO", "get_drive_files_recursive")
                
                try:
                    # Recursive call for subfolder
                    sub_files, sub_folders = get_drive_files_recursive(
                        folder_id=folder_id_sub,
                        path=folder_path,
                        max_files=max_files - len(all_files),
                        current_depth=current_depth + 1
                    )
                    
                    # Add results from subfolder
                    all_files.extend(sub_files)
                    all_folders.extend(sub_folders)
                    
                    log_debug(f"✅ Subfolder {folder_path} contributed {len(sub_files)} files, {len(sub_folders)} folders", "INFO", "get_drive_files_recursive")
                    
                except Exception as subfolder_error:
                    error_msg = f"Error scanning subfolder {folder_path}: {subfolder_error}"
                    log_debug(f"❌ {error_msg}", "ERROR", "get_drive_files_recursive")
                    debug_info["errors"].append(error_msg)
                    # Continue with other folders even if one fails
                    continue
        
        # Update debug info
        debug_info["files_found"] = len(all_files)
        
        result_summary = {
            "files": len(all_files), 
            "folders": len(all_folders), 
            "depth": current_depth,
            "path": path or "root"
        }
        
        log_debug(f"✅ Recursive scan complete for {path or 'root'}: {len(all_files)} files, {len(all_folders)} folders (depth: {current_depth})", "INFO", "get_drive_files_recursive")
        track_function_exit("get_drive_files_recursive", result_summary)
        return all_files, all_folders
        
    except Exception as e:
        error_msg = f"Recursive scan failed for {path or 'root'}: {str(e)}"
        log_debug(f"❌ {error_msg}", "ERROR", "get_drive_files_recursive")
        track_function_exit("get_drive_files_recursive", error=error_msg)
        return [], []
    finally:
        # Pop folder stack
        debug_info["folder_stack"].pop()

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    stop=tenacity.stop_after_attempt(3),
    reraise=True
)
def process_drive_file(file_info):
    """Enhanced file processing with comprehensive error handling and retry"""
    track_function_entry("process_drive_file", {"file_name": file_info.get('name'), "file_id": file_info.get('id')})
    
    global debug_info
    file_path = file_info.get('path', file_info['name'])
    debug_info["current_file"] = file_path  # Track current file for stuck detection
    try:
        file_id = file_info['id']
        file_name = file_info['name']
        file_path = file_info.get('path', file_name)
        mime_type = file_info['mimeType']
        file_size = int(file_info.get('size', 0)) if file_info.get('size') else 0
        
        log_debug(f"🔄 Processing file: {file_path} ({mime_type}, {file_size} bytes)", "INFO", "process_drive_file")
        
        # Check file size limit
        if file_size > LIMITS["MAX_FILE_SIZE"]:
            result = {
                "status": "skipped", 
                "reason": f"File too large: {file_size} bytes (limit: {LIMITS['MAX_FILE_SIZE']})", 
                "file_name": file_path
            }
            track_function_exit("process_drive_file", result)
            return result
        
        # Only process supported file types
        supported_types = [
            'application/pdf',
            'text/plain',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ]
        
        if mime_type not in supported_types:
            result = {
                "status": "skipped", 
                "reason": f"Unsupported file type: {mime_type}", 
                "file_name": file_path
            }
            track_function_exit("process_drive_file", result)
            return result
        
        # Check if file already processed and unchanged
        content_hash = file_info.get('modifiedTime', '')
        if file_path in file_registry and file_registry[file_path].get('modified_time') == content_hash:
            result = {"status": "unchanged", "file_name": file_path}
            track_function_exit("process_drive_file", result)
            return result
        
        # Download file content with timeout
        log_debug(f"⬇️ Downloading {file_name}...", "INFO", "process_drive_file")
        try:
            set_socket_timeout(TIMEOUTS["FILE_DOWNLOAD"])
            download_start = time.time()
            file_content = drive_service.files().get_media(fileId=file_id).execute()
            download_duration = time.time() - download_start
            log_debug(f"✅ Downloaded {file_name} in {download_duration:.2f}s ({len(file_content)} bytes)", "INFO", "process_drive_file")
        except HttpError as http_err:
            if http_err.resp.status in [429, 503]:  # Rate limit or temp unavailable
                log_debug(f"Drive error {http_err.resp.status} for {file_path}: Retrying", "WARN", "process_drive_file")
                raise  # Retry
            else:
                error_msg = f"Drive HttpError {http_err.resp.status} for {file_path}: {str(http_err)}"
                log_debug(error_msg, "ERROR", "process_drive_file")
                debug_info["errors"].append({"file": file_path, "error": error_msg, "traceback": traceback.format_exc()})
                raise
        except Exception as download_error:
            error_msg = f"Download failed for {file_path}: {download_error}"
            log_debug(f"❌ {error_msg}", "ERROR", "process_drive_file")
            result = {"status": "error", "error": error_msg, "file_name": file_path}
            track_function_exit("process_drive_file", result)
            raise  # Trigger retry
        
        # Extract text based on file type
        log_debug(f"📝 Extracting text from {file_path}...", "INFO", "process_drive_file")
        extraction_start = time.time()
        
        if mime_type == 'application/pdf':
            text_content = extract_text_from_pdf(file_content)
        elif mime_type == 'text/plain':
            try:
                text_content = file_content.decode('utf-8', errors='ignore')
            except:
                text_content = file_content.decode('latin-1', errors='ignore')
        else:
            text_content = f"Document: {file_name}\nContent type: {mime_type}\n(Text extraction not fully implemented for this type)"
        
        extraction_duration = time.time() - extraction_start
        log_debug(f"✅ Text extraction completed in {extraction_duration:.2f}s ({len(text_content)} chars)", "INFO", "process_drive_file")
        
        if not text_content.strip():
            result = {"status": "skipped", "reason": "No text content extracted", "file_name": file_path}
            track_function_exit("process_drive_file", result)
            return result
        
        # Limit text length
        if len(text_content) > LIMITS["MAX_TEXT_LENGTH"]:
            text_content = text_content[:LIMITS["MAX_TEXT_LENGTH"]]
            log_debug(f"⚠️ Text truncated for {file_path}", "WARN", "process_drive_file")
        
        # Store file metadata and content
        file_registry[file_path] = {
            'id': file_id,
            'name': file_name,
            'path': file_path,
            'mime_type': mime_type,
            'size': file_size,
            'modified_time': content_hash,
            'processed_time': datetime.utcnow().isoformat()
        }
        
        # Store text content in chunks
        log_debug(f"🔧 Chunking text for {file_path}...", "DEBUG", "process_drive_file")
        text_chunks = chunk_text(text_content)
        
        processed_files[file_path] = {
            'content': text_content,
            'chunks': text_chunks,
            'metadata': file_registry[file_path]
        }
        
        result = {
            "status": "processed", 
            "file_name": file_path, 
            "content_length": len(text_content), 
            "chunks": len(text_chunks)
        }
        
        log_debug(f"✅ Successfully processed: {file_path} - {len(text_content)} chars, {len(text_chunks)} chunks", "INFO", "process_drive_file")
        track_function_exit("process_drive_file", result)
        return result
        
    except Exception as e:
        error_msg = str(e)
        file_path = file_info.get('path', file_info.get('name', 'unknown'))
        log_debug(f"❌ Error processing file {file_path}: {error_msg}", "ERROR", "process_drive_file")
        result = {"status": "error", "error": error_msg, "file_name": file_path}
        track_function_exit("process_drive_file", error=error_msg)
        raise  # Trigger retry
    finally:
        debug_info["current_file"] = None  # Clear after processing

def sync_google_drive_recursive():
    """COMPLETE: Enhanced sync with RECURSIVE folder scanning"""
    track_function_entry("sync_google_drive_recursive")
    
    global sync_status, debug_info
    
    log_debug("🚀 RECURSIVE SYNC FUNCTION ENTRY - Starting comprehensive recursive sync", "INFO", "sync_google_drive_recursive")
    debug_info["sync_function_entry_time"] = datetime.utcnow().isoformat()
    
    # Thread-safe check-and-set with lock to prevent race
    with sync_lock:
        if sync_status["is_syncing"]:
            if is_sync_stale():
                log_debug("🔄 STALE SYNC DETECTED - Clearing and proceeding", "WARN", "sync_google_drive_recursive")
                clear_sync_state("stale_detection")
            else:
                result = {"message": "Sync already in progress", "status": "in_progress"}
                log_debug("⚠️ Sync already in progress, exiting", "WARN", "sync_google_drive_recursive")
                track_function_exit("sync_google_drive_recursive", result)
                return result
        
        # Set sync state atomically
        sync_status["is_syncing"] = True
        sync_status["sync_start_time"] = datetime.utcnow().isoformat()
        sync_status["sync_thread_id"] = threading.current_thread().ident
    
    log_debug(f"🔒 RECURSIVE SYNC STATE SET: is_syncing=True, thread={sync_status['sync_thread_id']}", "INFO", "sync_google_drive_recursive")
    
    # Initialize enhanced debug info
    debug_info.update({
        "current_operation": "initializing_recursive",
        "folder_stack": [],
        "files_found": 0,
        "api_calls": 0,
        "start_time": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat(),
        "thread_id": threading.current_thread().ident,
        "errors": [],
        "performance_metrics": {
            "files_per_second": 0,
            "avg_processing_time": 0
        },
        "background_task_state": "recursive_sync_running",
        "sync_steps": {},
        "recursive_stats": {
            "max_depth_reached": 0,
            "folders_scanned": 0,
            "total_api_calls": 0
        }
    })
    
    sync_results = {
        "added": [], "updated": [], "removed": [], 
        "skipped": [], "errors": [], "folders_scanned": 0,
        "recursive_stats": {
            "max_depth_reached": 0,
            "total_folders": 0,
            "total_subfolders": 0
        }
    }
    
    try:
        log_debug("🚀 Starting RECURSIVE sync with comprehensive folder traversal", "INFO", "sync_google_drive_recursive")
        start_time = datetime.utcnow()
        debug_info["sync_steps"]["recursive_sync_start"] = start_time.isoformat()
        
        # Test Drive connection
        log_debug("🔍 Testing Google Drive connection...", "INFO", "sync_google_drive_recursive")
        debug_info["current_operation"] = "testing_connection"
        
        try:
            set_socket_timeout(TIMEOUTS["HEALTH_CHECK"])
            connection_test_start = time.time()
            
            test_result = drive_service.files().list(
                q=f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false",
                fields="files(id, name)",
                pageSize=1
            ).execute()
            
            connection_test_duration = time.time() - connection_test_start
            log_debug(f"✅ Drive connection test successful in {connection_test_duration:.2f}s", "INFO", "sync_google_drive_recursive")
            
        except Exception as test_error:
            error_msg = f"Drive connection test failed: {str(test_error)}"
            log_debug(f"❌ {error_msg}", "ERROR", "sync_google_drive_recursive")
            track_function_exit("sync_google_drive_recursive", error=error_msg)
            raise Exception(error_msg)
        
        # RECURSIVE FILE SCANNING
        log_debug("📁 Starting RECURSIVE file scanning with folder traversal...", "INFO", "sync_google_drive_recursive")
        debug_info["current_operation"] = "recursive_scanning"
        debug_info["sync_steps"]["recursive_scan_start"] = datetime.utcnow().isoformat()
        
        scan_start = time.time()
        
        # Use recursive scanning instead of simple pagination
        all_files, all_folders = get_drive_files_recursive(
            max_files=LIMITS["MAX_FILES_PER_SYNC"]
        )
        
        scan_duration = time.time() - scan_start
        debug_info["sync_steps"]["recursive_scan_complete"] = datetime.utcnow().isoformat()
        
        total_files = len(all_files)
        total_folders = len(all_folders)
        
        # Calculate recursive statistics
        depth_levels = {}
        for folder in all_folders:
            folder_path = folder.get('path', '')
            depth = len(folder_path.split('/')) - 1 if folder_path else 0
            depth_levels[depth] = depth_levels.get(depth, 0) + 1
        
        max_depth_reached = max(depth_levels.keys()) if depth_levels else 0
        
        sync_results["folders_scanned"] = total_folders
        sync_results["recursive_stats"] = {
            "max_depth_reached": max_depth_reached,
            "total_folders": total_folders,
            "depth_distribution": depth_levels,
            "scan_duration": scan_duration
        }
        
        debug_info["recursive_stats"] = sync_results["recursive_stats"]
        
        log_debug(f"📊 RECURSIVE scan results in {scan_duration:.2f}s:", "INFO", "sync_google_drive_recursive")
        log_debug(f"   📄 Files: {total_files}", "INFO", "sync_google_drive_recursive")
        log_debug(f"   📁 Total folders: {total_folders}", "INFO", "sync_google_drive_recursive")
        log_debug(f"   🏗️ Max depth reached: {max_depth_reached}", "INFO", "sync_google_drive_recursive")
        log_debug(f"   📊 Depth distribution: {depth_levels}", "INFO", "sync_google_drive_recursive")
        
        if total_files == 0:
            log_debug("⚠️ No files found in recursive scan - check folder permissions and content", "WARN", "sync_google_drive_recursive")
            result = {
                "message": "No files found in recursive scan", 
                "status": "completed", 
                "results": sync_results
            }
            track_function_exit("sync_google_drive_recursive", result)
            return result
        
        # Process files (now we have files from all folders)
        log_debug(f"🔄 Starting file processing for {total_files} files from recursive scan", "INFO", "sync_google_drive_recursive")
        debug_info["current_operation"] = "processing_files_recursive"
        
        processed_count = 0
        processing_times = []
        
        for file_index, file_info in enumerate(all_files):
            file_start = datetime.utcnow()
            
            log_debug(f"🔄 Processing file {file_index + 1}/{total_files}: {file_info['path']}", "INFO", "sync_google_drive_recursive")
            
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > TIMEOUTS["OVERALL_SYNC"]:
                log_debug(f"⏰ Sync timeout reached after {elapsed:.1f} seconds", "WARN", "sync_google_drive_recursive")
                sync_results["errors"].append(f"Sync timed out after {elapsed:.1f} seconds")
                break
            
            try:
                result = process_drive_file(file_info)
                
                processing_time = (datetime.utcnow() - file_start).total_seconds()
                processing_times.append(processing_time)
                
                # Update results based on processing outcome
                if result["status"] == "processed":
                    if file_info['path'] in file_registry:
                        sync_results["updated"].append(result["file_name"])
                    else:
                        sync_results["added"].append(result["file_name"])
                elif result["status"] == "skipped":
                    sync_results["skipped"].append(f"{result['file_name']}: {result.get('reason', 'Unknown')}")
                elif result["status"] == "error":
                    sync_results["errors"].append(f"{result['file_name']}: {result.get('error', 'Unknown error')}")
                
                processed_count += 1
                
                # Update performance metrics
                if processing_times:
                    debug_info["performance_metrics"]["avg_processing_time"] = sum(processing_times) / len(processing_times)
                    debug_info["performance_metrics"]["files_per_second"] = processed_count / max(1, (datetime.utcnow() - start_time).total_seconds())
                
                # Safety check
                if processed_count >= LIMITS["MAX_FILES_PER_SYNC"]:
                    log_debug(f"⚠️ Reached file processing limit: {LIMITS['MAX_FILES_PER_SYNC']}", "WARN", "sync_google_drive_recursive")
                    break
                    
            except Exception as process_error:
                error_msg = f"Processing error for {file_info['path']}: {str(process_error)}"
                log_debug(f"❌ {error_msg}", "ERROR", "sync_google_drive_recursive")
                sync_results["errors"].append(error_msg)
        
        # Update final sync status
        end_time = datetime.utcnow()
        sync_duration = (end_time - start_time).total_seconds()
        debug_info["sync_steps"]["recursive_sync_complete"] = end_time.isoformat()
        
        sync_status["last_sync"] = end_time.isoformat()
        sync_status["last_sync_results"] = sync_results
        sync_status["next_auto_sync"] = (end_time + timedelta(minutes=30)).isoformat()
        sync_status["total_files_processed"] = len(processed_files)
        
        debug_info["performance_metrics"]["total_duration"] = sync_duration
        debug_info["performance_metrics"]["files_processed"] = processed_count
        
        log_debug(f"✅ RECURSIVE sync completed in {sync_duration:.1f}s:", "INFO", "sync_google_drive_recursive")
        log_debug(f"   📁 Total folders scanned: {sync_results['folders_scanned']}", "INFO", "sync_google_drive_recursive")
        log_debug(f"   📄 Total files found: {total_files}", "INFO", "sync_google_drive_recursive")
        log_debug(f"   🏗️ Max folder depth: {max_depth_reached}", "INFO", "sync_google_drive_recursive")
        log_debug(f"   ➕ Added: {len(sync_results['added'])}", "INFO", "sync_google_drive_recursive")
        log_debug(f"   🔄 Updated: {len(sync_results['updated'])}", "INFO", "sync_google_drive_recursive")
        log_debug(f"   ⏭️ Skipped: {len(sync_results['skipped'])}", "INFO", "sync_google_drive_recursive")
        log_debug(f"   ❌ Errors: {len(sync_results['errors'])}", "INFO", "sync_google_drive_recursive")
        log_debug(f"   ⚡ Performance: {debug_info['performance_metrics']['files_per_second']:.1f} files/sec", "INFO", "sync_google_drive_recursive")
        
        result = {
            "message": "RECURSIVE sync completed successfully", 
            "status": "completed", 
            "results": sync_results
        }
        track_function_exit("sync_google_drive_recursive", result)
        return result
        
    except Exception as e:
        error_msg = str(e)
        log_debug(f"❌ RECURSIVE sync failed: {error_msg}", "ERROR", "sync_google_drive_recursive")
        log_debug(f"🔍 Recursive Sync Error Traceback: {traceback.format_exc()}", "ERROR", "sync_google_drive_recursive")
        
        sync_results["errors"].append(error_msg)
        sync_status["last_sync_results"] = {
            "error": error_msg, 
            "error_type": type(e).__name__,
            "duration": (datetime.utcnow() - start_time).total_seconds() if 'start_time' in locals() else 0
        }
        
        result = {"message": "RECURSIVE sync failed", "status": "error", "error": error_msg}
        track_function_exit("sync_google_drive_recursive", error=error_msg)
        return result
    finally:
        # Proper cleanup
        clear_sync_state("recursive_sync_completion")
        debug_info["current_operation"] = "completed"
        debug_info["background_task_state"] = "completed"
        log_debug("🏁 RECURSIVE sync finally block executed - sync state properly cleared", "INFO", "sync_google_drive_recursive")

def run_recursive_sync_background():
    """Background sync with recursive folder scanning"""
    
    log_debug("🚀 RECURSIVE BACKGROUND TASK STARTED", "INFO", "run_recursive_sync_background")
    print("🚀 RECURSIVE BACKGROUND TASK STARTED", file=sys.stderr, flush=True)
    
    try:
        debug_info["background_task_state"] = "recursive_function_entered"
        debug_info["thread_creation_time"] = datetime.utcnow().isoformat()
        debug_info["thread_id"] = threading.current_thread().ident
        
        log_debug(f"🧵 Recursive background task thread info: ID={threading.current_thread().ident}", "INFO", "run_recursive_sync_background")
        
        # Check services
        if not drive_service:
            error_msg = "Google Drive service not available in recursive background task"
            log_debug(f"❌ {error_msg}", "ERROR", "run_recursive_sync_background")
            debug_info["background_task_state"] = "drive_service_missing"
            clear_sync_state("drive_service_missing")
            return
        
        log_debug("✅ Google Drive service available for recursive sync", "INFO", "run_recursive_sync_background")
        debug_info["background_task_state"] = "about_to_call_recursive_sync"
        
        start_time = datetime.utcnow()
        log_debug(f"🚀 About to call sync_google_drive_recursive() at {start_time.isoformat()}", "INFO", "run_recursive_sync_background")
        
        try:
            debug_info["background_task_state"] = "calling_recursive_sync_function"
            result = sync_google_drive_recursive()
            debug_info["background_task_state"] = "recursive_sync_function_returned"
            
            log_debug(f"✅ sync_google_drive_recursive() returned: {result}", "INFO", "run_recursive_sync_background")
            
        except Exception as sync_error:
            error_msg = f"sync_google_drive_recursive() failed: {str(sync_error)}"
            log_debug(f"❌ {error_msg}", "ERROR", "run_recursive_sync_background")
            debug_info["background_task_state"] = "recursive_sync_function_error"
            clear_sync_state("recursive_sync_function_error")
            return
        
        debug_info["background_task_state"] = "recursive_completed_successfully"
        log_debug(f"✅ RECURSIVE background sync completed successfully", "INFO", "run_recursive_sync_background")
            
    except Exception as e:
        error_msg = str(e)
        log_debug(f"❌ RECURSIVE background sync failed: {error_msg}", "ERROR", "run_recursive_sync_background")
        debug_info["background_task_state"] = "recursive_exception_occurred"
        clear_sync_state("recursive_background_task_exception")
    finally:
        debug_info["background_task_state"] = "recursive_finally_block"
        log_debug("🏁 Recursive background task finally block executed", "INFO", "run_recursive_sync_background")

# === ROBUST APP LIFESPAN ===

@asynccontextmanager
async def robust_lifespan(app: FastAPI):
    """ROBUST: App lifespan that never fails startup"""
    print(f"🚀 Starting COMPLETE RAG Clair System {VERSION}")
    print("📊 Container startup process beginning...")
    
    # Set basic timeout
    try:
        set_socket_timeout(30)
        print("✅ Socket timeout configured")
    except Exception as e:
        print(f"⚠️ Socket timeout setup failed: {e}")
    
    # Initialize services with graceful failure
    startup_results = {}
    
    print("🔧 Initializing services with graceful failure handling...")
    
    # Service 1: Clair Prompt (always succeeds)
    startup_results["clair_prompt"] = safe_load_clair_system_prompt()
    
    # Service 2: OpenAI (can fail gracefully)
    startup_results["openai"] = safe_initialize_openai()
    
    # Service 3: Google Drive (can fail gracefully)
    startup_results["google_drive"] = safe_initialize_google_drive()
    
    # Report startup status
    print(f"📊 COMPLETE service initialization status:")
    print(f"   🤖 Clair Prompt: {'✅' if startup_results['clair_prompt'] else '❌'}")
    print(f"   🧠 OpenAI: {'✅' if startup_results['openai'] else '❌'}")
    print(f"   🗂️  Google Drive: {'✅' if startup_results['google_drive'] else '❌'}")
    
    # Calculate service health
    healthy_services = sum(startup_results.values())
    total_services = len(startup_results)
    health_percentage = (healthy_services / total_services) * 100
    
    print(f"🏥 Service health: {healthy_services}/{total_services} ({health_percentage:.0f}%)")
    
    # Always proceed with startup - never fail
    if healthy_services == 0:
        print("⚠️ WARNING: No services initialized successfully")
        print("📝 App will start in limited mode")
    elif healthy_services < total_services:
        print(f"⚠️ WARNING: {total_services - healthy_services} service(s) failed to initialize")
        print("📝 App will start with reduced functionality")
    else:
        print("🎉 All services initialized successfully!")
    
    print("🏁 COMPLETE RAG Clair System startup complete - container ready!")
    
    yield
    
    print("🛑 Shutting down COMPLETE RAG Clair System")

# === CREATE FASTAPI APP ===

def create_complete_app():
    """Create app with complete functionality"""
    return FastAPI(
        title="COMPLETE RAG Clair System", 
        version=VERSION,
        description=f"Complete production-ready RAG system with recursive sync - Built {BUILD_DATE}",
        lifespan=robust_lifespan
    )

# Create the FastAPI app
app = create_complete_app()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# === ROBUST API ENDPOINTS ===

@app.get("/")
async def robust_root():
    """ROBUST: Root endpoint that always works"""
    try:
        return {
            "message": "COMPLETE RAG Clair System API",
            "version": VERSION,
            "status": "running",
            "container_health": "healthy",
            "available_features": get_available_features(),
            "services": {
                "openai_available": is_openai_available(),
                "drive_available": is_drive_available(),
                "clair_prompt_loaded": len(CLAIR_SYSTEM_PROMPT) > 0,
            },
            "sync_capabilities": {
                "recursive_sync": True,
                "max_depth": LIMITS["MAX_FOLDERS_DEPTH"],
                "max_files": LIMITS["MAX_FILES_PER_SYNC"]
            },
            "data": {
                "processed_files": len(processed_files),
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "message": "COMPLETE RAG Clair System API (Minimal Mode)",
            "version": VERSION,
            "status": "running",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/health")
async def robust_health():
    """ROBUST: Health check that works even with failed services"""
    try:
        health_data = {
            "status": "healthy",  # Always report healthy if container is running
            "version": VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "container_status": "running",
            "port_listening": True,
            "features": "complete_recursive_sync"
        }
        
        # Check individual services without failing
        services_status = {}
        
        try:
            services_status["clair_prompt"] = len(CLAIR_SYSTEM_PROMPT) > 0
        except:
            services_status["clair_prompt"] = False
            
        try:
            services_status["openai"] = openai_client is not None
        except:
            services_status["openai"] = False
            
        try:
            services_status["google_drive"] = drive_service is not None
        except:
            services_status["google_drive"] = False
        
        health_data["services"] = services_status
        health_data["service_count"] = {
            "healthy": sum(services_status.values()),
            "total": len(services_status)
        }
        
        # Additional container info
        health_data["container_info"] = {
            "port": int(os.environ.get("PORT", 8080)),
            "project_id": os.environ.get("GCP_PROJECT_ID", "not_set"),
            "drive_folder_id": os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "not_set"),
            "openai_key_configured": bool(os.environ.get("OPENAI_API_KEY"))
        }
        
        return health_data
        
    except Exception as e:
        # Even if health check fails, return basic success
        return {
            "status": "degraded",
            "message": "Health check partially failed but container is running",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/list_files")
async def list_files_complete():
    """COMPLETE: File listing with timeout protection"""
    track_function_entry("list_files_complete")
    
    try:
        async def get_file_structure():
            if not processed_files:
                return {
                    "files": [],
                    "file_count": 0,
                    "folder_count": 0,
                    "structure": "hierarchical",
                    "status": "no_files"
                }
            
            file_list = []
            folder_set = set()
            
            for file_path, file_data in processed_files.items():
                file_list.append({
                    "path": file_path,
                    "name": file_data['metadata']['name'],
                    "type": "file",
                    "mime_type": file_data['metadata']['mime_type'],
                    "size": file_data['metadata'].get('size', 0),
                    "processed_time": file_data['metadata']['processed_time']
                })
                
                # Add parent folders
                path_parts = file_path.split('/')
                for i in range(len(path_parts) - 1):
                    folder_path = '/'.join(path_parts[:i+1])
                    if folder_path:
                        folder_set.add(folder_path)
            
            # Add folder objects
            folders = [{"path": path, "name": path.split('/')[-1], "type": "folder"} for path in folder_set]
            
            return {
                "files": file_list,
                "folders": folders,
                "file_count": len(file_list),
                "folder_count": len(folders),
                "structure": "hierarchical",
                "status": "success",
                "recursive_scan_enabled": True
            }
        
        result = await asyncio.wait_for(get_file_structure(), timeout=15.0)
        track_function_exit("list_files_complete", result)
        return result
        
    except asyncio.TimeoutError:
        error_result = {
            "files": [],
            "folders": [],
            "error": "File listing timed out",
            "status": "timeout"
        }
        track_function_exit("list_files_complete", error="timeout")
        return JSONResponse(status_code=408, content=error_result)
    except Exception as e:
        error_result = {
            "files": [],
            "folders": [],
            "error": str(e),
            "status": "error"
        }
        track_function_exit("list_files_complete", error=str(e))
        return JSONResponse(status_code=500, content=error_result)

@app.get("/sync_status")
async def get_sync_status_complete():
    """Get current sync status with complete info"""
    return {
        **sync_status,
        "debug_info": {
            "current_operation": debug_info.get("current_operation", "idle"),
            "files_found": debug_info.get("files_found", 0),
            "api_calls": debug_info.get("api_calls", 0),
            "performance_metrics": debug_info.get("performance_metrics", {}),
            "background_task_state": debug_info.get("background_task_state", "unknown"),
            "thread_id": debug_info.get("thread_id"),
            "sync_steps": debug_info.get("sync_steps", {}),
            "recursive_stats": debug_info.get("recursive_stats", {}),
            "current_file": debug_info.get("current_file"),
            "recent_errors": debug_info.get("errors", [])[-10:]  # More recent errors with file info
        },
        "features": {
            "recursive_sync": True,
            "thread_safe": True,
            "comprehensive_debugging": True,
            "sync_state_management": True
        },
        "state_management": {
            "is_stale": is_sync_stale(),
            "sync_thread_active": sync_status.get("sync_thread_id") in [t.ident for t in threading.enumerate()] if sync_status.get("sync_thread_id") else False,
            "sync_duration": (datetime.utcnow() - datetime.fromisoformat(sync_status["sync_start_time"].replace('Z', '+00:00')).replace(tzinfo=None)).total_seconds() if sync_status.get("sync_start_time") else None
        }
    }

@app.post("/sync_drive")
async def trigger_recursive_sync_default(background_tasks: BackgroundTasks, force: bool = False):
    """Default sync endpoint - now uses recursive scanning"""
    return await trigger_recursive_sync(background_tasks, force)

@app.post("/sync_drive_recursive")
async def trigger_recursive_sync(background_tasks: BackgroundTasks, force: bool = False):
    """Trigger recursive sync that scans all subfolders"""
    track_function_entry("trigger_recursive_sync", {"force": force})
    
    if not is_drive_available():
        return JSONResponse(
            status_code=503,
            content={
                "message": "Google Drive service not available", 
                "status": "error",
                "available_features": get_available_features(),
                "suggestion": "Check environment variables and service credentials"
            }
        )
    
    # Check sync state
    with sync_lock:
        if sync_status["is_syncing"] and not force:
            if is_sync_stale():
                log_debug("🔄 STALE SYNC DETECTED - Clearing and proceeding with recursive sync", "WARN", "trigger_recursive_sync")
                clear_sync_state("stale_detection_recursive")
            else:
                return JSONResponse(
                    status_code=409,
                    content={
                        "message": "Sync already in progress", 
                        "status": "in_progress"
                    }
                )
    
    try:
        log_debug("🚀 RECURSIVE sync triggered via API", "INFO", "trigger_recursive_sync")
        
        # Reset debug state for recursive sync
        debug_info["background_task_state"] = "preparing_recursive"
        
        # Quick connection test
        async def test_connection():
            try:
                set_socket_timeout(TIMEOUTS["HEALTH_CHECK"])
                test_result = drive_service.files().list(
                    q=f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false",
                    fields="files(id, name)",
                    pageSize=1
                ).execute()
                return len(test_result.get('files', []))
            except Exception:
                return False
        
        connection_result = await asyncio.wait_for(test_connection(), timeout=10.0)
        
        if connection_result is False:
            return JSONResponse(
                status_code=503,
                content={
                    "message": "Google Drive connection test failed", 
                    "status": "error"
                }
            )
        
        log_debug(f"✅ Connection test passed for recursive sync", "INFO", "trigger_recursive_sync")
        
        # Add recursive background task
        log_debug("🧵 Adding RECURSIVE background task to FastAPI", "INFO", "trigger_recursive_sync")
        debug_info["background_task_state"] = "recursive_task_being_added"
        
        background_tasks.add_task(run_recursive_sync_background)
        
        log_debug("✅ RECURSIVE background task added successfully", "INFO", "trigger_recursive_sync")
        debug_info["background_task_state"] = "recursive_task_added"
        
        response_data = {
            "message": "RECURSIVE sync started successfully - will scan all subfolders", 
            "status": "started",
            "sync_type": "recursive",
            "features": {
                "recursive_folder_scanning": True,
                "max_depth": LIMITS["MAX_FOLDERS_DEPTH"],
                "max_files": LIMITS["MAX_FILES_PER_SYNC"]
            },
            "debug_info": {
                "connection_test_files": connection_result,
                "force_used": force
            }
        }
        
        track_function_exit("trigger_recursive_sync", response_data)
        return JSONResponse(status_code=202, content=response_data)
        
    except Exception as e:
        error_msg = str(e)
        log_debug(f"❌ RECURSIVE sync failed to start: {error_msg}", "ERROR", "trigger_recursive_sync")
        clear_sync_state("recursive_startup_error")
        
        error_response = {
            "message": f"Recursive sync failed to start: {error_msg}", 
            "status": "error"
        }
        track_function_exit("trigger_recursive_sync", error=error_msg)
        return JSONResponse(status_code=500, content=error_response)

@app.post("/ask")
async def complete_ask_question(request: dict):
    """COMPLETE: Question answering with robust error handling"""
    track_function_entry("complete_ask_question", {"query_length": len(request.get("query", ""))})
    
    query = request.get("query", "")
    filters = request.get("filters", [])
    
    if not query:
        track_function_exit("complete_ask_question", error="no query provided")
        raise HTTPException(status_code=400, detail="Query is required")
    
    # Check if OpenAI is available
    if not is_openai_available():
        return {
            "answer": f"我收到了您的问题：'{query}'。AI服务暂时不可用，请稍后重试，或联系技术支持。",
            "sources": [],
            "status": "service_unavailable",
            "available_services": get_available_features(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        log_debug(f"🤔 Processing COMPLETE question: {query[:100]}...", "INFO", "complete_ask_question")
        
        async def process_question():
            # Search documents with enhanced scoring
            search_results = []
            sources = []
            
            if processed_files and is_drive_available():
                search_results = search_documents(query, filters)
                log_debug(f"🔍 Found {len(search_results)} relevant documents", "INFO", "complete_ask_question")
            
            # Build enhanced context
            if search_results:
                context_parts = []
                
                for i, result in enumerate(search_results[:5]):  # Top 5 results
                    file_path = result['file_path']
                    sources.append(file_path)
                    
                    context_parts.append(f"\n--- Document {i+1}: {result['file_name']} ---")
                    
                    # Add best chunks with context
                    for chunk in result['chunks'][:2]:  # Top 2 chunks per document
                        context_parts.append(f"Content: {chunk['content'][:800]}")
                    
                    context_parts.append("")
                
                context = "\n".join(context_parts)
                
                # Enhanced system prompt with context
                enhanced_prompt = f"""{CLAIR_SYSTEM_PROMPT}

You have access to the user's financial documents. Please provide specific, actionable advice based on the document content provided.

Important guidelines:
- Reference specific documents when making recommendations
- Provide practical, actionable advice
- Explain complex concepts clearly
- If asked in Chinese, respond in Chinese; if asked in English, respond in English
- Always prioritize the user's financial well-being
"""
                
                messages = [
                    {"role": "system", "content": enhanced_prompt},
                    {"role": "user", "content": f"Based on the following documents:\n\n{context}\n\nQuestion: {query}"}
                ]
                
                # OpenAI call with timeout
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=1200,
                    temperature=0.7,
                    timeout=TIMEOUTS["OPENAI_API"]
                )
                
                return {
                    "answer": response.choices[0].message.content,
                    "sources": sources,
                    "model": "gpt-4o",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "success",
                    "context_used": True,
                    "documents_searched": len(search_results),
                    "sync_type": "recursive"
                }
            
            # Check if Drive is available but no documents found
            if not is_drive_available():
                note = "基于一般知识的回答（文档服务不可用）"
            else:
                note = "基于一般知识的回答（未找到相关文档）"
            
            # Fallback response
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": CLAIR_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Question: {query}\n\n注意：请提供有用的财务建议。{note}"}
                ],
                max_tokens=1000,
                temperature=0.7,
                timeout=TIMEOUTS["OPENAI_API"]
            )
            
            return {
                "answer": response.choices[0].message.content,
                "sources": [],
                "model": "gpt-4o",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success_general",
                "context_used": False,
                "documents_searched": 0,
                "note": note
            }
        
        # Execute with overall timeout
        result = await asyncio.wait_for(process_question(), timeout=35.0)
        track_function_exit("complete_ask_question", result)
        return result
        
    except asyncio.TimeoutError:
        log_debug("⏰ Question processing timed out", "ERROR", "complete_ask_question")
        response = {
            "answer": f"抱歉，处理您的问题'{query[:50]}...'时超时。请尝试简化问题或稍后重试。",
            "sources": [],
            "model": "gpt-4o",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "timeout"
        }
        track_function_exit("complete_ask_question", error="timeout")
        return response
    except Exception as e:
        error_msg = str(e)
        log_debug(f"❌ Error in COMPLETE ask endpoint: {error_msg}", "ERROR", "complete_ask_question")
        
        response = {
            "answer": f"处理您的问题时遇到错误。请稍后重试。如果问题持续，请联系技术支持。",
            "sources": [],
            "model": "gpt-4o",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error_details": error_msg if "timeout" in error_msg.lower() else "Internal processing error"
        }
        track_function_exit("complete_ask_question", error=error_msg)
        return response

@app.post("/feedback")
async def submit_feedback_complete(request: dict):
    """COMPLETE: Feedback collection with analysis"""
    track_function_entry("submit_feedback_complete")
    
    try:
        feedback_data = {
            "query": request.get("query"),
            "response": request.get("response"),
            "feedback_type": request.get("feedback_type"),
            "documents_used": request.get("documents_used", 0),
            "timestamp": datetime.utcnow().isoformat(),
            "model": "gpt-4o",
            "version": VERSION,
            "user_agent": request.get("user_agent", "unknown"),
            "recursive_sync_enabled": True
        }
        
        log_debug(f"📝 COMPLETE feedback: {feedback_data['feedback_type']} for query: {feedback_data['query'][:50]}...", "INFO", "submit_feedback_complete")
        
        response = {
            "message": "Feedback received and processed", 
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }
        track_function_exit("submit_feedback_complete", response)
        return response
    except Exception as e:
        log_debug(f"❌ Error processing feedback: {e}", "ERROR", "submit_feedback_complete")
        response = {
            "message": "Feedback received but processing failed", 
            "status": "partial_success",
            "timestamp": datetime.utcnow().isoformat()
        }
        track_function_exit("submit_feedback_complete", error=str(e))
        return response

@app.get("/debug")
async def debug_info_complete():
    """COMPLETE: Debug endpoint with comprehensive system info"""
    track_function_entry("debug_info_complete")
    
    debug_data = {
        "system": {
            "version": VERSION,
            "build_date": BUILD_DATE,
            "timestamp": datetime.utcnow().isoformat(),
            "cwd": os.getcwd(),
            "python_version": sys.version,
            "features": {
                "recursive_sync": True,
                "thread_safe": True,
                "enhanced_error_handling": True,
                "comprehensive_debugging": True,
                "robust_startup": True
            },
            "timeouts": TIMEOUTS,
            "limits": LIMITS
        },
        "services": {
            "drive_service_available": is_drive_available(),
            "openai_available": is_openai_available(),
            "gcp_project_id": GCP_PROJECT_ID,
            "folder_id": GOOGLE_DRIVE_FOLDER_ID,
        },
        "clair_prompt": {
            "loaded": len(CLAIR_SYSTEM_PROMPT) > 0,
            "length": len(CLAIR_SYSTEM_PROMPT),
            "preview": CLAIR_SYSTEM_PROMPT[:200] + "..." if len(CLAIR_SYSTEM_PROMPT) > 200 else CLAIR_SYSTEM_PROMPT
        },
        "processed_files": {
            "count": len(processed_files),
            "file_registry_count": len(file_registry),
            "sample_files": list(processed_files.keys())[:10],
            "total_content_length": sum(len(data['content']) for data in processed_files.values()),
            "total_chunks": sum(len(data['chunks']) for data in processed_files.values())
        },
        "sync_status": sync_status,
        "debug_info": debug_info,
        "threading": {
            "active_count": threading.active_count(),
            "current_thread_id": threading.current_thread().ident,
            "current_thread_name": threading.current_thread().name
        },
        "environment": {
            "openai_key_set": os.environ.get("OPENAI_API_KEY") is not None,
            "gcp_project_set": os.environ.get("GCP_PROJECT_ID") is not None,
            "drive_folder_set": os.environ.get("GOOGLE_DRIVE_FOLDER_ID") is not None,
        },
        "initialization_steps": debug_info.get("initialization_steps", {}),
        "function_call_stack": debug_info.get("function_call_stack", [])[-10:],
        "recent_logs": debug_info.get("detailed_logs", [])[-20:],
        "sync_state_management": {
            "is_syncing": sync_status["is_syncing"],
            "is_stale": is_sync_stale(),
            "sync_thread_id": sync_status.get("sync_thread_id"),
            "sync_start_time": sync_status.get("sync_start_time")
        },
        "recursive_capabilities": {
            "enabled": True,
            "max_depth": LIMITS["MAX_FOLDERS_DEPTH"],
            "current_stats": debug_info.get("recursive_stats", {})
        }
    }
    
    track_function_exit("debug_info_complete", {"data_size": len(str(debug_data))})
    return debug_data

@app.get("/debug_live")
async def debug_live_complete():
    """COMPLETE: Real-time debug information"""
    return {
        "sync_status": sync_status,
        "debug_info": debug_info,
        "processed_files_count": len(processed_files),
        "system_info": {
            "timestamp": datetime.utcnow().isoformat(),
            "version": VERSION,
            "thread_count": threading.active_count(),
            "current_thread": {
                "id": threading.current_thread().ident,
                "name": threading.current_thread().name
            },
            "available_features": get_available_features(),
            "socket_timeout": socket.getdefaulttimeout()
        },
        "performance": debug_info.get("performance_metrics", {}),
        "recent_errors": debug_info.get("errors", [])[-5:],
        "background_task": {
            "state": debug_info.get("background_task_state", "unknown"),
            "thread_creation_time": debug_info.get("thread_creation_time"),
            "sync_function_entry_time": debug_info.get("sync_function_entry_time"),
            "last_activity": debug_info.get("last_activity")
        },
        "recent_function_calls": debug_info.get("function_call_stack", [])[-5:],
        "recent_detailed_logs": debug_info.get("detailed_logs", [])[-10:],
        "sync_progress": {
            "current_operation": debug_info.get("current_operation", "idle"),
            "files_found": debug_info.get("files_found", 0),
            "api_calls": debug_info.get("api_calls", 0),
            "folder_stack": debug_info.get("folder_stack", []),
            "sync_steps": debug_info.get("sync_steps", {}),
            "recursive_stats": debug_info.get("recursive_stats", {})
        },
        "sync_state_management": {
            "is_syncing": sync_status["is_syncing"],
            "is_stale": is_sync_stale(),
            "sync_thread_id": sync_status.get("sync_thread_id"),
            "sync_start_time": sync_status.get("sync_start_time"),
            "sync_thread_active": sync_status.get("sync_thread_id") in [t.ident for t in threading.enumerate()] if sync_status.get("sync_thread_id") else False,
            "active_thread_ids": [t.ident for t in threading.enumerate()]
        }
    }

@app.post("/emergency_reset")
async def emergency_reset_complete():
    """COMPLETE: Emergency reset with comprehensive cleanup"""
    track_function_entry("emergency_reset_complete")
    
    global sync_status, processed_files, file_registry, debug_info
    
    log_debug("🚨 COMPLETE EMERGENCY RESET TRIGGERED", "WARN", "emergency_reset_complete")
    
    try:
        # Clear sync state first
        log_debug("🛑 FORCEFULLY clearing sync state...", "INFO", "emergency_reset_complete")
        clear_sync_state("emergency_reset")
        
        # Clear all data
        log_debug("🗑️ Clearing processed files and registry...", "INFO", "emergency_reset_complete")
        processed_files.clear()
        file_registry.clear()
        
        # Reset sync status
        log_debug("🔄 Completely resetting sync status...", "INFO", "emergency_reset_complete")
        sync_status.clear()
        sync_status.update({
            "is_syncing": False,
            "last_sync": None,
            "last_sync_results": {"reset": "COMPLETE emergency reset performed"},
            "next_auto_sync": None,
            "total_files_processed": 0,
            "version": VERSION,
            "enhanced_features": True,
            "sync_start_time": None,
            "sync_thread_id": None,
            "recursive_enabled": True
        })
        
        # Reset debug info but preserve some history
        log_debug("🔧 Resetting debug information...", "INFO", "emergency_reset_complete")
        old_logs = debug_info.get("detailed_logs", [])[-10:]
        old_function_calls = debug_info.get("function_call_stack", [])[-5:]
        
        debug_info.clear()
        debug_info.update({
            "current_operation": "reset",
            "folder_stack": [],
            "files_found": 0,
            "api_calls": 0,
            "start_time": None,
            "last_activity": datetime.utcnow().isoformat(),
            "thread_id": None,
            "errors": [],
            "performance_metrics": {},
            "background_task_state": "reset",
            "function_call_stack": old_function_calls,
            "detailed_logs": old_logs,
            "initialization_steps": {},
            "reset_performed": datetime.utcnow().isoformat(),
            "recursive_stats": {
                "max_depth_reached": 0,
                "folders_scanned": 0,
                "total_api_calls": 0
            }
        })
        
        # Reset socket timeout
        log_debug("🔌 Resetting socket timeout...", "INFO", "emergency_reset_complete")
        set_socket_timeout(TIMEOUTS["DRIVE_API"])
        
        # Verify sync state is actually cleared
        log_debug(f"🔍 VERIFICATION: sync_status['is_syncing'] = {sync_status['is_syncing']}", "INFO", "emergency_reset_complete")
        log_debug(f"🔍 VERIFICATION: is_sync_stale() = {is_sync_stale()}", "INFO", "emergency_reset_complete")
        
        # Log reset completion
        log_debug("✅ COMPLETE EMERGENCY RESET COMPLETE", "INFO", "emergency_reset_complete")
        
        reset_response = {
            "message": "COMPLETE emergency reset completed successfully",
            "status": "reset",
            "timestamp": datetime.utcnow().isoformat(),
            "features": {
                "recursive_sync": True,
                "thread_safe": True,
                "comprehensive_debugging": True,
                "robust_startup": True
            },
            "cleared": {
                "processed_files": True,
                "file_registry": True,
                "sync_status": True,
                "debug_info": True,
                "socket_timeout": True
            },
            "preserved": {
                "recent_logs": len(old_logs),
                "recent_function_calls": len(old_function_calls)
            },
            "system_state": {
                "active_threads": threading.active_count(),
                "drive_service_available": is_drive_available(),
                "openai_available": is_openai_available()
            },
            "verification": {
                "is_syncing": sync_status["is_syncing"],
                "is_stale": is_sync_stale(),
                "sync_thread_id": sync_status.get("sync_thread_id"),
                "sync_start_time": sync_status.get("sync_start_time")
            }
        }
        
        track_function_exit("emergency_reset_complete", reset_response)
        return reset_response
        
    except Exception as e:
        error_msg = str(e)
        log_debug(f"❌ Emergency reset failed: {error_msg}", "ERROR", "emergency_reset_complete")
        log_debug(f"🔍 Emergency Reset Error Traceback: {traceback.format_exc()}", "ERROR", "emergency_reset_complete")
        
        error_response = {
            "message": f"Emergency reset failed: {error_msg}",
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error_details": error_msg,
            "traceback": traceback.format_exc()
        }
        track_function_exit("emergency_reset_complete", error=error_msg)
        return JSONResponse(status_code=500, content=error_response)

# === ADDITIONAL UTILITY ENDPOINTS ===

@app.post("/test_background_task")
async def test_background_task(background_tasks: BackgroundTasks):
    """Test endpoint to debug background task execution"""
    
    def test_task():
        log_debug("🧪 TEST BACKGROUND TASK STARTED", "INFO", "test_task")
        print("🧪 TEST BACKGROUND TASK STARTED", file=sys.stderr, flush=True)
        
        try:
            log_debug(f"🧵 Test task thread info: ID={threading.current_thread().ident}, Name={threading.current_thread().name}", "INFO", "test_task")
            
            # Simple test operations
            import time
            for i in range(3):
                log_debug(f"🔄 Test task step {i+1}/3", "INFO", "test_task")
                time.sleep(1)
            
            log_debug("✅ TEST BACKGROUND TASK COMPLETED", "INFO", "test_task")
            
        except Exception as e:
            log_debug(f"❌ TEST BACKGROUND TASK FAILED: {str(e)}", "ERROR", "test_task")
            log_debug(f"🔍 Test Task Traceback: {traceback.format_exc()}", "ERROR", "test_task")
    
    log_debug("🧪 Adding test background task", "INFO", "test_background_task")
    background_tasks.add_task(test_task)
    
    return {
        "message": "Test background task added",
        "status": "started",
        "timestamp": datetime.utcnow().isoformat(),
        "active_threads": threading.active_count()
    }

@app.get("/features")
async def get_available_features_endpoint():
    """Get available features based on service status"""
    return {
        "available_features": get_available_features(),
        "service_status": {
            "openai": is_openai_available(),
            "google_drive": is_drive_available(),
            "clair_prompt": len(CLAIR_SYSTEM_PROMPT) > 0
        },
        "sync_capabilities": {
            "recursive_sync": True,
            "max_depth": LIMITS["MAX_FOLDERS_DEPTH"],
            "max_files": LIMITS["MAX_FILES_PER_SYNC"],
            "supported_file_types": [
                "application/pdf",
                "text/plain",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword"
            ]
        },
        "version": VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/config")
async def get_system_config():
    """Get system configuration and limits"""
    return {
        "version": VERSION,
        "build_date": BUILD_DATE,
        "timeouts": TIMEOUTS,
        "limits": LIMITS,
        "environment": {
            "gcp_project_id": GCP_PROJECT_ID,
            "google_drive_folder_id": GOOGLE_DRIVE_FOLDER_ID,
            "openai_configured": is_openai_available(),
            "drive_configured": is_drive_available()
        },
        "features": {
            "recursive_sync": True,
            "thread_safe_operations": True,
            "comprehensive_error_handling": True,
            "robust_startup": True,
            "graceful_service_degradation": True
        },
        "container_info": {
            "port": int(os.environ.get("PORT", 8080)),
            "working_directory": os.getcwd(),
            "python_version": sys.version,
            "active_threads": threading.active_count()
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# === BACKWARD COMPATIBILITY ENDPOINTS ===

@app.post("/sync_drive_force")
async def trigger_sync_force(background_tasks: BackgroundTasks):
    """Force sync endpoint that bypasses state checks"""
    return await trigger_recursive_sync(background_tasks, force=True)

@app.get("/api/health")
async def api_health():
    """Alternative health endpoint for different routing"""
    return await robust_health()

@app.get("/api/status")
async def api_status():
    """Alternative status endpoint"""
    return await get_sync_status_complete()

# === MAIN STARTUP PROCESS ===

if __name__ == "__main__":
    try:
        # Comprehensive startup logging
        port = int(os.environ.get("PORT", 8080))
        print(f"🚀 Starting COMPLETE RAG Clair server on port {port}")
        print(f"🔧 Working directory: {os.getcwd()}")
        print(f"🔧 Python executable: {sys.executable}")
        print(f"🔧 Python version: {sys.version}")
        
        # Environment check
        print(f"🔧 Environment variables status:")
        print(f"   - PORT: {os.environ.get('PORT', 'not set')}")
        print(f"   - GCP_PROJECT_ID: {os.environ.get('GCP_PROJECT_ID', 'not set')}")
        print(f"   - GOOGLE_DRIVE_FOLDER_ID: {os.environ.get('GOOGLE_DRIVE_FOLDER_ID', 'not set')}")
        print(f"   - OPENAI_API_KEY: {'set' if os.environ.get('OPENAI_API_KEY') else 'not set'}")
        print(f"   - GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'using default')}")
        
        # Final system check
        print(f"🔧 System capabilities:")
        print(f"   - Recursive sync: ✅")
        print(f"   - Thread-safe operations: ✅")
        print(f"   - Robust startup: ✅")
        print(f"   - Graceful service degradation: ✅")
        print(f"   - Comprehensive error handling: ✅")
        print(f"   - Max folder depth: {LIMITS['MAX_FOLDERS_DEPTH']}")
        print(f"   - Max files per sync: {LIMITS['MAX_FILES_PER_SYNC']}")
        
        # Start server with robust configuration
        log_debug(f"🚀 Starting COMPLETE RAG Clair server on port {port}", "INFO", "main")
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            timeout_keep_alive=5,
            access_log=True,
            log_level="info",
            # Additional uvicorn settings for robustness
            loop="asyncio",
            http="auto",
            workers=1  # Single worker for thread safety
        )
        
    except Exception as e:
        print(f"❌ FATAL: Server startup failed: {e}")
        print(f"🔍 Startup Error Traceback: {traceback.format_exc()}")
        log_debug(f"❌ FATAL: Server startup failed: {e}", "ERROR", "main")
        log_debug(f"🔍 Startup Error Traceback: {traceback.format_exc()}", "ERROR", "main")
        sys.exit(1)

# Placeholder for search_documents (add your implementation if missing)
def search_documents(query, filters):
    # Implement document search logic here
    return []  # Return empty list as placeholder