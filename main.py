import os
import uuid
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage, aiplatform
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.api_core import exceptions
import numpy as np
import tiktoken
import pdfplumber
from openai import OpenAI
from typing import List, Dict, Optional
import io
import hashlib
import json

# --- Configuration & Initialization ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION", "us-central1")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
INDEX_ENDPOINT_ID = os.getenv("INDEX_ENDPOINT_ID")
DEPLOYED_INDEX_ID = os.getenv("DEPLOYED_INDEX_ID")

# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")  # The shared folder ID
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service-account.json")

if not all([PROJECT_ID, BUCKET_NAME, INDEX_ENDPOINT_ID, DEPLOYED_INDEX_ID, GOOGLE_DRIVE_FOLDER_ID]):
    raise ValueError("Missing one or more required environment variables.")

# Initialize Google Cloud services
storage_client = storage.Client(project=PROJECT_ID)
aiplatform.init(project=PROJECT_ID, location=REGION)
openai_client = OpenAI()
bucket = storage_client.bucket(BUCKET_NAME)

# Initialize Google Drive service
try:
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    drive_service = build('drive', 'v3', credentials=credentials)
    print("Successfully initialized Google Drive service.")
except Exception as e:
    print(f"ERROR: Could not initialize Google Drive service: {e}")
    drive_service = None

# Initialize Vertex AI Index Endpoint
try:
    index_endpoint_resource_name = f"projects/{PROJECT_ID}/locations/{REGION}/indexEndpoints/{INDEX_ENDPOINT_ID}"
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=index_endpoint_resource_name)
    print("Successfully initialized Vertex AI Index Endpoint.")
except Exception as e:
    print(f"ERROR: Could not find Index Endpoint: {e}")
    index_endpoint = None

EMBED_MODEL = "text-embedding-3-small"
SIMILARITY_THRESHOLD = 0.75
TOP_K = 3

# Global sync state
sync_state = {
    "is_syncing": False,
    "last_sync": None,
    "last_sync_results": None,
    "next_auto_sync": None
}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core Logic Functions (same as before) ---
def embed_text(text: str) -> List[float]:
    """Create embeddings with error handling"""
    try:
        if not text or not text.strip():
            return [0.0] * 1536
        response = openai_client.embeddings.create(input=[text], model=EMBED_MODEL)
        return response.data[0].embedding
    except Exception as e:
        print(f"ERROR creating embedding: {e}")
        return [0.0] * 1536

def split_text(text: str, max_tokens: int = 500) -> List[str]:
    """Enhanced text splitting with better error handling"""
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        words = text.split()
        chunks = []
        current_chunk = []
        current_token_count = 0
        
        for word in words:
            word_token_count = len(enc.encode(word + " "))
            if current_token_count + word_token_count > max_tokens and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_token_count = 0
            current_chunk.append(word)
            current_token_count += word_token_count
            
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks if chunks else [text]
    except Exception as e:
        print(f"ERROR in text splitting: {e}")
        return [text]

def parse_pdf(file_content: bytes, filename: str) -> str:
    """Parse PDF from bytes content"""
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
                                print(f"Warning: Could not parse table in {filename}: {e}")
                                continue
                except Exception as e:
                    print(f"Warning: Could not parse page in {filename}: {e}")
                    continue
        
        result = "\n\n".join(texts)
        return result if result.strip() else f"Could not extract text from PDF: {filename}"
        
    except Exception as e:
        print(f"ERROR parsing PDF {filename}: {e}")
        return f"Error parsing PDF {filename}: {str(e)}"

def upsert_embeddings_to_index(embeddings_data: List[Dict]) -> bool:
    """Upsert embeddings to Vertex AI index with proper error handling"""
    if not index_endpoint or not embeddings_data:
        print("Warning: No index endpoint or no data to upsert")
        return False
    
    try:
        response = index_endpoint.upsert_datapoints(
            deployed_index_id=DEPLOYED_INDEX_ID,
            datapoints=embeddings_data
        )
        print(f"Successfully upserted {len(embeddings_data)} datapoints")
        return True
    except Exception as e:
        print(f"Error upserting to index: {e}")
        return False

# --- Google Drive Sync Functions ---
def get_file_hash(content: bytes) -> str:
    """Generate hash for file content to detect changes"""
    return hashlib.md5(content).hexdigest()

def get_drive_files(folder_id: str = None) -> List[Dict]:
    """Get all files from Google Drive folder recursively"""
    if not drive_service:
        return []
    
    if folder_id is None:
        folder_id = GOOGLE_DRIVE_FOLDER_ID
    
    files = []
    try:
        # Get files in current folder
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)"
        ).execute()
        
        items = results.get('files', [])
        
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # Recursively get files from subfolders
                subfolder_files = get_drive_files(item['id'])
                for subfile in subfolder_files:
                    subfile['path'] = f"{item['name']}/{subfile['path']}"
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
                        'path': item['name']
                    })
        
        return files
        
    except Exception as e:
        print(f"Error getting Drive files: {e}")
        return []

def download_drive_file(file_id: str) -> bytes:
    """Download file content from Google Drive"""
    if not drive_service:
        raise Exception("Google Drive service not available")
    
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        return file_io.getvalue()
        
    except Exception as e:
        print(f"Error downloading file {file_id}: {e}")
        raise

def get_local_file_metadata() -> Dict[str, Dict]:
    """Get metadata of all local files"""
    try:
        metadata_blob = bucket.blob("sync_metadata.json")
        if metadata_blob.exists():
            return json.loads(metadata_blob.download_as_text())
        return {}
    except Exception as e:
        print(f"Error getting local metadata: {e}")
        return {}

def save_local_file_metadata(metadata: Dict[str, Dict]):
    """Save metadata of local files"""
    try:
        metadata_blob = bucket.blob("sync_metadata.json")
        metadata_blob.upload_from_string(json.dumps(metadata, indent=2))
    except Exception as e:
        print(f"Error saving metadata: {e}")

async def process_file_for_search(file_path: str, file_content: bytes, file_name: str) -> Dict:
    """Process a file for search indexing"""
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
            chunk_blob = bucket.blob(chunk_path)
            chunk_blob.upload_from_string(chunk)
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
        print(f"Error processing file {file_name}: {e}")
        return {"status": "error", "message": str(e)}

async def sync_single_file(drive_file: Dict, local_metadata: Dict) -> Dict:
    """Sync a single file from Google Drive"""
    file_path = f"documents/{drive_file['path']}"
    
    try:
        # Download file content
        file_content = download_drive_file(drive_file['id'])
        file_hash = get_file_hash(file_content)
        
        # Check if file needs updating
        local_file_info = local_metadata.get(file_path, {})
        if local_file_info.get('hash') == file_hash:
            return {
                "status": "skipped",
                "message": "File unchanged",
                "file_path": file_path
            }
        
        # Store original file in GCS
        file_blob = bucket.blob(file_path)
        file_blob.upload_from_string(file_content)
        
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
        print(f"Error syncing file {drive_file['name']}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "file_path": file_path
        }

async def remove_local_file(file_path: str, local_metadata: Dict) -> Dict:
    """Remove a file that no longer exists in Google Drive"""
    try:
        # Remove original file
        file_blob = bucket.blob(file_path)
        if file_blob.exists():
            file_blob.delete()
        
        # Remove chunks
        chunk_prefix = f"chunks/{file_path}/"
        chunk_blobs = list(storage_client.list_blobs(BUCKET_NAME, prefix=chunk_prefix))
        chunk_ids = []
        
        for chunk_blob in chunk_blobs:
            chunk_ids.append(chunk_blob.name)
            chunk_blob.delete()
        
        # Remove from vector index
        if index_endpoint and chunk_ids:
            try:
                index_endpoint.remove_datapoints(
                    deployed_index_id=DEPLOYED_INDEX_ID,
                    datapoint_ids=chunk_ids
                )
            except Exception as e:
                print(f"Warning: Could not remove from vector index: {e}")
        
        # Remove from metadata
        if file_path in local_metadata:
            del local_metadata[file_path]
        
        return {
            "status": "success",
            "message": f"Removed file and {len(chunk_ids)} chunks",
            "file_path": file_path
        }
        
    except Exception as e:
        print(f"Error removing file {file_path}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "file_path": file_path
        }

# --- API Endpoints ---
@app.post("/sync_drive")
async def sync_google_drive(background_tasks: BackgroundTasks):
    """Manually trigger Google Drive sync"""
    if sync_state["is_syncing"]:
        return {"message": "Sync already in progress", "status": "running"}
    
    background_tasks.add_task(perform_drive_sync)
    return {"message": "Sync started", "status": "started"}

@app.get("/sync_status")
async def get_sync_status():
    """Get current sync status"""
    return {
        "is_syncing": sync_state["is_syncing"],
        "last_sync": sync_state["last_sync"],
        "last_sync_results": sync_state["last_sync_results"],
        "next_auto_sync": sync_state["next_auto_sync"]
    }

async def perform_drive_sync():
    """Perform the actual sync operation"""
    sync_state["is_syncing"] = True
    start_time = datetime.utcnow()
    
    try:
        print("Starting Google Drive sync...")
        
        # Get files from Google Drive
        drive_files = get_drive_files()
        print(f"Found {len(drive_files)} files in Google Drive")
        
        # Get local metadata
        local_metadata = get_local_file_metadata()
        
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
        save_local_file_metadata(local_metadata)
        
        # Update sync state
        sync_state["last_sync"] = start_time.isoformat()
        sync_state["last_sync_results"] = results
        sync_state["next_auto_sync"] = (start_time + timedelta(minutes=10)).isoformat()
        
        print(f"Sync completed: {len(results['updated'])} updated, {len(results['removed'])} removed, {len(results['errors'])} errors")
        
    except Exception as e:
        print(f"Sync failed: {e}")
        sync_state["last_sync_results"] = {"error": str(e)}
    finally:
        sync_state["is_syncing"] = False

# --- Auto-sync background task ---
@app.on_event("startup")
async def start_auto_sync():
    """Start automatic sync loop"""
    asyncio.create_task(auto_sync_loop())

async def auto_sync_loop():
    """Automatic sync every 10 minutes"""
    while True:
        try:
            await asyncio.sleep(600)  # 10 minutes
            if not sync_state["is_syncing"]:
                await perform_drive_sync()
        except Exception as e:
            print(f"Auto-sync error: {e}")

# --- Existing endpoints (modified for compatibility) ---
@app.get("/list_files")
def list_files():
    """List all synced files"""
    try:
        local_metadata = get_local_file_metadata()
        files = list(local_metadata.keys())
        return {"files": sorted(files)}
    except Exception as e:
        print(f"ERROR listing files: {e}")
        raise HTTPException(status_code=500, detail=f"Could not list files: {str(e)}")

@app.post("/ask")
async def ask(request: Request):
    """Enhanced ask endpoint with better error handling"""
    try:
        data = await request.json()
        query = data.get("query", "")
        filters = data.get("filters", [])
        
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query not provided")
        
        print(f"Processing query: {query}")
        print(f"With filters: {filters}")
        
        relevant_chunks = []
        highest_score = -1.0
        
        # Try vector search if index is available
        if index_endpoint:
            try:
                query_vec = embed_text(query)
                
                # Prepare search parameters
                search_params = {
                    "deployed_index_id": DEPLOYED_INDEX_ID,
                    "queries": [query_vec],
                    "num_neighbors": TOP_K
                }
                
                # Add filters if specified
                if filters:
                    restricts = []
                    for filepath in filters:
                        restricts.append({"namespace": "filepath", "allow_list": [filepath]})
                    search_params["filter"] = restricts
                
                # Perform search
                search_results = index_endpoint.find_neighbors(**search_params)
                
                # Process results
                if search_results and len(search_results) > 0:
                    neighbors = search_results[0]
                    for neighbor in neighbors:
                        similarity_score = 1 - neighbor.distance
                        if similarity_score >= SIMILARITY_THRESHOLD:
                            chunk_blob = bucket.blob(neighbor.id)
                            if chunk_blob.exists():
                                chunk_text = chunk_blob.download_as_text()
                                relevant_chunks.append(chunk_text)
                        if similarity_score > highest_score:
                            highest_score = similarity_score
                            
            except Exception as e:
                print(f"Vector search failed: {e}")
        
        # Generate response
        try:
            if relevant_chunks:
                print(f"Found {len(relevant_chunks)} relevant chunks. Highest score: {highest_score:.4f}")
                combined_context = "\n\n---\n\n".join(relevant_chunks)
                system_prompt = (
                    "You are Clair, an expert AI financial advisor (AI财富专家). Your task is to provide accurate, "
                    "helpful financial and insurance advice based on the provided context from documents. "
                    "Use ONLY the information from the context snippets below. If the context doesn't contain "
                    "the answer, state that clearly. Always be precise and reference specific policy provisions "
                    "or financial information when applicable."
                )
                user_prompt = f"CONTEXT:\n---\n{combined_context}\n---\n\nQUESTION: {query}"
            else:
                print("No relevant context found. Using general knowledge.")
                system_prompt = (
                    "You are Clair, an expert AI financial advisor (AI财富专家). Provide helpful, accurate "
                    "information about financial and insurance topics based on your general knowledge. "
                    "Always mention that specific details should be verified with the actual policy documents "
                    "or financial statements."
                )
                user_prompt = query
            
            # Call OpenAI API
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            answer = response.choices[0].message.content
            return {"answer": answer}
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return {"answer": "I'm experiencing technical difficulties generating a response. Please try again."}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in ask endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Could not process query: {str(e)}")

@app.post("/feedback")
async def submit_feedback(request: Request):
    """Collect user feedback for improving the system"""
    try:
        data = await request.json()
        query = data.get("query")
        response = data.get("response")
        feedback_type = data.get("feedback_type")  # 'helpful' or 'not_helpful'
        documents_used = data.get("documents_used", 0)
        
        # Log feedback for analysis (in production, store in database)
        feedback_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "response": response,
            "feedback_type": feedback_type,
            "documents_used": documents_used
        }
        
        # For now, just log to console (replace with proper storage)
        print(f"User Feedback: {feedback_entry}")
        
        # You could store this in Cloud Firestore, BigQuery, or another database
        # Example:
        # feedback_collection.add(feedback_entry)
        
        return {"message": "Feedback recorded successfully"}
        
    except Exception as e:
        print(f"ERROR recording feedback: {e}")
        return {"message": "Failed to record feedback"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "vector_index_available": index_endpoint is not None,
        "bucket_accessible": bucket is not None,
        "drive_service_available": drive_service is not None,
        "sync_status": sync_state
    }

@app.get("/status")
def quick_status():
    """Quick status check that responds immediately"""
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)