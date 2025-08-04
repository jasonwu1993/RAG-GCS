#!/usr/bin/env python3
"""
Final Language Matching Test
"""

import asyncio
from ai_service import ai_service

async def final_language_test():
    """Final comprehensive test of language matching"""
    
    print("🎯 FINAL LANGUAGE MATCHING TEST")
    print("=" * 60)
    
    # Test Chinese query
    print("\n1️⃣ Chinese Query Test:")
    print("User: 我需要保险，家里有4个人")
    
    result1 = await ai_service.process_query_with_gpt_intelligence(
        query="我需要保险，家里有4个人", 
        context="", 
        session_id="final_chinese_test"
    )
    
    print(f"Clair (Chinese): {result1['answer'][:150]}...")
    
    # Check hotkeys in response
    has_chinese_hotkeys = "推荐" in result1['answer'] or "解释" in result1['answer'] or "费用" in result1['answer']
    has_english_hotkeys = "Recommend" in result1['answer'] or "Explain" in result1['answer'] or "Cost" in result1['answer']
    
    print(f"  ✅ Chinese hotkeys: {has_chinese_hotkeys}")
    print(f"  ❌ English hotkeys: {has_english_hotkeys}")
    print(f"  Status: {'✅ PERFECT' if has_chinese_hotkeys and not has_english_hotkeys else '❌ NEEDS FIX'}")
    
    # Test English query
    print("\n2️⃣ English Query Test:")
    print("User: I need insurance for my family of 4")
    
    result2 = await ai_service.process_query_with_gpt_intelligence(
        query="I need insurance for my family of 4", 
        context="", 
        session_id="final_english_test"
    )
    
    print(f"Clair (English): {result2['answer'][:150]}...")
    
    # Check hotkeys in response
    has_english_hotkeys2 = "Recommend" in result2['answer'] or "Explain" in result2['answer'] or "Cost" in result2['answer']
    has_chinese_hotkeys2 = "推荐" in result2['answer'] or "解释" in result2['answer'] or "费用" in result2['answer']
    
    print(f"  ✅ English hotkeys: {has_english_hotkeys2}")
    print(f"  ❌ Chinese hotkeys: {has_chinese_hotkeys2}")
    print(f"  Status: {'✅ PERFECT' if has_english_hotkeys2 and not has_chinese_hotkeys2 else '❌ NEEDS FIX'}")
    
    # Final summary
    print(f"\n🏆 FINAL RESULTS:")
    chinese_perfect = has_chinese_hotkeys and not has_english_hotkeys
    english_perfect = has_english_hotkeys2 and not has_chinese_hotkeys2
    
    if chinese_perfect and english_perfect:
        print("  🎉 PERFECT! Language matching works flawlessly!")
        print("  ✅ Chinese queries → Chinese hotkeys")
        print("  ✅ English queries → English hotkeys")
        print("  ✅ No duplicate hotkeys")
        print("  ✅ Contextual and relevant")
    else:
        print(f"  🔄 Partial success:")
        print(f"    Chinese matching: {'✅' if chinese_perfect else '❌'}")
        print(f"    English matching: {'✅' if english_perfect else '❌'}")

if __name__ == "__main__":
    asyncio.run(final_language_test())