#!/usr/bin/env python3
"""
Test script to validate Clair's compliance with system prompt guidelines
"""

import asyncio
import json
from ai_service import ai_service

async def test_clair_compliance():
    """Test various scenarios to ensure Clair follows system prompt guidelines"""
    
    test_cases = [
        {
            "name": "Insurance Recommendation Query",
            "query": "What insurance is right for me?",
            "context": "",
            "expected_compliance": ["disclaimer", "personalization_questions"]
        },
        {
            "name": "Policy Comparison Query", 
            "query": "Should I get term or whole life insurance?",
            "context": "",
            "expected_compliance": ["disclaimer", "personalization_questions"]
        },
        {
            "name": "General Information Query",
            "query": "What is life insurance?",
            "context": "",
            "expected_compliance": ["educational_tone"]
        },
        {
            "name": "Context Available Query",
            "query": "What are the premium rates for a 35-year-old?",
            "context": "Premium rates for Term Life Insurance: Age 35, Male, $500,000 coverage: $45/month for 20-year term.",
            "expected_compliance": ["reference_context", "disclaimer"]
        }
    ]
    
    print("🧪 Testing Clair's System Prompt Compliance")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        
        try:
            result = await ai_service.process_query_with_gpt_intelligence(
                query=test_case["query"],
                context=test_case["context"],
                session_id=f"test_session_{i}"
            )
            
            print(f"✅ Response generated successfully")
            print(f"📊 Compliance Score: {result['compliance_validation']['compliance_score']:.2f}")
            
            if result['compliance_validation']['issues']:
                print(f"⚠️  Issues: {', '.join(result['compliance_validation']['issues'])}")
                
            if result['compliance_validation']['recommendations']:
                print(f"💡 Recommendations: {', '.join(result['compliance_validation']['recommendations'])}")
            
            print(f"📝 Response Preview: {result['answer'][:200]}...")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("-" * 40)
    
    print("\n✅ Compliance testing completed!")

if __name__ == "__main__":
    asyncio.run(test_clair_compliance())