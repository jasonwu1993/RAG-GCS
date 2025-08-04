#!/usr/bin/env python3
"""
Test Language Matching for Hotkeys
"""

import asyncio
from ai_service import ai_service

async def test_language_matching():
    """Test that hotkeys match the language of the main response"""
    
    print("🧪 Testing Language Matching for Hotkeys")
    print("=" * 60)
    
    # Test 1: Chinese query should get Chinese hotkeys
    print("\n1️⃣ Testing Chinese Query:")
    print("User: 2个大人，2个孩子 大人50， 55.。小孩子：20， 24")
    
    result1 = await ai_service.process_query_with_gpt_intelligence(
        query="2个大人，2个孩子 大人50， 55.。小孩子：20， 24", 
        context="", 
        session_id="chinese_test_session"
    )
    
    response1 = result1['answer']
    print(f"Clair: {response1[:150]}...")
    
    # Check if hotkeys are in Chinese
    has_chinese_hotkeys = "推荐" in response1 or "解释" in response1 or "费用" in response1
    has_english_hotkeys = "Recommend" in response1 or "Explain" in response1 or "Cost" in response1
    
    print(f"\n  📊 Analysis:")
    print(f"  • Has Chinese hotkeys: {has_chinese_hotkeys}")
    print(f"  • Has English hotkeys: {has_english_hotkeys}")
    print(f"  • Status: {'✅ CORRECT' if has_chinese_hotkeys and not has_english_hotkeys else '❌ INCORRECT'}")
    
    # Test 2: English query should get English hotkeys
    print("\n2️⃣ Testing English Query:")
    print("User: Tell me about your insurance products")
    
    result2 = await ai_service.process_query_with_gpt_intelligence(
        query="Tell me about your insurance products", 
        context="", 
        session_id="english_test_session"
    )
    
    response2 = result2['answer']
    print(f"Clair: {response2[:150]}...")
    
    # Check if hotkeys are in English
    has_english_hotkeys2 = "Recommend" in response2 or "Explain" in response2 or "Cost" in response2
    has_chinese_hotkeys2 = "推荐" in response2 or "解释" in response2 or "费用" in response2
    
    print(f"\n  📊 Analysis:")
    print(f"  • Has English hotkeys: {has_english_hotkeys2}")
    print(f"  • Has Chinese hotkeys: {has_chinese_hotkeys2}")
    print(f"  • Status: {'✅ CORRECT' if has_english_hotkeys2 and not has_chinese_hotkeys2 else '❌ INCORRECT'}")
    
    # Summary
    print(f"\n🎯 SUMMARY:")
    chinese_correct = has_chinese_hotkeys and not has_english_hotkeys
    english_correct = has_english_hotkeys2 and not has_chinese_hotkeys2
    
    if chinese_correct and english_correct:
        print("  ✅ Language matching is working perfectly!")
    elif chinese_correct:
        print("  🔄 Chinese matching works, English needs improvement")
    elif english_correct:
        print("  🔄 English matching works, Chinese needs improvement")
    else:
        print("  ❌ Language matching needs further fixes")

if __name__ == "__main__":
    asyncio.run(test_language_matching())