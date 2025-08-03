from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import pickle
import numpy as np
import tiktoken
import pdfplumber
from openai import OpenAI
from typing import List

# --- App & Middleware Setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration & Initialization ---
EMBED_MODEL = "text-embedding-3-small"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize the OpenAI client (it automatically uses the OPENAI_API_KEY env var)
client = OpenAI()

# --- Core Logic Functions ---

def embed_text(text: str) -> np.ndarray:
    """Generates an embedding for a given text using the specified OpenAI model."""
    response = client.embeddings.create(input=[text], model=EMBED_MODEL)
    return np.array(response.data[0].embedding, dtype='float32')

def split_text(text: str, max_tokens: int = 500) -> List[str]:
    """Splits text into chunks of a maximum token size."""
    enc = tiktoken.get_encoding("cl100k_base")
    words = text.split()
    chunks = []
    current_chunk = []
    current_token_count = 0
    for word in words:
        # Estimate token count for the word
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
    """Extracts text content from a PDF file, including tables."""
    texts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                texts.append(page_text)
            
            # Extract tables and format them as markdown
            tables = page.extract_tables()
            for table in tables:
                if table:
                    table_md = "\n".join([" | ".join(map(str, row)) for row in table])
                    texts.append(table_md)
                    
    return "\n\n".join(texts)

# --- API Endpoints ---

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """Handles file uploads, parsing, chunking, embedding, and saving."""
    try:
        # Save the file temporarily
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Parse text based on file type
        if file.filename.lower().endswith('.pdf'):
            text_content = parse_pdf(file_path)
        else: # Assumes .md or other text files
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()

        # Split text into chunks
        chunks = split_text(text_content)
        
        # Create embeddings for each chunk
        vectors = [embed_text(chunk) for chunk in chunks]

        # Save chunks and their vectors to a pickle file
        pickle_filename = f"{os.path.splitext(file.filename)[0]}.pkl"
        pickle_path = os.path.join(UPLOAD_DIR, pickle_filename)
        with open(pickle_path, "wb") as f:
            pickle.dump((chunks, vectors), f)
            
        # Clean up the original uploaded file
        os.remove(file_path)

        return {"message": f"File '{file.filename}' processed and saved as '{pickle_filename}'"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/list_files")
def list_files():
    """Lists all available .pkl files for context selection."""
    files = sorted([f for f in os.listdir(UPLOAD_DIR) if f.endswith('.pkl')])
    return {"files": files}

@app.post("/delete_file")
async def delete_file(request: Request):
    """Deletes a specified file from the server."""
    try:
        data = await request.json()
        filename = data.get("filename")
        if not filename:
            return {"error": "Filename not provided"}, 400

        file_path = os.path.join(UPLOAD_DIR, filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            return {"message": f"File '{filename}' deleted successfully."}
        else:
            return {"error": f"File '{filename}' not found."}, 404
    except Exception as e:
        return {"error": str(e)}, 500

@app.post("/ask")
async def ask(request: Request):
    """Answers a query using context from selected files (RAG)."""
    data = await request.json()
    query = data.get("query", "")
    filters = data.get("filters", []) # These are the .pkl filenames

    if not query or not filters:
        return {"answer": "Please provide a query and select at least one document."}

    query_vec = embed_text(query)
    
    # Find the most relevant chunk from the selected files
    top_results = []
    for fname in filters:
        db_path = os.path.join(UPLOAD_DIR, fname)
        if not os.path.exists(db_path):
            continue
        
        with open(db_path, "rb") as f:
            chunks, vectors = pickle.load(f)
            
        # Calculate cosine similarity scores
        scores = [np.dot(query_vec, v) for v in vectors]
        if scores:
            top_idx = int(np.argmax(scores))
            top_results.append(chunks[top_idx])

    if not top_results:
        return {"answer": "Could not find relevant information in the selected documents."}
        
    context = "\n\n---\n\n".join(top_results)
    prompt = f"Using the following context, answer the question.\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    
    # Get the answer from the LLM
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return {"answer": resp.choices[0].message.content}
