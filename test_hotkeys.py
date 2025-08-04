#!/usr/bin/env python3
"""
Test Hotkey Processing
"""

import asyncio
from ai_service import ai_service

async def test_hotkey_processing():
    """Test how the system handles hotkey inputs"""
    
    print("🔍 Testing Hotkey Processing")
    print("=" * 50)
    
    # Test various hotkey inputs
    hotkey_tests = [
        "R",
        "E", 
        "C",
        "F",
        "L"
    ]
    
    for hotkey in hotkey_tests:
        print(f"\n🔑 Testing hotkey: {hotkey}")
        try:
            result = await ai_service.process_query_with_gpt_intelligence(
                query=hotkey,
                context="",
                session_id="hotkey_test_session"
            )
            
            print(f"  • Response length: {len(result['answer'])} chars")
            print(f"  • Answer preview: {result['answer'][:100]}...")
            print(f"  • Enforcement applied: {result.get('clair_enforcement', {}).get('enforcement_applied', False)}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_hotkey_processing())