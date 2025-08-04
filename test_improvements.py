#!/usr/bin/env python3
"""
Test All Improvements
"""

import asyncio
from ai_service import ai_service

async def test_all_improvements():
    """Test all the improvements made"""
    
    print("🧪 Testing All Improvements")
    print("=" * 60)
    
    session_id = "improvement_test_session"
    
    # Test 1: Chinese query (should not repeat introduction)
    print("\n1️⃣ Testing Chinese Query (No Repetitive Intro):")
    query1 = "介绍一下你们代理的产品"
    result1 = await ai_service.process_query_with_gpt_intelligence(
        query=query1, context="", session_id=session_id
    )
    print(f"  • Response length: {len(result1['answer'])} chars")
    print(f"  • Answer preview: {result1['answer'][:100]}...")
    print(f"  • Enforcement applied: {result1.get('clair_enforcement', {}).get('enforcement_applied', False)}")
    
    # Test 2: Hotkey R
    print("\n2️⃣ Testing Hotkey R:")
    result2 = await ai_service.process_query_with_ultra_intelligence(
        query="R", context="", session_id=session_id
    )
    print(f"  • Response length: {len(result2['answer'])} chars")
    print(f"  • Hotkey processed: {result2.get('hotkey_processed', False)}")
    print(f"  • Answer preview: {result2['answer'][:100]}...")
    
    # Test 3: Hotkey E  
    print("\n3️⃣ Testing Hotkey E:")
    result3 = await ai_service.process_query_with_ultra_intelligence(
        query="E", context="", session_id=session_id
    )
    print(f"  • Response length: {len(result3['answer'])} chars")
    print(f"  • Hotkey processed: {result3.get('hotkey_processed', False)}")
    print(f"  • Answer preview: {result3['answer'][:100]}...")
    
    # Test 4: Policy trigger (should not trigger for existing policy)
    print("\n4️⃣ Testing Existing Policy Query:")
    query4 = "我去年已经买了一份保单"
    result4 = await ai_service.process_query_with_gpt_intelligence(
        query=query4, context="", session_id=session_id
    )
    print(f"  • Response length: {len(result4['answer'])} chars")
    print(f"  • Mandatory links: {result4.get('clair_enforcement', {}).get('mandatory_links', [])}")
    print(f"  • Answer preview: {result4['answer'][:100]}...")
    
    # Test 5: Performance timing
    print("\n5️⃣ Testing Response Time:")
    import time
    start_time = time.time()
    result5 = await ai_service.process_query_with_gpt_intelligence(
        query="什么是保险？", context="", session_id=session_id
    )
    end_time = time.time()
    response_time = end_time - start_time
    print(f"  • Response time: {response_time:.2f} seconds")
    print(f"  • Processing time (internal): {result5['processing_time_seconds']:.2f} seconds")
    print(f"  • Target: <3 seconds")
    print(f"  • Status: {'✅ PASS' if response_time < 3.0 else '❌ SLOW'}")

if __name__ == "__main__":
    asyncio.run(test_all_improvements())