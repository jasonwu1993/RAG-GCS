#!/usr/bin/env python3
"""
Clair Enterprise RAG System - Server Runner
Run the application from the root directory with proper Python path setup
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Import and run the main application
if __name__ == "__main__":
    import uvicorn
    from main import app
    
    print("🚀 Starting Clair Enterprise RAG System...")
    print(f"📁 Working directory: {current_dir}")
    print(f"🐍 Python path includes: {src_dir}")
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )