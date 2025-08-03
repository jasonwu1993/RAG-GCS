# Documents Router - Google Drive Sync and File Management
# Preserves ALL original Google Drive sync functionality from main.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Any
from datetime import datetime, timedelta
import asyncio
import pdfplumber
import io

from core import log_debug, track_function_entry, global_state, bucket, index_endpoint
from google_drive import ultra_sync
from ai_service import split_text, embed_text
from config import DEPLOYED_INDEX_ID, TOP_K

router = APIRouter(prefix="/documents", tags=["documents"])

def parse_pdf(file_content: bytes, filename: str) -> str:
    """Parse PDF from bytes content - preserved from original main.py"""
    try:
        texts = []
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        texts.append(page_text)
                    
                    # Extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            try:
                                table_md = "\n".join([" | ".join([str(cell) if cell else "" for cell in row]) for row in table])
                                texts.append(table_md)
                            except Exception as e:
                                log_debug(f"Warning: Could not parse table in {filename}", {"error": str(e)})
                                continue
                except Exception as e:
                    log_debug(f"Warning: Could not parse page in {filename}", {"error": str(e)})
                    continue
        
        result = "\n\n".join(texts)
        return result if result.strip() else f"Could not extract text from PDF: {filename}"
        
    except Exception as e:
        log_debug(f"ERROR parsing PDF {filename}", {"error": str(e)})
        return f"Error parsing PDF {filename}: {str(e)}"

def upsert_embeddings_to_index(embeddings_data: List[Dict]) -> bool:
    """Upsert embeddings to Vertex AI index - preserved from original main.py"""
    if not index_endpoint or not embeddings_data:
        log_debug("Warning: No index endpoint or no data to upsert")
        return False
    
    try:
        response = index_endpoint.upsert_datapoints(
            deployed_index_id=DEPLOYED_INDEX_ID,
            datapoints=embeddings_data
        )
        log_debug(f"Successfully upserted {len(embeddings_data)} datapoints")
        return True
    except Exception as e:
        log_debug("Error upserting to index", {"error": str(e)})
        return False

async def process_file_for_search(file_path: str, file_content: bytes, file_name: str) -> Dict:
    """Process a file for search indexing - preserved from original main.py"""
    track_function_entry("process_file_for_search")
    
    try:
        # Extract text based on file type
        if file_name.lower().endswith('.pdf'):
            text_content = parse_pdf(file_content, file_name)
        else:
            text_content = file_content.decode('utf-8', errors='ignore')
        
        if not text_content or not text_content.strip():
            return {"status": "error", "message": "No text content extracted"}
        
        # Create chunks
        chunks = split_text(text_content)
        if not chunks:
            return {"status": "error", "message": "Could not create chunks"}
        
        # Store chunks and create embeddings
        embeddings_to_upsert = []
        uploaded_chunks = []
        
        for i, chunk in enumerate(chunks):
            chunk_path = f"chunks/{file_path}/{i}.txt"
            
            # Store chunk in GCS
            if ultra_sync.upload_file_to_gcs(chunk_path, chunk.encode('utf-8')):
                uploaded_chunks.append(chunk_path)
                
                # Create embedding
                vector = embed_text(chunk)
                
                # Prepare datapoint for vector index
                datapoint = {
                    "datapoint_id": chunk_path,
                    "feature_vector": vector,
                    "restricts": [{"namespace": "filepath", "allow_list": [file_path]}]
                }
                embeddings_to_upsert.append(datapoint)
        
        # Upsert to vector index
        vector_success = True
        if index_endpoint and embeddings_to_upsert:
            vector_success = upsert_embeddings_to_index(embeddings_to_upsert)
        
        return {
            "status": "success",
            "chunks_created": len(uploaded_chunks),
            "vector_indexed": vector_success,
            "message": f"Processed {len(uploaded_chunks)} chunks, vector indexed: {vector_success}"
        }
        
    except Exception as e:
        log_debug(f"Error processing file {file_name}", {"error": str(e)})
        return {"status": "error", "message": str(e)}

async def sync_single_file(drive_file: Dict, local_metadata: Dict) -> Dict:
    """Sync a single file from Google Drive - preserved from original main.py"""
    track_function_entry("sync_single_file")
    
    file_path = f"documents/{drive_file['path']}"
    
    try:
        # Download file content
        file_content = ultra_sync.download_drive_file(drive_file['id'])
        file_hash = ultra_sync.get_file_hash(file_content)
        
        # Check if file needs updating
        local_file_info = local_metadata.get(file_path, {})
        if local_file_info.get('hash') == file_hash:
            return {
                "status": "skipped",
                "message": "File unchanged",
                "file_path": file_path
            }
        
        # Store original file in GCS
        ultra_sync.upload_file_to_gcs(file_path, file_content)
        
        # Process for search
        process_result = await process_file_for_search(file_path, file_content, drive_file['name'])
        
        # Update metadata
        local_metadata[file_path] = {
            "hash": file_hash,
            "modified_time": drive_file['modifiedTime'],
            "size": drive_file['size'],
            "drive_id": drive_file['id'],
            "last_synced": datetime.utcnow().isoformat()
        }
        
        return {
            "status": "success",
            "message": f"Synced and processed: {process_result['message']}",
            "file_path": file_path,
            "process_result": process_result
        }
        
    except Exception as e:
        log_debug(f"Error syncing file {drive_file['name']}", {"error": str(e)})
        return {
            "status": "error",
            "message": str(e),
            "file_path": file_path
        }

async def remove_local_file(file_path: str, local_metadata: Dict) -> Dict:
    """Remove a file that no longer exists in Google Drive - preserved from original main.py"""
    track_function_entry("remove_local_file")
    
    try:
        # Remove original file
        ultra_sync.remove_file_from_gcs(file_path)
        
        # Remove chunks and get chunk IDs
        chunk_ids = ultra_sync.remove_chunks_from_gcs(file_path)
        
        # Remove from vector index
        if index_endpoint and chunk_ids:
            try:
                index_endpoint.remove_datapoints(
                    deployed_index_id=DEPLOYED_INDEX_ID,
                    datapoint_ids=chunk_ids
                )
            except Exception as e:
                log_debug("Warning: Could not remove from vector index", {"error": str(e)})
        
        # Remove from metadata
        if file_path in local_metadata:
            del local_metadata[file_path]
        
        return {
            "status": "success",
            "message": f"Removed file and {len(chunk_ids)} chunks",
            "file_path": file_path
        }
        
    except Exception as e:
        log_debug(f"Error removing file {file_path}", {"error": str(e)})
        return {
            "status": "error",
            "message": str(e),
            "file_path": file_path
        }

async def perform_drive_sync():
    """Perform the actual sync operation - preserved from original main.py"""
    track_function_entry("perform_drive_sync")
    
    global_state.sync_state["is_syncing"] = True
    start_time = datetime.utcnow()
    
    try:
        log_debug("Starting Google Drive sync...")
        
        # Get files from Google Drive
        drive_files = ultra_sync.get_drive_files_recursive()
        log_debug(f"Found {len(drive_files)} files in Google Drive")
        
        # Get local metadata
        local_metadata = ultra_sync.get_local_file_metadata()
        
        # Track sync results
        results = {
            "added": [],
            "updated": [],
            "removed": [],
            "skipped": [],
            "errors": []
        }
        
        # Create mapping of drive files
        drive_file_paths = {f"documents/{f['path']}" for f in drive_files}
        local_file_paths = set(local_metadata.keys())
        
        # Sync files from Drive
        for drive_file in drive_files:
            sync_result = await sync_single_file(drive_file, local_metadata)
            
            if sync_result["status"] == "success":
                results["updated"].append(sync_result)
            elif sync_result["status"] == "skipped":
                results["skipped"].append(sync_result)
            else:
                results["errors"].append(sync_result)
        
        # Remove files that no longer exist in Drive
        files_to_remove = local_file_paths - drive_file_paths
        for file_path in files_to_remove:
            remove_result = await remove_local_file(file_path, local_metadata)
            if remove_result["status"] == "success":
                results["removed"].append(remove_result)
            else:
                results["errors"].append(remove_result)
        
        # Save updated metadata
        ultra_sync.save_local_file_metadata(local_metadata)
        
        # Update sync state
        global_state.sync_state["last_sync"] = start_time.isoformat()
        global_state.sync_state["last_sync_results"] = results
        global_state.sync_state["next_auto_sync"] = (start_time + timedelta(hours=2)).isoformat()
        
        log_debug(f"Sync completed: {len(results['updated'])} updated, {len(results['removed'])} removed, {len(results['errors'])} errors")
        
    except Exception as e:
        log_debug("Sync failed", {"error": str(e)})
        global_state.sync_state["last_sync_results"] = {"error": str(e)}
    finally:
        global_state.sync_state["is_syncing"] = False

# API Endpoints - ALL preserved from original main.py

@router.post("/sync")
async def sync_google_drive(background_tasks: BackgroundTasks):
    """Manually trigger Google Drive sync - preserved from original main.py"""
    track_function_entry("sync_google_drive")
    
    if global_state.sync_state["is_syncing"]:
        return {"message": "Sync already in progress", "status": "running"}
    
    background_tasks.add_task(perform_drive_sync)
    return {"message": "Sync started", "status": "started"}

@router.get("/sync_status")
async def get_sync_status():
    """Get current sync status - preserved from original main.py"""
    track_function_entry("get_sync_status")
    
    return {
        "is_syncing": global_state.sync_state["is_syncing"],
        "last_sync": global_state.sync_state["last_sync"],
        "last_sync_results": global_state.sync_state["last_sync_results"],
        "next_auto_sync": global_state.sync_state["next_auto_sync"],
        "ultra_sync_status": ultra_sync.get_sync_status()
    }

@router.get("/list")
async def list_files():
    """COMPLETE: File listing with hierarchical structure - enhanced from original main.py"""
    track_function_entry("list_files")
    
    try:
        async def get_file_structure():
            local_metadata = ultra_sync.get_local_file_metadata()
            
            if not local_metadata:
                return {
                    "files": [],
                    "folders": [],
                    "file_count": 0,
                    "folder_count": 0,
                    "structure": "hierarchical",
                    "status": "no_files"
                }
            
            file_list = []
            folder_set = set()
            
            # Process each file with enhanced metadata
            for file_path, file_data in local_metadata.items():
                file_info = {
                    "path": file_path,
                    "name": file_data.get('name', file_path.split('/')[-1]),
                    "type": "file",
                    "mime_type": file_data.get('mime_type', 'application/octet-stream'),
                    "size": file_data.get('size', 0),
                    "processed_time": file_data.get('processed_time', file_data.get('modified_time'))
                }
                file_list.append(file_info)
                
                # Add parent folders to the set
                path_parts = file_path.split('/')
                for i in range(len(path_parts) - 1):
                    folder_path = '/'.join(path_parts[:i+1])
                    if folder_path:
                        folder_set.add(folder_path)
            
            # Create folder objects
            folders = [
                {
                    "path": path, 
                    "name": path.split('/')[-1], 
                    "type": "folder"
                } 
                for path in sorted(folder_set)
            ]
            
            return {
                "files": file_list,
                "folders": folders,
                "file_count": len(file_list),
                "folder_count": len(folders),
                "structure": "hierarchical",
                "status": "success",
                "recursive_scan_enabled": True
            }
        
        # Add timeout protection like original
        result = await asyncio.wait_for(get_file_structure(), timeout=15.0)
        
        # Update global files found counter
        global_state.update_files_found(result.get("file_count", 0))
        
        return result
        
    except asyncio.TimeoutError:
        error_result = {
            "files": [],
            "folders": [],
            "error": "File listing timed out",
            "status": "timeout"
        }
        return JSONResponse(status_code=408, content=error_result)
    except Exception as e:
        log_debug("ERROR listing files", {"error": str(e)})
        error_result = {
            "files": [],
            "folders": [],
            "error": str(e),
            "status": "error"
        }
        return JSONResponse(status_code=500, content=error_result)

@router.post("/sync_drive")
async def legacy_sync_drive(background_tasks: BackgroundTasks):
    """Legacy endpoint for backward compatibility"""
    return await sync_google_drive(background_tasks)

@router.get("/drive_files")
async def get_drive_files():
    """Get files directly from Google Drive"""
    track_function_entry("get_drive_files")
    
    try:
        drive_files = ultra_sync.get_drive_files_recursive()
        return {
            "files": drive_files,
            "total_count": len(drive_files),
            "sync_status": ultra_sync.get_sync_status()
        }
    except Exception as e:
        log_debug("ERROR getting drive files", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not get drive files: {str(e)}")

@router.get("/indexed")
async def list_indexed_documents():
    """List documents that are actually indexed in Vertex AI (have chunks)"""
    track_function_entry("list_indexed_documents")
    
    try:
        from core import bucket
        
        if not bucket:
            raise HTTPException(status_code=503, detail="Storage service not available")
        
        # Get all chunks from the chunks/ directory
        chunk_blobs = list(bucket.list_blobs(prefix="chunks/documents/"))
        
        # Extract unique document paths from chunk paths
        indexed_documents = set()
        for blob in chunk_blobs:
            # Chunk path format: chunks/documents/folder/file.pdf/0.txt
            # Extract: documents/folder/file.pdf
            path_parts = blob.name.split('/')
            if len(path_parts) >= 4:  # chunks/documents/file or chunks/documents/folder/file
                # Reconstruct document path by removing 'chunks/' prefix and chunk filename
                doc_path = '/'.join(path_parts[1:-1])  # Skip 'chunks' and chunk filename
                if doc_path.startswith('documents/'):
                    # Remove 'documents/' prefix to match expected format
                    clean_path = doc_path[len('documents/'):]
                    if clean_path:  # Make sure it's not empty
                        indexed_documents.add(clean_path)
        
        # Convert to sorted list
        indexed_files = sorted(list(indexed_documents))
        
        # Get metadata for each indexed document
        local_metadata = ultra_sync.get_local_file_metadata()
        file_details = []
        
        for file_path in indexed_files:
            full_path = f"documents/{file_path}"
            metadata = local_metadata.get(full_path, {})
            
            file_info = {
                "path": file_path,
                "name": file_path.split('/')[-1],
                "indexed": True,
                "size": metadata.get('size', 0),
                "modified_time": metadata.get('modified_time'),
                "last_synced": metadata.get('last_synced'),
                "drive_id": metadata.get('drive_id')
            }
            file_details.append(file_info)
        
        return {
            "files": indexed_files,  # Simple list for compatibility
            "file_details": file_details,  # Detailed info for advanced use
            "total_indexed": len(indexed_files),
            "status": "success",
            "source": "vertex_ai_chunks"
        }
        
    except Exception as e:
        log_debug("ERROR listing indexed documents", {"error": str(e)})
        return {
            "files": [],
            "file_details": [],
            "total_indexed": 0,
            "status": "error",
            "error": str(e)
        }

@router.post("/cleanup_vertex_ai")
async def cleanup_vertex_ai_ghosts():
    """Clean up ghost/duplicate documents from Vertex AI index"""
    track_function_entry("cleanup_vertex_ai_ghosts")
    
    try:
        from core import bucket, index_endpoint
        
        if not bucket:
            raise HTTPException(status_code=503, detail="Storage service not available")
        
        if not index_endpoint:
            raise HTTPException(status_code=503, detail="Vertex AI service not available")
        
        log_debug("Starting Vertex AI cleanup", {"operation": "remove_ghost_documents"})
        
        # Define the actual valid root-level files (from the filtering logic)
        valid_root_files = [
            'AI Strategies Highlights Flyer.pdf',
            'PATNAM DYNAMIC LOW VOLATILITY STRATEGIES POWERFUL COMBINATION LIM_1664_324_FINAL.pdf'
        ]
        
        # Files to remove (ghosts that shouldn't be in root)
        ghost_files = [
            'EXTERNAL TERM CONVERSION PROGRAM.pdf',
            'KEY FINANCIAL UNDERWRITING GUIDELINES.pdf', 
            'LIFE INSURANCE APPLICATIONS INFORMAL VS FORMAL LIM_1812_525_FINAL.pdf',
            'NLG FLEXLIFE PRODUCT GUIDE.pdf',
            'NLG FLEXLIFE QUICK REFERENCE GUIDE.pdf',
            'SUMMITLIFE QUICK REFERENCE GUIDE.pdf',
            'Symetra Knowledge Base.md'
        ]
        
        cleanup_results = {
            "removed_chunks": [],
            "removed_datapoints": [],
            "errors": [],
            "total_removed": 0
        }
        
        # Remove chunks and datapoints for ghost files
        for ghost_file in ghost_files:
            try:
                # Remove chunks from GCS
                chunk_prefix = f"chunks/documents/{ghost_file}/"
                chunk_blobs = list(bucket.list_blobs(prefix=chunk_prefix))
                
                chunk_ids_to_remove = []
                for blob in chunk_blobs:
                    chunk_ids_to_remove.append(blob.name)
                    blob.delete()
                    log_debug(f"Deleted chunk: {blob.name}")
                
                # Remove datapoints from Vertex AI index
                if chunk_ids_to_remove:
                    try:
                        # Remove datapoints from vector index
                        index_endpoint.remove_datapoints(
                            deployed_index_id=DEPLOYED_INDEX_ID,
                            datapoint_ids=chunk_ids_to_remove
                        )
                        cleanup_results["removed_datapoints"].extend(chunk_ids_to_remove)
                        log_debug(f"Removed {len(chunk_ids_to_remove)} datapoints for {ghost_file}")
                    except Exception as e:
                        log_debug(f"Error removing datapoints for {ghost_file}", {"error": str(e)})
                        cleanup_results["errors"].append(f"Datapoint removal failed for {ghost_file}: {str(e)}")
                
                cleanup_results["removed_chunks"].extend(chunk_ids_to_remove)
                
                # Also remove the original file from GCS if it exists
                try:
                    original_blob = bucket.blob(f"documents/{ghost_file}")
                    if original_blob.exists():
                        original_blob.delete()
                        log_debug(f"Deleted original file: documents/{ghost_file}")
                except Exception as e:
                    log_debug(f"Error removing original file {ghost_file}", {"error": str(e)})
                
            except Exception as e:
                error_msg = f"Error cleaning up {ghost_file}: {str(e)}"
                log_debug(error_msg)
                cleanup_results["errors"].append(error_msg)
        
        cleanup_results["total_removed"] = len(cleanup_results["removed_chunks"])
        
        log_debug("Vertex AI cleanup completed", {
            "removed_chunks": len(cleanup_results["removed_chunks"]),
            "removed_datapoints": len(cleanup_results["removed_datapoints"]),
            "errors": len(cleanup_results["errors"])
        })
        
        return {
            "status": "success",
            "message": f"Cleaned up {cleanup_results['total_removed']} ghost documents from Vertex AI",
            "details": cleanup_results
        }
        
    except Exception as e:
        log_debug("ERROR in Vertex AI cleanup", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Auto-sync functionality
async def auto_sync_loop():
    """Automatic sync every 2 hours"""
    # Set initial next auto-sync time
    from datetime import datetime, timedelta
    next_sync_time = datetime.utcnow() + timedelta(hours=2)
    global_state.sync_state["next_auto_sync"] = next_sync_time.isoformat()
    log_debug("Auto-sync loop started", {"next_sync": next_sync_time.isoformat()})
    
    while True:
        try:
            await asyncio.sleep(7200)  # 2 hours (7200 seconds)
            if not global_state.sync_state["is_syncing"]:
                log_debug("Starting scheduled auto-sync", {"interval": "2 hours"})
                await perform_drive_sync()
        except Exception as e:
            log_debug("Auto-sync error", {"error": str(e)})