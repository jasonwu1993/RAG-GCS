#!/usr/bin/env python3
"""
Test Hotkey Duplication Fix
"""

import asyncio
from ai_service import ai_service

async def test_hotkey_duplication_fix():
    """Test that hotkey duplication is fixed"""
    
    print("🧪 Testing Hotkey Duplication Fix")
    print("=" * 50)
    
    # Test the same query that showed duplication
    query = "2个大人，2个孩子 大人50， 55.。小孩子：20， 24"
    
    result = await ai_service.process_query_with_gpt_intelligence(
        query=query, context="", session_id="hotkey_fix_test"
    )
    
    response = result['answer']
    
    print("📝 Full Response:")
    print("-" * 50)
    print(response)
    print("-" * 50)
    
    # Check for duplication
    quick_suggestions_count = response.count("quick suggestions")
    hotkey_sections = response.count("💡")
    
    print(f"\n📊 Analysis:")
    print(f"  • 'quick suggestions' mentions: {quick_suggestions_count}")
    print(f"  • Hotkey sections (💡): {hotkey_sections}")
    print(f"  • Total response length: {len(response)} chars")
    
    if quick_suggestions_count <= 1 and hotkey_sections <= 1:
        print("  ✅ No duplicate hotkeys detected!")
    else:
        print("  ⚠️ Potential duplicate hotkeys still present")
    
    # Check if GPT-generated hotkeys are contextual
    if "Advance with details" in response or "Talk to an agent" in response:
        print("  ✅ Contextual hotkeys present")
    else:
        print("  ⚠️ Contextual hotkeys may be missing")

if __name__ == "__main__":
    asyncio.run(test_hotkey_duplication_fix())