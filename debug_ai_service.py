#!/usr/bin/env python3
"""
Debug AI Service Processing
Find out why the AI service is failing for Chinese queries
"""

import asyncio
import traceback
from datetime import datetime

async def debug_ai_service_flow():
    """Debug the AI service processing flow"""
    
    print("🔍 Debugging AI Service Flow")
    print("=" * 60)
    
    query = "我需要保险"
    print(f"Query: {query}")
    
    # Step 1: Test core imports
    print("\n1️⃣ Testing Core Imports:")
    try:
        from core import log_debug, track_function_entry, openai_client
        print("  ✅ Core imports successful")
        print(f"  • OpenAI client available: {openai_client is not None}")
    except Exception as e:
        print(f"  ❌ Core import failed: {e}")
        return
    
    # Step 2: Test config imports
    print("\n2️⃣ Testing Config Imports:")
    try:
        from config import (GPT_MODEL, MAX_TOKENS, TEMPERATURE, TOP_P, 
                           PRESENCE_PENALTY, FREQUENCY_PENALTY, CLAIR_SYSTEM_PROMPT_ACTIVE)
        print("  ✅ Config imports successful")
        print(f"  • GPT Model: {GPT_MODEL}")
        print(f"  • System prompt length: {len(CLAIR_SYSTEM_PROMPT_ACTIVE)} chars")
    except Exception as e:
        print(f"  ❌ Config import failed: {e}")
        return
    
    # Step 3: Test AI service import
    print("\n3️⃣ Testing AI Service Import:")
    try:
        from ai_service import ai_service
        print("  ✅ AI service import successful")
        print(f"  • AI service available: {ai_service is not None}")
        print(f"  • Ultra intelligence enabled: {ai_service.ultra_intelligence_enabled}")
        print(f"  • Prompt enforcer enabled: {ai_service.prompt_enforcer_enabled}")
    except Exception as e:
        print(f"  ❌ AI service import failed: {e}")
        traceback.print_exc()
        return
    
    # Step 4: Test environment variables
    print("\n4️⃣ Testing Environment Variables:")
    import os
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"  ✅ OpenAI API key available: {openai_key[:8]}...")
    else:
        print("  ❌ OpenAI API key not set")
    
    # Step 5: Test direct AI service call
    print("\n5️⃣ Testing Direct AI Service Call:")
    try:
        result = await ai_service.process_query_with_ultra_intelligence(
            query=query,
            context="",
            session_id="debug_session"
        )
        print("  ✅ AI service call successful")
        print(f"  • Response length: {len(result.get('answer', ''))} chars")
        print(f"  • Answer preview: {result.get('answer', '')[:100]}...")
        print(f"  • Enforcement applied: {result.get('clair_enforcement', {}).get('enforcement_applied', False)}")
        print(f"  • Language enforcement: {result.get('clair_enforcement', {}).get('language_enforcement', False)}")
    except Exception as e:
        print(f"  ❌ AI service call failed: {e}")
        traceback.print_exc()
        
        # Try fallback GPT processing
        print("\n  🔄 Trying fallback GPT processing:")
        try:
            result = await ai_service.process_query_with_gpt_intelligence(
                query=query,
                context="",
                session_id="debug_session"
            )
            print("    ✅ Fallback GPT processing successful")
            print(f"    • Response length: {len(result.get('answer', ''))} chars")
            print(f"    • Answer preview: {result.get('answer', '')[:100]}...")
        except Exception as fallback_error:
            print(f"    ❌ Fallback GPT processing failed: {fallback_error}")
            traceback.print_exc()

if __name__ == "__main__":
    print("Starting AI Service Debug...")
    asyncio.run(debug_ai_service_flow())