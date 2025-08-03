#!/usr/bin/env python3
"""
Diagnostic script to debug deployment issues
"""

import os
import sys

print("=== DEPLOYMENT DIAGNOSTIC ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")
print()

print("=== FILES IN CURRENT DIRECTORY ===")
try:
    files = os.listdir(".")
    for f in sorted(files):
        if f.endswith('.py'):
            print(f"✅ {f}")
    print()
except Exception as e:
    print(f"❌ Error listing files: {e}")

print("=== TESTING INDIVIDUAL IMPORTS ===")

modules_to_test = [
    'core',
    'config', 
    'ai_service',
    'google_drive',
    'documents_router',
    'search_router',
    'chat_router',
    'admin_router'
]

for module in modules_to_test:
    try:
        __import__(module)
        print(f"✅ {module} - OK")
    except Exception as e:
        print(f"❌ {module} - FAILED: {e}")

print("\n=== TESTING FUNCTION IMPORTS ===")

function_tests = [
    ('ai_service', ['split_text', 'embed_text', 'ai_service']),
    ('google_drive', ['ultra_sync']),
    ('core', ['log_debug', 'track_function_entry', 'global_state', 'bucket', 'index_endpoint']),
    ('config', ['DEPLOYED_INDEX_ID', 'TOP_K', 'SIMILARITY_THRESHOLD', 'CLAIR_GREETING'])
]

for module, functions in function_tests:
    try:
        mod = __import__(module)
        for func in functions:
            if hasattr(mod, func):
                print(f"✅ {module}.{func} - OK")
            else:
                print(f"❌ {module}.{func} - NOT FOUND")
    except Exception as e:
        print(f"❌ {module} module failed: {e}")

print("\n=== SYSTEM PROMPT FILE CHECK ===")
if os.path.exists("Clair-sys-prompt.txt"):
    print("✅ Clair-sys-prompt.txt exists")
    with open("Clair-sys-prompt.txt", "r") as f:
        content = f.read()
        print(f"📝 File size: {len(content)} characters")
        print(f"📝 First 100 chars: {content[:100]}...")
else:
    print("❌ Clair-sys-prompt.txt NOT FOUND")

print("\n=== DIAGNOSTIC COMPLETE ===")