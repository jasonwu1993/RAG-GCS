#!/usr/bin/env python3
"""
Minimal test to see if the basic app structure can start
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

if __name__ == "__main__":
    try:
        print("🧪 Testing minimal app import...")
        
        # Test basic FastAPI import
        from fastapi import FastAPI
        print("✅ FastAPI import successful")
        
        # Test our main app import
        from main import app
        print("✅ Main app import successful")
        print(f"App type: {type(app)}")
        
        # Try to start with uvicorn
        import uvicorn
        print("🚀 Starting minimal test server...")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8080)),
            reload=False,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)