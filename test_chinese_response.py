#!/usr/bin/env python3
"""
Test Chinese Response Generation
Verify that "我需要保险" produces a proper Chinese response
"""

import asyncio
import json
from datetime import datetime
from ai_service import ai_service
from clair_prompt_enforcer import clair_prompt_enforcer

async def test_chinese_query():
    """Test Chinese query handling"""
    
    print("🧪 Testing Chinese Query Response")
    print("=" * 60)
    
    # Test query
    query = "我需要保险"
    print(f"Query: {query}")
    
    # Test 1: Direct enforcer test
    print("\n1️⃣ Testing Enforcer Directly:")
    mock_response = "Hello! I'm Clair, your trusted AI financial advisor..."
    enforced_response, enforcement_result = clair_prompt_enforcer.enforce_system_prompt(query, mock_response)
    
    print(f"  • English detected: {not enforcement_result.needs_chinese}")
    print(f"  • Needs Chinese: {enforcement_result.needs_chinese}")
    print(f"  • Trigger type: {enforcement_result.trigger_type}")
    print(f"  • Enforcement applied: {enforcement_result.enforcement_applied}")
    print(f"  • Response preview: {enforced_response[:100]}...")
    
    # Test 2: Full AI service test
    print("\n2️⃣ Testing Full AI Service:")
    try:
        result = await ai_service.process_query_with_ultra_intelligence(
            query=query,
            context="",
            session_id="test_chinese_session"
        )
        
        print(f"  • Response generated successfully")
        print(f"  • Language enforcement: {result.get('clair_enforcement', {}).get('language_enforcement', False)}")
        print(f"  • Enforcement applied: {result.get('clair_enforcement', {}).get('enforcement_applied', False)}")
        print(f"  • Response length: {len(result['answer'])} characters")
        print(f"\n📝 Response:")
        print("-" * 40)
        print(result['answer'])
        print("-" * 40)
        
        # Check if response contains Chinese
        chinese_chars = len([c for c in result['answer'] if '\u4e00' <= c <= '\u9fff'])
        total_chars = len(result['answer'].replace(' ', '').replace('\n', ''))
        chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
        
        print(f"\n📊 Analysis:")
        print(f"  • Chinese characters: {chinese_chars}")
        print(f"  • Total characters: {total_chars}")
        print(f"  • Chinese ratio: {chinese_ratio:.1%}")
        
        if chinese_ratio > 0.5:
            print("  ✅ Response is in Chinese!")
        else:
            print("  ❌ Response is NOT in Chinese!")
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    # Test 3: Test other Chinese queries
    print("\n3️⃣ Testing Additional Chinese Queries:")
    
    test_queries = [
        "什么是保险？",
        "我需要生成保单",
        "保险市场现状如何？",
        "请比较不同的保险产品"
    ]
    
    for test_query in test_queries:
        print(f"\n  Testing: {test_query}")
        _, enforcement_result = clair_prompt_enforcer.enforce_system_prompt(test_query, "test")
        print(f"    • Needs Chinese: {enforcement_result.needs_chinese}")
        print(f"    • Trigger type: {enforcement_result.trigger_type}")
        print(f"    • Mandatory links: {enforcement_result.mandatory_links}")

if __name__ == "__main__":
    print("Starting Chinese Response Test...")
    asyncio.run(test_chinese_query())