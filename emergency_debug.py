#!/usr/bin/env python3
"""
Emergency Debug - Comprehensive System Diagnosis
Find and fix the OpenAI API failure issue
"""

import asyncio
import traceback
from datetime import datetime
import os
from dotenv import load_dotenv

# SECURE ENVIRONMENT LOADING - CONDITIONAL BASED ON DEPLOYMENT
# =================================================================
# LOCAL DEVELOPMENT: Load from .env file (development only)
# PRODUCTION (Cloud Run): Use Google Secret Manager (secure)
# =================================================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
print(f"🔧 Environment: {ENVIRONMENT}")

if ENVIRONMENT == "development":
    # LOCAL DEVELOPMENT ONLY: Load .env file
    try:
        load_dotenv()
        print("📁 [LOCAL] Loaded environment variables from .env file")
    except Exception as e:
        print(f"⚠️ [LOCAL] Failed to load .env file: {e}")
else:
    # PRODUCTION: Environment variables come from Google Secret Manager via Cloud Run
    print("🏭 [PRODUCTION] Using environment variables from Google Secret Manager")
    print("🔐 [SECURITY] .env file loading disabled in production for security")

async def emergency_diagnosis():
    """Comprehensive system diagnosis to find the API failure"""
    print("🚨 EMERGENCY DIAGNOSIS - OpenAI API Failure")
    print("=" * 55)
    
    # Test 1: Environment and Basic Setup
    print("\n1️⃣ Environment Check:")
    print(f"  API Key set: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")
    print(f"  API Key starts with: {os.getenv('OPENAI_API_KEY', '')[:10]}...")
    
    # Test 2: OpenAI Client Direct Test
    print(f"\n2️⃣ OpenAI Client Direct Test:")
    try:
        from openai import OpenAI
        client = OpenAI()
        
        # Simple direct test
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API test successful' in Chinese"}
            ],
            max_tokens=50,
            temperature=0.3
        )
        
        print("  ✅ Direct OpenAI client works")
        print(f"  📝 Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"  ❌ Direct OpenAI client FAILED: {e}")
        print(f"  📋 Full error: {traceback.format_exc()}")
        return
    
    # Test 3: Config Loading
    print(f"\n3️⃣ Config Loading Test:")
    try:
        from config import (CLAIR_SYSTEM_PROMPT_ACTIVE, GPT_MODEL, 
                          ENABLE_STRUCTURED_OUTPUTS, MAX_TOKENS, TEMPERATURE)
        
        print(f"  ✅ Config loaded successfully")
        print(f"  📄 System prompt length: {len(CLAIR_SYSTEM_PROMPT_ACTIVE):,} chars")
        print(f"  🤖 Model: {GPT_MODEL}")
        print(f"  📊 Max tokens: {MAX_TOKENS}")
        print(f"  🌡️ Temperature: {TEMPERATURE}")
        print(f"  📋 Structured outputs: {ENABLE_STRUCTURED_OUTPUTS}")
        
    except Exception as e:
        print(f"  ❌ Config loading FAILED: {e}")
        print(f"  📋 Full error: {traceback.format_exc()}")
        return
    
    # Test 4: AI Service Loading
    print(f"\n4️⃣ AI Service Loading Test:")
    try:
        from ai_service import IntelligentAIService, get_openai_client
        
        print("  ✅ AI service imports successful")
        
        ai_client = get_openai_client()
        if ai_client:
            print("  ✅ AI service OpenAI client available")
        else:
            print("  ❌ AI service OpenAI client NOT available")
            return
            
    except Exception as e:
        print(f"  ❌ AI service loading FAILED: {e}")
        print(f"  📋 Full error: {traceback.format_exc()}")
        return
    
    # Test 5: System Prompt API Test
    print(f"\n5️⃣ Full System Prompt API Test:")
    try:
        # Test with the actual system prompt that's failing
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": CLAIR_SYSTEM_PROMPT_ACTIVE},
                {"role": "user", "content": "您都有什么样的保险"}
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=0.95,
            presence_penalty=0.2,
            frequency_penalty=0.05
        )
        
        print("  ✅ Full system prompt API call successful")
        print(f"  📝 Response preview: {response.choices[0].message.content[:200]}...")
        
        # Check if it's in Chinese
        response_text = response.choices[0].message.content
        chinese_chars = sum(1 for c in response_text if '\u4e00' <= c <= '\u9fff')
        print(f"  🇨🇳 Chinese characters: {chinese_chars}")
        print(f"  ✅ Language: {'Chinese' if chinese_chars > 10 else 'English'}")
        
    except Exception as e:
        print(f"  ❌ Full system prompt API call FAILED: {e}")
        print(f"  📋 Full error: {traceback.format_exc()}")
        
        # Check if it's a token limit issue
        if "token" in str(e).lower():
            print("  ⚠️ POSSIBLE TOKEN LIMIT ISSUE")
            print(f"  📏 System prompt length: {len(CLAIR_SYSTEM_PROMPT_ACTIVE):,} characters")
            
            # Try with shorter prompt
            print(f"\n  🧪 Testing with shorter prompt:")
            try:
                short_response = client.chat.completions.create(
                    model=GPT_MODEL,
                    messages=[
                        {"role": "system", "content": "You are Clair, a financial advisor. Respond in Chinese."},
                        {"role": "user", "content": "您都有什么样的保险"}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                
                print("    ✅ Short prompt works")
                print(f"    📝 Response: {short_response.choices[0].message.content[:100]}...")
                
            except Exception as e2:
                print(f"    ❌ Short prompt also fails: {e2}")
        
        return
    
    # Test 6: AI Service Integration
    print(f"\n6️⃣ AI Service Integration Test:")
    try:
        ai_service = IntelligentAIService()
        
        result = await ai_service.process_query_with_ultra_intelligence(
            query="您都有什么样的保险",
            context="",
            session_id="emergency_debug_session"
        )
        
        print("  ✅ AI service integration successful")
        print(f"  📝 Answer preview: {result.get('answer', '')[:200]}...")
        
        # Check for the error message
        if "technical difficulties" in result.get('answer', ''):
            print("  ❌ Still getting technical difficulties error")
            print("  📋 Full result:", result)
        else:
            print("  ✅ AI service working correctly")
            
    except Exception as e:
        print(f"  ❌ AI service integration FAILED: {e}")
        print(f"  📋 Full error: {traceback.format_exc()}")
    
    print(f"\n🎯 EMERGENCY DIAGNOSIS SUMMARY:")
    print("  If direct API works but AI service fails:")
    print("  → Issue is in AI service implementation")
    print("  If system prompt API fails:")
    print("  → Issue is token limits or prompt content")
    print("  If OpenAI client fails:")
    print("  → Issue is API key or connection")

if __name__ == "__main__":
    asyncio.run(emergency_diagnosis())