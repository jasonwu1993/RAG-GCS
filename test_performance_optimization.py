#!/usr/bin/env python3
"""
Test Performance Optimizations
"""

import asyncio
import time
from ai_service import ai_service

async def test_performance_optimizations():
    """Test that performance optimizations are working"""
    
    print("🚀 Testing Performance Optimizations")
    print("=" * 60)
    
    # Test 1: Response caching
    print("\n1️⃣ Testing Response Caching:")
    test_query = "保险的基本概念是什么？"
    
    # First request (not cached)
    start_time = time.time()
    result1 = await ai_service.process_query_with_gpt_intelligence(
        query=test_query,
        context="",
        session_id="performance_test_1"
    )
    first_response_time = time.time() - start_time
    
    print(f"  First request time: {first_response_time:.2f}s")
    print(f"  Cached response flag: {result1.get('cached_response', 'Not set')}")
    
    # Second request (should be cached)
    start_time = time.time()
    result2 = await ai_service.process_query_with_gpt_intelligence(
        query=test_query,
        context="",
        session_id="performance_test_1"
    )
    second_response_time = time.time() - start_time
    
    print(f"  Second request time: {second_response_time:.2f}s")
    print(f"  Cached response flag: {result2.get('cached_response', 'Not set')}")
    
    # Calculate improvement
    if first_response_time > 0:
        improvement = ((first_response_time - second_response_time) / first_response_time) * 100
        print(f"  Performance improvement: {improvement:.1f}%")
    
    # Test 2: Token optimization
    print(f"\n2️⃣ Testing Token Optimization:")
    if 'token_usage' in result1:
        tokens = result1['token_usage']
        print(f"  Prompt tokens: {tokens.get('prompt_tokens', 'N/A')}")
        print(f"  Completion tokens: {tokens.get('completion_tokens', 'N/A')}")
        print(f"  Total tokens: {tokens.get('total_tokens', 'N/A')}")
        
        # Check if tokens are within optimized range
        total_tokens = tokens.get('total_tokens', 0)
        if total_tokens < 1500:
            print(f"  ✅ Token usage optimized: {total_tokens} tokens")
        else:
            print(f"  ⚠️ Token usage high: {total_tokens} tokens")
    
    # Test 3: Hotkey performance (should be instant)
    print(f"\n3️⃣ Testing Hotkey Performance:")
    start_time = time.time()
    hotkey_result = await ai_service.process_query_with_gpt_intelligence(
        query="R",
        context="",
        session_id="hotkey_test"
    )
    hotkey_time = time.time() - start_time
    
    print(f"  Hotkey response time: {hotkey_time:.3f}s")
    print(f"  Hotkey processed flag: {hotkey_result.get('hotkey_processed', 'Not set')}")
    
    if hotkey_time < 0.1:
        print(f"  ✅ Hotkey performance excellent: <0.1s")
    else:
        print(f"  ⚠️ Hotkey performance needs improvement: {hotkey_time:.3f}s")
    
    # Test 4: Overall performance summary
    print(f"\n🏆 Performance Summary:")
    print(f"  • First API call: {first_response_time:.2f}s")
    print(f"  • Cached response: {second_response_time:.3f}s")
    print(f"  • Hotkey response: {hotkey_time:.3f}s")
    
    # Check if all optimizations are working
    cache_working = result2.get('cached_response', False)
    hotkey_fast = hotkey_time < 0.1
    tokens_optimized = result1.get('token_usage', {}).get('total_tokens', 0) < 1500
    
    if cache_working and hotkey_fast and tokens_optimized:
        print(f"  🎉 All performance optimizations working!")
    else:
        print(f"  🔄 Some optimizations need attention:")
        if not cache_working:
            print(f"    - Response caching not working")
        if not hotkey_fast:
            print(f"    - Hotkey responses too slow")
        if not tokens_optimized:
            print(f"    - Token usage not optimized")

if __name__ == "__main__":
    asyncio.run(test_performance_optimizations())