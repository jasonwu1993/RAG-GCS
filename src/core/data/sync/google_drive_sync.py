# Ultra-Resilient Google Drive Sync with Circuit Breaker Pattern
# Enhanced with exponential backoff and comprehensive error handling

import time
import random
import hashlib
import json
import io
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from googleapiclient.http import MediaIoBaseDownload
from core import log_debug, track_function_entry, drive_service, bucket, storage_client, global_state
from config import BUCKET_NAME

class CircuitBreaker:
    """Circuit breaker pattern for resilient API calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class UltraResilientGoogleDriveSync:
    """Ultra-resilient Google Drive sync with comprehensive error handling"""
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = {
            "last_request": 0,
            "min_interval": 0.1  # 100ms between requests
        }
    
    def _exponential_backoff(self, attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """Calculate exponential backoff with jitter"""
        delay = min(base_delay * (2 ** attempt), max_delay)
        jitter = random.uniform(0.1, 0.3) * delay
        return delay + jitter
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        elapsed = current_time - self.rate_limiter["last_request"]
        if elapsed < self.rate_limiter["min_interval"]:
            time.sleep(self.rate_limiter["min_interval"] - elapsed)
        self.rate_limiter["last_request"] = time.time()
    
    def _execute_with_retry(self, operation, max_retries: int = 3, operation_name: str = "unknown"):
        """Execute operation with retry logic"""
        for attempt in range(max_retries + 1):
            if not self.circuit_breaker.can_execute():
                raise Exception(f"Circuit breaker is OPEN for {operation_name}")
            
            try:
                self._rate_limit()
                result = operation()
                self.circuit_breaker.record_success()
                return result
            except Exception as e:
                self.circuit_breaker.record_failure()
                
                if attempt == max_retries:
                    log_debug(f"Operation {operation_name} failed after {max_retries + 1} attempts", {"error": str(e)})
                    raise
                
                delay = self._exponential_backoff(attempt)
                log_debug(f"Operation {operation_name} failed, retrying in {delay:.2f}s", {
                    "attempt": attempt + 1,
                    "error": str(e)
                })
                time.sleep(delay)
    
    def get_file_hash(self, content: bytes) -> str:
        """Generate hash for file content to detect changes"""
        return hashlib.md5(content).hexdigest()
    
    def get_drive_files_recursive(self, folder_id: str = None) -> List[Dict]:
        """Get all files from Google Drive folder recursively with resilience"""
        track_function_entry("get_drive_files_recursive")
        
        if not drive_service:
            log_debug("Drive service not available")
            return []
        
        from config import GOOGLE_DRIVE_FOLDER_ID
        if folder_id is None:
            folder_id = GOOGLE_DRIVE_FOLDER_ID
        
        def _get_files():
            return self._get_files_from_folder(folder_id)
        
        try:
            files = self._execute_with_retry(_get_files, operation_name="get_drive_files")
            log_debug(f"Retrieved {len(files)} files from Google Drive")
            return files
        except Exception as e:
            log_debug("Failed to retrieve files from Google Drive", {"error": str(e)})
            return []
    
    def _get_files_from_folder(self, folder_id: str, path_prefix: str = "") -> List[Dict]:
        """Internal recursive function to get files from a folder"""
        files = []
        
        try:
            # Get files in current folder
            results = drive_service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)"
            ).execute()
            
            # Track API call
            global_state.track_api_call()
            
            items = results.get('files', [])
            
            for item in items:
                current_path = f"{path_prefix}/{item['name']}" if path_prefix else item['name']
                
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursively get files from subfolders
                    subfolder_files = self._get_files_from_folder(item['id'], current_path)
                    files.extend(subfolder_files)
                else:
                    # Filter for supported file types
                    supported_types = [
                        'application/pdf',
                        'text/plain',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'application/msword'
                    ]
                    
                    if item['mimeType'] in supported_types:
                        files.append({
                            'id': item['id'],
                            'name': item['name'],
                            'mimeType': item['mimeType'],
                            'modifiedTime': item['modifiedTime'],
                            'size': int(item.get('size', 0)),
                            'path': current_path
                        })
            
            return files
            
        except Exception as e:
            log_debug(f"Error getting files from folder {folder_id}", {"error": str(e)})
            raise
    
    def download_drive_file(self, file_id: str) -> bytes:
        """Download file content from Google Drive with resilience"""
        track_function_entry("download_drive_file")
        
        if not drive_service:
            raise Exception("Google Drive service not available")
        
        def _download():
            request = drive_service.files().get_media(fileId=file_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            return file_io.getvalue()
        
        try:
            content = self._execute_with_retry(_download, operation_name=f"download_file_{file_id}")
            # Track API call for download
            global_state.track_api_call()
            log_debug(f"Downloaded file {file_id}, size: {len(content)} bytes")
            return content
        except Exception as e:
            log_debug(f"Failed to download file {file_id}", {"error": str(e)})
            raise
    
    def get_local_file_metadata(self) -> Dict[str, Dict]:
        """Get metadata of all local files with resilience"""
        track_function_entry("get_local_file_metadata")
        
        def _get_metadata():
            if not bucket:
                return {}
            metadata_blob = bucket.blob("sync_metadata.json")
            if metadata_blob.exists():
                return json.loads(metadata_blob.download_as_text())
            return {}
        
        try:
            metadata = self._execute_with_retry(_get_metadata, operation_name="get_local_metadata")
            log_debug(f"Retrieved metadata for {len(metadata)} local files")
            return metadata
        except Exception as e:
            log_debug("Failed to get local file metadata", {"error": str(e)})
            return {}
    
    def save_local_file_metadata(self, metadata: Dict[str, Dict]):
        """Save metadata of local files with resilience"""
        track_function_entry("save_local_file_metadata")
        
        def _save_metadata():
            if not bucket:
                raise Exception("Storage bucket not available")
            metadata_blob = bucket.blob("sync_metadata.json")
            metadata_blob.upload_from_string(json.dumps(metadata, indent=2))
        
        try:
            self._execute_with_retry(_save_metadata, operation_name="save_local_metadata")
            log_debug(f"Saved metadata for {len(metadata)} files")
        except Exception as e:
            log_debug("Failed to save local file metadata", {"error": str(e)})
            raise
    
    def upload_file_to_gcs(self, file_path: str, content: bytes) -> bool:
        """Upload file to Google Cloud Storage with resilience"""
        track_function_entry("upload_file_to_gcs")
        
        def _upload():
            if not bucket:
                raise Exception("Storage bucket not available")
            file_blob = bucket.blob(file_path)
            file_blob.upload_from_string(content)
        
        try:
            self._execute_with_retry(_upload, operation_name=f"upload_{file_path}")
            log_debug(f"Uploaded file to GCS: {file_path}, size: {len(content)} bytes")
            return True
        except Exception as e:
            log_debug(f"Failed to upload file to GCS: {file_path}", {"error": str(e)})
            return False
    
    def remove_file_from_gcs(self, file_path: str) -> bool:
        """Remove file from Google Cloud Storage with resilience"""
        track_function_entry("remove_file_from_gcs")
        
        def _remove():
            if not bucket:
                raise Exception("Storage bucket not available")
            file_blob = bucket.blob(file_path)
            if file_blob.exists():
                file_blob.delete()
        
        try:
            self._execute_with_retry(_remove, operation_name=f"remove_{file_path}")
            log_debug(f"Removed file from GCS: {file_path}")
            return True
        except Exception as e:
            log_debug(f"Failed to remove file from GCS: {file_path}", {"error": str(e)})
            return False
    
    def remove_chunks_from_gcs(self, file_path: str) -> List[str]:
        """Remove all chunks for a file from GCS"""
        track_function_entry("remove_chunks_from_gcs")
        
        try:
            chunk_prefix = f"chunks/{file_path}/"
            chunk_blobs = list(storage_client.list_blobs(BUCKET_NAME, prefix=chunk_prefix))
            chunk_ids = []
            
            for chunk_blob in chunk_blobs:
                chunk_ids.append(chunk_blob.name)
                chunk_blob.delete()
            
            log_debug(f"Removed {len(chunk_ids)} chunks for file: {file_path}")
            return chunk_ids
        except Exception as e:
            log_debug(f"Failed to remove chunks for file: {file_path}", {"error": str(e)})
            return []
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync system status"""
        return {
            "circuit_breaker_state": self.circuit_breaker.state,
            "failure_count": self.circuit_breaker.failure_count,
            "last_failure": self.circuit_breaker.last_failure_time,
            "rate_limiter": self.rate_limiter,
            "drive_service_available": drive_service is not None,
            "storage_available": bucket is not None
        }

# Global ultra-resilient sync instance
ultra_sync = UltraResilientGoogleDriveSync()