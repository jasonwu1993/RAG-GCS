#!/usr/bin/env python3
"""
Debug Environment Variables - Quick diagnostic for production environment
"""
import os
import json
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

# Check critical environment variables
env_vars = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "ENVIRONMENT": os.getenv("ENVIRONMENT"),
    "GPT_MODEL": os.getenv("GPT_MODEL"),
    "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID")
}

print("\n🔧 Environment Variables:")
for key, value in env_vars.items():
    if key == "OPENAI_API_KEY" and value:
        print(f"  {key}: {value[:15]}... (length: {len(value)})")
    elif value:
        print(f"  {key}: {value}")
    else:
        print(f"  {key}: ❌ NOT SET")

# Test if we can create OpenAI client
print("\n🤖 OpenAI Client Test:")
try:
    from openai import OpenAI
    client = OpenAI()
    print("✅ OpenAI client created successfully")
    
    # Try a simple call
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    print("✅ OpenAI API call successful")
    print(f"Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ OpenAI test failed: {e}")

if __name__ == "__main__":
    pass