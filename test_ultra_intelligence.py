#!/usr/bin/env python3
"""
Ultra-Intelligence Test Suite for Clair
Demonstrates the advanced multi-source routing and synthesis capabilities
"""

import asyncio
import json
from datetime import datetime
from ai_service import ai_service

class UltraIntelligenceDemo:
    """Demonstrate Clair's ultra-intelligent capabilities"""
    
    def __init__(self):
        self.test_scenarios = [
            {
                "name": "Policy-Specific Query",
                "query": "What are the specific premium rates for a 35-year-old male for $500,000 term life insurance?",
                "context": "Premium Schedule: Age 35, Male, Non-smoker, $500,000 20-Year Term: $42/month",
                "expected_routing": ["vertex_database"],
                "expected_query_type": "policy_specific"
            },
            {
                "name": "Market Trends Query",
                "query": "What are the current life insurance rates trending in 2024?",
                "context": "",
                "expected_routing": ["internet_search"],
                "expected_query_type": "market_trends"
            },
            {
                "name": "Comparative Analysis Query",
                "query": "Should I choose term life or whole life insurance for my situation?",
                "context": "Term Life: Lower premiums, temporary coverage. Whole Life: Higher premiums, permanent coverage with cash value.",
                "expected_routing": ["vertex_database", "internet_search"],
                "expected_query_type": "comparative"
            },
            {
                "name": "Educational Query",
                "query": "What is the difference between term and whole life insurance?",
                "context": "",
                "expected_routing": ["knowledge_base"],
                "expected_query_type": "educational"
            },
            {
                "name": "Current Events Query",
                "query": "What are the latest regulatory changes affecting life insurance in 2024?",
                "context": "",
                "expected_routing": ["internet_search"],
                "expected_query_type": "current_events"
            },
            {
                "name": "Personalized Advice Query",
                "query": "I'm 45 years old with two kids. What type of life insurance would you recommend for me?",
                "context": "",
                "expected_routing": ["vertex_database", "internet_search"],
                "expected_query_type": "personalized"
            }
        ]
    
    async def run_comprehensive_demo(self):
        """Run comprehensive demonstration of ultra-intelligence capabilities"""
        
        print("🚀 CLAIR ULTRA-INTELLIGENCE DEMONSTRATION")
        print("=" * 80)
        print("Testing advanced multi-source routing and synthesis capabilities")
        print(f"Test started at: {datetime.utcnow().isoformat()}")
        print("\n")
        
        results = []
        
        for i, scenario in enumerate(self.test_scenarios, 1):
            print(f"📋 TEST {i}: {scenario['name']}")
            print("-" * 60)
            print(f"Query: {scenario['query']}")
            print(f"Context Available: {'Yes' if scenario['context'] else 'No'}")
            print(f"Expected Routing: {', '.join(scenario['expected_routing'])}")
            print(f"Expected Type: {scenario['expected_query_type']}")
            print("\n")
            
            try:
                # Test ultra-intelligent processing
                result = await ai_service.process_query_with_ultra_intelligence(
                    query=scenario["query"],
                    context=scenario["context"],
                    session_id=f"demo_session_{i}"
                )
                
                # Analyze results
                analysis_results = self._analyze_test_results(scenario, result)
                results.append(analysis_results)
                
                # Display results
                self._display_test_results(analysis_results)
                
            except Exception as e:
                print(f"❌ Error in test {i}: {str(e)}")
                results.append({
                    "test_name": scenario["name"],
                    "status": "failed",
                    "error": str(e)
                })
            
            print("\n" + "="*80 + "\n")
        
        # Generate summary report
        self._generate_summary_report(results)
    
    def _analyze_test_results(self, scenario: dict, result: dict) -> dict:
        """Analyze test results against expectations"""
        
        ultra_metadata = result.get("ultra_intelligence_metadata", {})
        query_analysis = ultra_metadata.get("query_analysis", {})
        synthesis_info = ultra_metadata.get("information_synthesis", {})
        
        analysis = {
            "test_name": scenario["name"],
            "status": "completed",
            "query_analysis": {
                "detected_type": query_analysis.get("type"),
                "expected_type": scenario["expected_query_type"],
                "type_match": query_analysis.get("type") == scenario["expected_query_type"],
                "confidence": query_analysis.get("confidence", 0.0),
                "complexity_score": query_analysis.get("complexity_score", 0.0),
                "search_strategy": query_analysis.get("search_strategy")
            },
            "routing_analysis": {
                "sources_used": ultra_metadata.get("sources_used", []),
                "expected_sources": scenario["expected_routing"],
                "routing_accuracy": self._calculate_routing_accuracy(
                    ultra_metadata.get("sources_used", []), 
                    scenario["expected_routing"]
                )
            },
            "synthesis_quality": {
                "confidence_score": synthesis_info.get("confidence_score", 0.0),
                "sources_synthesized": synthesis_info.get("synthesis_metadata", {}).get("sources_used", 0),
                "content_available": bool(synthesis_info.get("synthesized_content", "").strip())
            },
            "response_quality": {
                "compliance_score": result.get("compliance_validation", {}).get("compliance_score", 0.0),
                "compliance_issues": result.get("compliance_validation", {}).get("issues", []),
                "response_length": len(result.get("answer", "")),
                "processing_time": result.get("processing_time_seconds", 0.0)
            },
            "conversation_features": {
                "conversation_aware": result.get("conversation_aware", False),
                "multi_source_enabled": ultra_metadata.get("multi_source_enabled", False)
            }
        }
        
        return analysis
    
    def _calculate_routing_accuracy(self, actual_sources: list, expected_sources: list) -> float:
        """Calculate routing accuracy score"""
        if not expected_sources:
            return 1.0
        
        actual_set = set(actual_sources)
        expected_set = set(expected_sources)
        
        if not actual_set and not expected_set:
            return 1.0
        
        if not actual_set or not expected_set:
            return 0.0
        
        intersection = actual_set.intersection(expected_set)
        union = actual_set.union(expected_set)
        
        return len(intersection) / len(union)
    
    def _display_test_results(self, analysis: dict):
        """Display detailed test results"""
        
        print("🧠 QUERY ANALYSIS:")
        qa = analysis["query_analysis"]
        type_status = "✅" if qa["type_match"] else "❌"
        print(f"  {type_status} Query Type: {qa['detected_type']} (expected: {qa['expected_type']})")
        print(f"  📊 Confidence: {qa['confidence']:.2f}")
        print(f"  🔄 Complexity: {qa['complexity_score']:.2f}")
        print(f"  🎯 Strategy: {qa['search_strategy']}")
        
        print("\n🔀 ROUTING ANALYSIS:")
        ra = analysis["routing_analysis"]
        routing_status = "✅" if ra["routing_accuracy"] > 0.7 else "⚠️" if ra["routing_accuracy"] > 0.3 else "❌"
        print(f"  {routing_status} Routing Accuracy: {ra['routing_accuracy']:.2f}")
        print(f"  📍 Sources Used: {', '.join(ra['sources_used']) if ra['sources_used'] else 'None'}")
        print(f"  🎯 Expected: {', '.join(ra['expected_sources'])}")
        
        print("\n🔬 SYNTHESIS QUALITY:")
        sq = analysis["synthesis_quality"]
        synthesis_status = "✅" if sq["confidence_score"] > 0.7 else "⚠️" if sq["confidence_score"] > 0.3 else "❌"
        print(f"  {synthesis_status} Synthesis Confidence: {sq['confidence_score']:.2f}")
        print(f"  📚 Sources Synthesized: {sq['sources_synthesized']}")
        print(f"  📝 Content Available: {'Yes' if sq['content_available'] else 'No'}")
        
        print("\n📋 RESPONSE QUALITY:")
        rq = analysis["response_quality"]
        compliance_status = "✅" if rq["compliance_score"] > 0.8 else "⚠️" if rq["compliance_score"] > 0.6 else "❌"
        print(f"  {compliance_status} Compliance Score: {rq['compliance_score']:.2f}")
        if rq["compliance_issues"]:
            print(f"  ⚠️  Issues: {', '.join(rq['compliance_issues'])}")
        print(f"  ⏱️  Processing Time: {rq['processing_time']:.2f}s")
        print(f"  📏 Response Length: {rq['response_length']} characters")
        
        print("\n🤖 CONVERSATION FEATURES:")
        cf = analysis["conversation_features"]
        print(f"  💬 Conversation Aware: {'✅' if cf['conversation_aware'] else '❌'}")
        print(f"  🧠 Multi-Source Enabled: {'✅' if cf['multi_source_enabled'] else '❌'}")
    
    def _generate_summary_report(self, results: list):
        """Generate comprehensive summary report"""
        
        print("📊 ULTRA-INTELLIGENCE SYSTEM SUMMARY REPORT")
        print("=" * 80)
        
        successful_tests = [r for r in results if r["status"] == "completed"]
        failed_tests = [r for r in results if r["status"] == "failed"]
        
        print(f"📈 OVERALL PERFORMANCE:")
        print(f"  ✅ Successful Tests: {len(successful_tests)}/{len(results)} ({len(successful_tests)/len(results)*100:.1f}%)")
        
        if successful_tests:
            # Calculate averages
            avg_type_accuracy = sum(1 for r in successful_tests if r["query_analysis"]["type_match"]) / len(successful_tests)
            avg_confidence = sum(r["query_analysis"]["confidence"] for r in successful_tests) / len(successful_tests)
            avg_routing_accuracy = sum(r["routing_analysis"]["routing_accuracy"] for r in successful_tests) / len(successful_tests)
            avg_synthesis_confidence = sum(r["synthesis_quality"]["confidence_score"] for r in successful_tests) / len(successful_tests)
            avg_compliance = sum(r["response_quality"]["compliance_score"] for r in successful_tests) / len(successful_tests)
            avg_processing_time = sum(r["response_quality"]["processing_time"] for r in successful_tests) / len(successful_tests)
            
            print(f"\n🎯 ACCURACY METRICS:")
            print(f"  Query Type Detection: {avg_type_accuracy:.1%}")
            print(f"  Query Analysis Confidence: {avg_confidence:.2f}")
            print(f"  Source Routing Accuracy: {avg_routing_accuracy:.2f}")
            print(f"  Information Synthesis: {avg_synthesis_confidence:.2f}")
            print(f"  Response Compliance: {avg_compliance:.2f}")
            
            print(f"\n⚡ PERFORMANCE METRICS:")
            print(f"  Average Processing Time: {avg_processing_time:.2f}s")
            
            # Multi-source capabilities
            multi_source_tests = sum(1 for r in successful_tests if r["conversation_features"]["multi_source_enabled"])
            print(f"  Multi-Source Enabled: {multi_source_tests}/{len(successful_tests)} tests")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['test_name']}: {test.get('error', 'Unknown error')}")
        
        print(f"\n📝 SYSTEM STATUS:")
        if len(successful_tests) == len(results) and avg_compliance > 0.8 and avg_routing_accuracy > 0.7:
            print("  🎉 ULTRA-INTELLIGENCE SYSTEM: FULLY OPERATIONAL")
        elif len(successful_tests) > len(results) * 0.8:
            print("  ⚠️  ULTRA-INTELLIGENCE SYSTEM: MOSTLY OPERATIONAL")
        else:
            print("  ❌ ULTRA-INTELLIGENCE SYSTEM: NEEDS ATTENTION")
        
        print(f"\nTest completed at: {datetime.utcnow().isoformat()}")

async def run_demo():
    """Run the ultra-intelligence demonstration"""
    demo = UltraIntelligenceDemo()
    await demo.run_comprehensive_demo()

if __name__ == "__main__":
    print("Starting Clair Ultra-Intelligence Demonstration...")
    asyncio.run(run_demo())