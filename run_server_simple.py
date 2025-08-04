#!/usr/bin/env python3
"""
Simple server runner that uses the working modular architecture from 7104d64
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add current directory to Python path for modular imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    print("🚀 Starting Simple RAG Clair System with Working Sync Endpoint...")
    print(f"📁 Working directory: {current_dir}")
    
    try:
        # Import the working modular app
        from main_modular import app
        print("✅ Successfully imported main_modular app")
        
        # Run with uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8080)),
            reload=False
        )
    except Exception as e:
        print(f"❌ Failed to start with main_modular: {e}")
        print("🔄 Falling back to simple implementation...")
        
        # Import the simple app we created
        from main_simple import app
        print("✅ Using simple app with working sync endpoint")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8080)),
            reload=False
        )