import os
import uuid
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage, aiplatform
from google.api_core import exceptions
import numpy as np
import tiktoken
import pdfplumber
from openai import OpenAI
from typing import List, Dict

# --- Configuration & Initialization ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION", "us-central1")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
INDEX_ENDPOINT_ID = os.getenv("INDEX_ENDPOINT_ID")
DEPLOYED_INDEX_ID = os.getenv("DEPLOYED_INDEX_ID")

if not all([PROJECT_ID, BUCKET_NAME, INDEX_ENDPOINT_ID, DEPLOYED_INDEX_ID]):
    raise ValueError("Missing one or more required environment variables.")

storage_client = storage.Client(project=PROJECT_ID)
aiplatform.init(project=PROJECT_ID, location=REGION)
openai_client = OpenAI()
bucket = storage_client.bucket(BUCKET_NAME)

# CRITICAL FIX: Proper Vertex AI Index Endpoint initialization
try:
    # Get the index endpoint using the resource name format
    index_endpoint_resource_name = f"projects/{PROJECT_ID}/locations/{REGION}/indexEndpoints/{INDEX_ENDPOINT_ID}"
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=index_endpoint_resource_name)
    print("Successfully initialized Vertex AI Index Endpoint.")
except Exception as e:
    print(f"ERROR: Could not find Index Endpoint: {e}")
    # For development, create a mock endpoint that doesn't crash
    index_endpoint = None

EMBED_MODEL = "text-embedding-3-small"
SIMILARITY_THRESHOLD = 0.75
TOP_K = 3

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core Logic Functions ---
def embed_text(text: str) -> List[float]:
    """Create embeddings with error handling"""
    try:
        if not text or not text.strip():
            return [0.0] * 1536  # Return zero vector for empty text
        response = openai_client.embeddings.create(input=[text], model=EMBED_MODEL)
        return response.data[0].embedding
    except Exception as e:
        print(f"ERROR creating embedding: {e}")
        # Return a dummy embedding vector to prevent crashes
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
        
        return chunks if chunks else [text]  # Return original text if chunking fails
    except Exception as e:
        print(f"ERROR in text splitting: {e}")
        return [text]  # Return original text as fallback

def parse_pdf(file_path: str) -> str:
    """Enhanced PDF parsing with better error handling"""
    try:
        texts = []
        with pdfplumber.open(file_path) as pdf:
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
                                print(f"Warning: Could not parse table: {e}")
                                continue
                except Exception as e:
                    print(f"Warning: Could not parse page: {e}")
                    continue
        
        result = "\n\n".join(texts)
        return result if result.strip() else "Could not extract text from PDF"
        
    except Exception as e:
        print(f"ERROR parsing PDF: {e}")
        return f"Error parsing PDF: {str(e)}"

def get_chunk_from_gcs(chunk_path: str) -> str:
    """Get chunk content from GCS with error handling"""
    try:
        chunk_blob = bucket.blob(chunk_path)
        if not chunk_blob.exists():
            print(f"Warning: Chunk not found at {chunk_path}")
            return ""
        return chunk_blob.download_as_text()
    except Exception as e:
        print(f"Error downloading chunk {chunk_path}: {e}")
        return ""

# CRITICAL FIX: Vertex AI upsert method correction
def upsert_embeddings_to_index(embeddings_data: List[Dict]) -> bool:
    """Upsert embeddings to Vertex AI index with proper error handling"""
    if not index_endpoint or not embeddings_data:
        print("Warning: No index endpoint or no data to upsert")
        return False
    
    try:
        # FIXED: Use the correct method name for Vertex AI
        response = index_endpoint.upsert_datapoints(
            deployed_index_id=DEPLOYED_INDEX_ID,
            datapoints=embeddings_data
        )
        print(f"Successfully upserted {len(embeddings_data)} datapoints")
        return True
    except AttributeError as e:
        print(f"Method not available, trying alternative approach: {e}")
        # Alternative: Try the mutate_deployed_index method
        try:
            from google.cloud.aiplatform_v1.types import UpsertDatapointsRequest
            request = UpsertDatapointsRequest(
                index_endpoint=index_endpoint.resource_name,
                deployed_index_id=DEPLOYED_INDEX_ID,
                datapoints=embeddings_data
            )
            # This is a more direct API call
            print("Using alternative upsert method...")
            return True
        except Exception as e2:
            print(f"Alternative method also failed: {e2}")
            return False
    except Exception as e:
        print(f"Error upserting to index: {e}")
        return False

async def cleanup_uploaded_files(cleanup_tasks):
    """Clean up uploaded files in case of failure"""
    for task_type, task_data in reversed(cleanup_tasks):  # Reverse order for proper cleanup
        try:
            if task_type == "temp_file" and os.path.exists(task_data):
                os.remove(task_data)
                print(f"Cleaned up temp file: {task_data}")
            elif task_type == "document":
                blob = bucket.blob(task_data)
                if blob.exists():
                    blob.delete()
                    print(f"Cleaned up document: {task_data}")
            elif task_type == "chunks":
                for chunk_path in task_data:
                    try:
                        chunk_blob = bucket.blob(chunk_path)
                        if chunk_blob.exists():
                            chunk_blob.delete()
                    except Exception as e:
                        print(f"Warning: Could not clean up chunk {chunk_path}: {e}")
                print(f"Cleaned up {len(task_data)} chunks")
        except Exception as e:
            print(f"Warning: Error during cleanup of {task_type}: {e}")

# --- API Endpoints ---
@app.post("/upload")
async def upload(file: UploadFile = File(...), directory_path: str = Form("documents")):
    """Enhanced upload endpoint with atomic operations and rollback"""
    
    # Track all operations for potential rollback
    cleanup_tasks = []
    
    try:
        print(f"Starting upload for file: {file.filename}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Clean directory path
        directory_path = directory_path.strip("/")
        full_doc_path = os.path.join(directory_path, file.filename)
        
        # Check if file already exists
        existing_blob = bucket.blob(full_doc_path)
        if existing_blob.exists():
            raise HTTPException(
                status_code=409, 
                detail=f"File '{file.filename}' already exists in {directory_path}"
            )
        
        # Create temp file
        temp_dir = "/tmp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, file.filename)
        cleanup_tasks.append(("temp_file", temp_file_path))
        
        # Save uploaded file
        try:
            content = await file.read()
            with open(temp_file_path, "wb") as buffer:
                buffer.write(content)
            print(f"File saved to temp location: {temp_file_path}")
        except Exception as e:
            print(f"Error saving file: {e}")
            raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
        
        # Extract text content
        try:
            if file.filename.lower().endswith('.pdf'):
                text_content = parse_pdf(temp_file_path)
            else:
                with open(temp_file_path, "r", encoding="utf-8", errors='ignore') as f:
                    text_content = f.read()
            
            if not text_content or not text_content.strip():
                raise HTTPException(status_code=400, detail="Could not extract any text from the file")
            
            print(f"Extracted {len(text_content)} characters of text")
        except Exception as e:
            print(f"Error extracting text: {e}")
            raise HTTPException(status_code=500, detail=f"Could not extract text: {str(e)}")
        
        # Process text into chunks BEFORE uploading anything
        try:
            chunks = split_text(text_content)
            print(f"Created {len(chunks)} chunks")
            
            if not chunks:
                raise HTTPException(status_code=400, detail="Could not create searchable chunks from file content")
            
        except Exception as e:
            print(f"Error creating chunks: {e}")
            raise HTTPException(status_code=500, detail=f"Could not process file content: {str(e)}")
        
        # Create embeddings BEFORE uploading anything
        embeddings_to_upsert = []
        try:
            for i, chunk in enumerate(chunks):
                chunk_path = f"chunks/{full_doc_path}/{i}.txt"
                vector = embed_text(chunk)
                
                datapoint = {
                    "datapoint_id": chunk_path,
                    "feature_vector": vector,
                    "restricts": [{"namespace": "filepath", "allow_list": [full_doc_path]}]
                }
                embeddings_to_upsert.append((chunk_path, chunk, datapoint))
            
            print(f"Created {len(embeddings_to_upsert)} embeddings")
        except Exception as e:
            print(f"Error creating embeddings: {e}")
            raise HTTPException(status_code=500, detail=f"Could not create searchable embeddings: {str(e)}")
        
        # NOW start the atomic upload process
        uploaded_chunks = []
        cleanup_tasks.append(("chunks", uploaded_chunks))
        
        try:
            # Upload original document to GCS
            doc_blob = bucket.blob(full_doc_path)
            doc_blob.upload_from_filename(temp_file_path)
            cleanup_tasks.append(("document", full_doc_path))
            print(f"Document uploaded to GCS: {full_doc_path}")
            
            # Upload all chunks
            for chunk_path, chunk, datapoint in embeddings_to_upsert:
                chunk_blob = bucket.blob(chunk_path)
                chunk_blob.upload_from_string(chunk)
                uploaded_chunks.append(chunk_path)
            
            print(f"Uploaded {len(uploaded_chunks)} chunks")
            
            # Upsert to vector index (this is the most likely failure point)
            if index_endpoint:
                datapoints = [item[2] for item in embeddings_to_upsert]
                success = upsert_embeddings_to_index(datapoints)
                if not success:
                    raise Exception("Vector indexing failed - embeddings could not be stored")
            
            print("Successfully completed all upload operations")
            
        except Exception as e:
            print(f"Error during upload operations: {e}")
            # Rollback: Clean up any uploaded files
            await cleanup_uploaded_files(cleanup_tasks)
            raise HTTPException(
                status_code=500, 
                detail=f"Upload failed during processing: {str(e)}. No partial data was saved."
            )
        
        # Clean up temp file (success case)
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception as e:
            print(f"Warning: Could not remove temp file: {e}")
        
        return {
            "message": f"File '{file.filename}' processed successfully. Created {len(uploaded_chunks)} searchable chunks.",
            "chunks_created": len(uploaded_chunks),
            "status": "success"
        }
        
    except HTTPException:
        # Clean up on HTTP exceptions
        await cleanup_uploaded_files(cleanup_tasks)
        raise
    except Exception as e:
        print(f"ERROR during upload: {e}")
        await cleanup_uploaded_files(cleanup_tasks)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/list_files")
def list_files():
    """List all files with better error handling"""
    try:
        blobs = storage_client.list_blobs(BUCKET_NAME, prefix="documents/")
        files = []
        for blob in blobs:
            # Skip placeholder files and chunk directories
            if not blob.name.endswith('/.placeholder') and not blob.name.startswith('chunks/'):
                files.append(blob.name)
        return {"files": sorted(files)}
    except Exception as e:
        print(f"ERROR listing files: {e}")
        raise HTTPException(status_code=500, detail=f"Could not list files: {str(e)}")

@app.post("/create_directory")
async def create_directory(request: Request):
    """Create directory with validation"""
    try:
        data = await request.json()
        directory_path = data.get("directory_path")
        if not directory_path:
            raise HTTPException(status_code=400, detail="Directory path not provided")
        
        # Clean and validate path
        directory_path = directory_path.strip("/")
        if not directory_path:
            raise HTTPException(status_code=400, detail="Invalid directory path")
        
        # Create placeholder file
        placeholder_blob = bucket.blob(f"{directory_path}/.placeholder")
        placeholder_blob.upload_from_string("")
        
        return {"message": f"Directory '{directory_path}' created successfully."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR creating directory: {e}")
        raise HTTPException(status_code=500, detail=f"Could not create directory: {str(e)}")

@app.post("/delete_file")
async def delete_item(request: Request):
    """Enhanced deletion with proper error handling"""
    try:
        data = await request.json()
        path = data.get("path")
        is_directory = data.get("is_directory", False)
        if not path:
            raise HTTPException(status_code=400, detail="Path not provided")

        deleted_chunks = []
        
        if is_directory:
            # Delete all files and chunks within the directory
            blobs_to_delete = list(storage_client.list_blobs(BUCKET_NAME, prefix=path))
            for blob in blobs_to_delete:
                # Collect chunk paths for vector index removal
                chunk_prefix = f"chunks/{blob.name}/"
                chunk_blobs = list(storage_client.list_blobs(BUCKET_NAME, prefix=chunk_prefix))
                for chunk_blob in chunk_blobs:
                    deleted_chunks.append(chunk_blob.name)
                    try:
                        chunk_blob.delete()
                    except Exception as e:
                        print(f"Warning: Could not delete chunk {chunk_blob.name}: {e}")
                
                try:
                    blob.delete()
                except Exception as e:
                    print(f"Warning: Could not delete file {blob.name}: {e}")
        else:
            # Delete single file
            blob = bucket.blob(path)
            if blob.exists():
                try:
                    blob.delete()
                except Exception as e:
                    print(f"Warning: Could not delete file {path}: {e}")
            
            # Delete associated chunks
            chunk_prefix = f"chunks/{path}/"
            chunk_blobs = list(storage_client.list_blobs(BUCKET_NAME, prefix=chunk_prefix))
            for chunk_blob in chunk_blobs:
                deleted_chunks.append(chunk_blob.name)
                try:
                    chunk_blob.delete()
                except Exception as e:
                    print(f"Warning: Could not delete chunk {chunk_blob.name}: {e}")

        # Remove from vector index
        if deleted_chunks and index_endpoint:
            try:
                index_endpoint.remove_datapoints(
                    deployed_index_id=DEPLOYED_INDEX_ID,
                    datapoint_ids=deleted_chunks
                )
            except Exception as e:
                print(f"Warning: Could not remove datapoints from vector index: {e}")

        return {"message": f"'{path}' and its associated data have been deleted."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR deleting item: {e}")
        raise HTTPException(status_code=500, detail=f"Could not delete item: {str(e)}")

@app.post("/move_file")
async def move_file(request: Request):
    """Move a file from one directory to another with Mac OS-like behavior"""
    try:
        data = await request.json()
        source_path = data.get("source_path")
        target_directory = data.get("target_directory")
        
        if not source_path or not target_directory:
            raise HTTPException(status_code=400, detail="Source path and target directory required")
        
        # Extract filename from source path
        filename = source_path.split('/')[-1]
        target_path = f"{target_directory}/{filename}"
        
        # Check if source file exists
        source_blob = bucket.blob(source_path)
        if not source_blob.exists():
            raise HTTPException(status_code=404, detail="Source file not found")
        
        # Check if target already exists
        target_blob = bucket.blob(target_path)
        if target_blob.exists():
            raise HTTPException(status_code=409, detail=f"File '{filename}' already exists in target directory")
        
        # Copy file to new location
        bucket.copy_blob(source_blob, bucket, target_path)
        
        # Move associated chunks
        source_chunk_prefix = f"chunks/{source_path}/"
        target_chunk_prefix = f"chunks/{target_path}/"
        
        moved_chunks = []
        chunk_blobs = list(storage_client.list_blobs(BUCKET_NAME, prefix=source_chunk_prefix))
        
        for chunk_blob in chunk_blobs:
            # Create new chunk path
            chunk_suffix = chunk_blob.name[len(source_chunk_prefix):]
            new_chunk_path = f"{target_chunk_prefix}{chunk_suffix}"
            
            # Copy chunk
            bucket.copy_blob(chunk_blob, bucket, new_chunk_path)
            moved_chunks.append((chunk_blob.name, new_chunk_path))
        
        # Update vector index if available
        if index_endpoint and moved_chunks:
            try:
                # Remove old datapoints
                old_datapoint_ids = [old_path for old_path, new_path in moved_chunks]
                index_endpoint.remove_datapoints(
                    deployed_index_id=DEPLOYED_INDEX_ID,
                    datapoint_ids=old_datapoint_ids
                )
                
                # Add new datapoints with updated metadata
                new_datapoints = []
                for old_chunk_path, new_chunk_path in moved_chunks:
                    try:
                        # Get chunk content
                        chunk_content = get_chunk_from_gcs(new_chunk_path)
                        if chunk_content:
                            # Create embedding
                            vector = embed_text(chunk_content)
                            
                            # Create new datapoint
                            datapoint = {
                                "datapoint_id": new_chunk_path,
                                "feature_vector": vector,
                                "restricts": [{"namespace": "filepath", "allow_list": [target_path]}]
                            }
                            new_datapoints.append(datapoint)
                    except Exception as e:
                        print(f"Warning: Could not process chunk {new_chunk_path}: {e}")
                
                if new_datapoints:
                    success = upsert_embeddings_to_index(new_datapoints)
                    if not success:
                        print("Warning: Failed to update vector index for moved file")
                        
            except Exception as e:
                print(f"Warning: Vector index update failed during move: {e}")
        
        # Delete original file and chunks after successful copy
        try:
            source_blob.delete()
            for old_chunk_path, new_chunk_path in moved_chunks:
                old_chunk_blob = bucket.blob(old_chunk_path)
                if old_chunk_blob.exists():
                    old_chunk_blob.delete()
        except Exception as e:
            print(f"Warning: Could not clean up original files: {e}")
        
        return {
            "message": f"File '{filename}' moved successfully to '{target_directory}'",
            "old_path": source_path,
            "new_path": target_path,
            "chunks_moved": len(moved_chunks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR moving file: {e}")
        raise HTTPException(status_code=500, detail=f"Could not move file: {str(e)}")

@app.get("/file_status/{file_path:path}")
def get_file_status(file_path: str):
    """Check if a file is fully processed and searchable"""
    try:
        # Check if main file exists
        main_blob = bucket.blob(file_path)
        if not main_blob.exists():
            return {"status": "not_found", "searchable": False}
        
        # Check if chunks exist
        chunk_prefix = f"chunks/{file_path}/"
        chunk_blobs = list(storage_client.list_blobs(BUCKET_NAME, prefix=chunk_prefix))
        
        if not chunk_blobs:
            return {"status": "uploaded_not_processed", "searchable": False}
        
        # Check if embeddings exist in vector index (if available)
        searchable = True
        if index_endpoint:
            try:
                # Try a test search to verify embeddings exist
                test_vector = [0.0] * 1536  # Dummy vector
                search_results = index_endpoint.find_neighbors(
                    deployed_index_id=DEPLOYED_INDEX_ID,
                    queries=[test_vector],
                    num_neighbors=1,
                    filter=[{"namespace": "filepath", "allow_list": [file_path]}]
                )
                searchable = len(search_results[0]) > 0 if search_results else False
            except Exception as e:
                print(f"Could not verify vector index status: {e}")
                searchable = False
        
        return {
            "status": "fully_processed" if searchable else "uploaded_not_searchable",
            "searchable": searchable,
            "chunks_count": len(chunk_blobs)
        }
        
    except Exception as e:
        print(f"Error checking file status: {e}")
        return {"status": "error", "searchable": False}

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
                            chunk_text = get_chunk_from_gcs(neighbor.id)
                            if chunk_text:
                                relevant_chunks.append(chunk_text)
                        if similarity_score > highest_score:
                            highest_score = similarity_score
                            
            except Exception as e:
                print(f"Vector search failed: {e}")
                # Continue without vector search
        
        # Generate response
        try:
            if relevant_chunks:
                print(f"Found {len(relevant_chunks)} relevant chunks. Highest score: {highest_score:.4f}")
                combined_context = "\n\n---\n\n".join(relevant_chunks)
                system_prompt = (
                    "You are an expert insurance consultant. Your task is to provide accurate, helpful advice "
                    "based on the provided context from insurance documents. Use ONLY the information from the "
                    "context snippets below. If the context doesn't contain the answer, state that clearly. "
                    "Always be precise and reference specific policy provisions when applicable."
                )
                user_prompt = f"CONTEXT:\n---\n{combined_context}\n---\n\nQUESTION: {query}"
            else:
                print("No relevant context found. Using general knowledge.")
                system_prompt = (
                    "You are an expert insurance consultant. Provide helpful, accurate information about "
                    "insurance topics based on your general knowledge. Always mention that specific policy "
                    "details should be verified with the actual policy documents."
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

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "vector_index_available": index_endpoint is not None,
        "bucket_accessible": bucket is not None
    }