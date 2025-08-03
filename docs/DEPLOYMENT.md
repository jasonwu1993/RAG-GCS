# Deployment Guide: RAG System

## Backend (FastAPI)
1. Deploy to Render:
   - Create a new Web Service
   - Use Python 3.11 environment
   - Start command: `uvicorn main:app --host 0.0.0.0 --port 10000`
   - Add `OPENAI_API_KEY` to environment variables

2. Point frontend to this backend URL

## Frontend (Next.js)
1. Deploy to Vercel
2. Replace API URL with your Render backend endpoint
3. Customize UI to reflect your assistant branding

## Custom Domain
- Optional: Connect Vercel to Cloudflare and map `seminar.BeClair.ai`

## Future Enhancements
- PDF/Markdown ingestion
- FAISS vector store
- Metadata filtering


FAISS Overview
FAISS (Facebook AI Similarity Search) is a vector database:

Efficiently stores high-dimensional embeddings

Lets you find the most relevant chunks of text by similarity

Used in RAG systems to fetch the best context before GPT answers

🛠️ Deploy Instructions (Render)
Create a new Web Service with Python 3.11

Upload these files or point to GitHub repo

Add environment variable:
OPENAI_API_KEY = sk-...

Start command:
uvicorn main:app --host 0.0.0.0 --port 10000


What’s New in This Version
Feature	Description
✅ Multi-file support	Upload and index multiple .pdf or .md files
💾 Persistent FAISS vector store	Saved to disk (index_store/) and auto-loaded on restart
🏷️ Source tracking	GPT answers cite the file name (e.g., [GOODLIFE_REWARDS.pdf]: ...)
🔁 /reset endpoint	Wipes vector DB and metadata when called

 fully upgraded RAG backend is ready with:

🔍 /list_files to show available KB sources

🎯 /ask now supports search filters by file

🔗 GPT answers with Markdown-style file source links

🧠 PDF + Markdown support, persistent FAISS, reset endpoint

Feature	                        Description
✅ FAISS vector DB (on disk)	   Saved in index_store/, auto-loads on restart
✅ Upload .pdf or .md	            All content chunked + indexed, with filename stored
✅ Source citations	            GPT answers show file name using Markdown hyperlinks
✅ File filter	                  Users can search only selected files via checkboxes
✅ /list_files, /reset, /ask	   Ready for frontend integration