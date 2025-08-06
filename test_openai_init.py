#!/usr/bin/env python3
"""
Test OpenAI Client Initialization
"""

import os
from dotenv import load_dotenv

# SECURE ENVIRONMENT LOADING - FOR TESTING
# Local development testing only
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "development":
    load_dotenv()
    print("📁 [TEST] Loaded .env for local testing")
else:
    print("🏭 [TEST] Using production environment variables")

print("🔍 Testing OpenAI Client Initialization")
print("=" * 50)

# Check environment variable
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    print(f"✅ OpenAI API key found: {openai_key[:8]}...")
else:
    print("❌ OpenAI API key not found")
    exit(1)

# Test direct OpenAI import and initialization
try:
    from openai import OpenAI
    print("✅ OpenAI import successful")
    
    # Test client creation
    client = OpenAI()
    print("✅ OpenAI client created successfully")
    
    # Test a simple API call
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello World' in Chinese"}
        ],
        max_tokens=50,
        temperature=0.7
    )
    
    answer = response.choices[0].message.content
    print(f"✅ OpenAI API call successful: {answer}")
    
except Exception as e:
    print(f"❌ OpenAI error: {e}")
    import traceback
    traceback.print_exc()

# Test core initialization
print("\n🔧 Testing Core Initialization:")
try:
    from core import initialize_openai_client, openai_client
    print(f"• OpenAI client before init: {openai_client}")
    
    success = initialize_openai_client()
    print(f"• Initialization success: {success}")
    
    from core import openai_client as updated_client
    print(f"• OpenAI client after init: {updated_client}")
    
except Exception as e:
    print(f"❌ Core initialization error: {e}")
    import traceback
    traceback.print_exc()