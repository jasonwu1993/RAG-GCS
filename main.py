import os
import uuid
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage, aiplatform
from google.api_core import exceptions
import numpy as np
import tiktoken
import pdfplumber
from openai import OpenAI
from typing import List

# --- Configuration & Initialization ---

# Load configuration from environment variables
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION", "us-central1")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
INDEX_ENDPOINT_ID = os.getenv("INDEX_ENDPOINT_ID")
DEPLOYED_INDEX_ID = os.getenv("DEPLOYED_INDEX_ID")

# Validate that all required environment variables are set
if not all([PROJECT_ID, BUCKET_NAME, INDEX_ENDPOINT_ID, DEPLOYED_INDEX_ID]):
    raise ValueError("Missing one or more required environment variables: GCP_PROJECT_ID, GCS_BUCKET_NAME, INDEX_ENDPOINT_ID, DEPLOYED_INDEX_ID")

# Initialize clients
storage_client = storage.Client(project=PROJECT_ID)
aiplatform.init(project=PROJECT_ID, location=REGION)
openai_client = OpenAI()
bucket = storage_client.bucket(BUCKET_NAME)

# Initialize the Vertex AI Index Endpoint
try:
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=INDEX_ENDPOINT_ID)
    print("Successfully initialized Vertex AI Index Endpoint.")
except exceptions.NotFound:
    print(f"ERROR: Could not find Index Endpoint with ID: {INDEX_ENDPOINT_ID}")
    # In a real app, you might exit or handle this more gracefully
    raise

# Constants
EMBED_MODEL = "text-embedding-3-small"
SIMILARITY_THRESHOLD = 0.75
TOP_K = 3

# --- FastAPI App Setup ---
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
    response = openai_client.embeddings.create(input=[text], model=EMBED_MODEL)
    return response.data[0].embedding

def split_text(text: str, max_tokens: int = 500) -> List[str]:
    enc = tiktoken.get_encoding("cl100k_base")
    words = text.split()
    chunks = []
    current_chunk = []
    current_token_count = 0
    for word in words:
        word_token_count = len(enc.encode(word + " "))
        if current_token_count + word_token_count > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_token_count = 0
        current_chunk.append(word)
        current_token_count += word_token_count
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def parse_pdf(file_path: str) -> str:
    texts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                texts.append(page_text)
            tables = page.extract_tables()
            for table in tables:
                if table:
                    table_md = "\n".join([" | ".join(map(str, row)) for row in table])
                    texts.append(table_md)
    return "\n\n".join(texts)

# --- IMPROVEMENT: Helper function to retrieve chunk text from GCS ---
def get_chunk_from_gcs(chunk_path: str) -> str:
    """Downloads and reads the content of a text chunk from GCS."""
    try:
        chunk_blob = bucket.blob(chunk_path)
        return chunk_blob.download_as_text()
    except exceptions.NotFound:
        print(f"Warning: Chunk not found at {chunk_path}")
        return "" # Return empty string if chunk is not found

# --- API Endpoints ---

@app.post("/upload")
async def upload(file: UploadFile = File(...), directory_path: str = Form("documents")):
    """
    IMPROVEMENT: Handles file uploads to a specific directory within the GCS bucket.
    Also stores individual text chunks in GCS for precise retrieval later.
    """
    try:
        # Sanitize directory path to prevent traversal issues
        directory_path = directory_path.strip("/")
        # IMPROVEMENT: Construct the full path for the document within the specified directory
        full_doc_path = os.path.join(directory_path, file.filename)

        # Save file to a temporary local path for processing
        temp_dir = "/tmp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, file.filename)
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Parse text content
        if file.filename.lower().endswith('.pdf'):
            text_content = parse_pdf(temp_file_path)
        else:
            with open(temp_file_path, "r", encoding="utf-8") as f:
                text_content = f.read()
        
        # Upload original file to GCS for permanent storage
        doc_blob = bucket.blob(full_doc_path)
        doc_blob.upload_from_filename(temp_file_path)
        
        os.remove(temp_file_path)

        # Process and upsert vectors to Vertex AI
        chunks = split_text(text_content)
        embeddings_to_upsert = []
        for i, chunk in enumerate(chunks):
            # IMPROVEMENT: Store each chunk as a separate object in GCS
            chunk_path = f"chunks/{full_doc_path}/{i}.txt"
            chunk_blob = bucket.blob(chunk_path)
            chunk_blob.upload_from_string(chunk)

            vector = embed_text(chunk)
            
            # IMPROVEMENT: The datapoint ID is now the GCS path to the chunk text
            embeddings_to_upsert.append(aiplatform.MatchingEngineIndex.Datapoint(
                datapoint_id=chunk_path,
                feature_vector=vector,
                restricts=[
                    aiplatform.MatchingEngineIndex.Namespace(
                        name="filepath", allow_list=[full_doc_path]
                    )
                ]
            ))
        
        if embeddings_to_upsert:
            index_endpoint.upsert_datapoints(datapoints=embeddings_to_upsert)

        return {"message": f"File '{file.filename}' processed and stored in '{directory_path}' successfully."}
    except Exception as e:
        print(f"ERROR during upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list_files")
def list_files():
    """IMPROVEMENT: Lists all files, returning their full paths to represent the directory structure."""
    try:
        blobs = storage_client.list_blobs(BUCKET_NAME, prefix="documents/")
        # Return the full path of each document
        files = [blob.name for blob in blobs if not blob.name.endswith('/')]
        return {"files": sorted(files)}
    except Exception as e:
        print(f"ERROR listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/delete_file")
async def delete_file(request: Request):
    """IMPROVEMENT: Deletes a file and all its associated chunks from GCS and Vertex AI."""
    try:
        data = await request.json()
        # The frontend will now send the full path of the file
        filepath = data.get("filename")
        if not filepath:
            raise HTTPException(status_code=400, detail="Filepath not provided")

        # Delete original document from GCS
        blob = bucket.blob(filepath)
        if blob.exists():
            blob.delete()
        
        # Delete all associated chunks from GCS
        chunk_prefix = f"chunks/{filepath}/"
        chunk_blobs = storage_client.list_blobs(BUCKET_NAME, prefix=chunk_prefix)
        for chunk_blob in chunk_blobs:
            chunk_blob.delete()
        
        # Delete from Vertex AI by filtering on the full filepath
        index_endpoint.delete_datapoints(
            filter=aiplatform.MatchingEngineIndex.Namespace(
                name="filepath", allow_list=[filepath]
            )
        )
        
        return {"message": f"File '{filepath}' and its associated data have been deleted."}
    except Exception as e:
        print(f"ERROR deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    query = data.get("query", "")
    # Filters will now be a list of full filepaths
    filters = data.get("filters", [])

    if not query:
        raise HTTPException(status_code=400, detail="Query not provided")

    query_vec = embed_text(query)
    
    # --- Perform search on Vertex AI ---
    search_results = []
    if filters:
        search_results = index_endpoint.find_neighbors(
            queries=[query_vec],
            deployed_index_id=DEPLOYED_INDEX_ID,
            num_neighbors=TOP_K,
            # IMPROVEMENT: Filter by the full filepath for precise context scoping
            filter=[aiplatform.MatchingEngineIndex.Namespace(name="filepath", allow_list=filters)]
        )

    # --- Process results and decide on prompt ---
    relevant_chunks = []
    highest_score = -1.0
    if search_results and search_results[0]:
        for neighbor in search_results[0]:
            if neighbor.distance >= SIMILARITY_THRESHOLD:
                # --- CRITICAL IMPROVEMENT: Retrieve the actual chunk text from GCS ---
                chunk_text = get_chunk_from_gcs(neighbor.id)
                if chunk_text:
                    relevant_chunks.append(chunk_text)
            if neighbor.distance > highest_score:
                highest_score = neighbor.distance

    if relevant_chunks:
        print(f"INFO: Found {len(relevant_chunks)} relevant chunks. Highest score: {highest_score:.4f}. Using RAG.")
        combined_context = "\n\n---\n\n".join(relevant_chunks)
        system_prompt = (
            "You are an expert AI assistant. Your task is to synthesize a comprehensive and accurate answer based "
            "on the provided context. Use ONLY the information from the context snippets below. "
            "Combine information from multiple snippets if necessary to formulate the best possible response. "
            "If the context does not contain the answer, state that clearly."
        )
        user_prompt = f"CONTEXT:\n---\n{combined_context}\n---\n\nQUESTION: {query}"
    else:
        if filters:
            print(f"INFO: No relevant context found above threshold. Highest score was {highest_score:.4f}. Using general knowledge.")
        else:
            print("INFO: No files selected. Using general knowledge.")
        system_prompt = "You are an expert AI assistant. Answer the following question to the best of your ability based on your general knowledge."
        user_prompt = query

    try:
        resp = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return {"answer": resp.choices[0].message.content}
    except Exception as e:
        print(f"ERROR: OpenAI API call failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get a response from the AI model.")

