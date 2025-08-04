#!/usr/bin/env python3
"""
Comprehensive Test Suite for Clair System Prompt Compliance
Tests Chinese language enforcement, mandatory links, hotkeys, and trigger detection
"""

import asyncio
import json
from datetime import datetime
from ai_service import ai_service
from clair_prompt_enforcer import clair_prompt_enforcer

class ClairSystemPromptTester:
    """Test suite for validating Clair's system prompt compliance"""
    
    def __init__(self):
        self.test_scenarios = [
            {
                "name": "Chinese Language Enforcement - Chinese Query",
                "query": "什么是保险？",
                "expected": {
                    "language": "chinese",
                    "hotkeys": True,
                    "trigger_type": "general"
                }
            },
            {
                "name": "English Language Detection - English Query", 
                "query": "What is insurance?",
                "expected": {
                    "language": "english",
                    "hotkeys": True,
                    "trigger_type": "general"
                }
            },
            {
                "name": "Policy Generation Trigger - Chinese",
                "query": "请为我生成一个保单",
                "expected": {
                    "language": "chinese",
                    "mandatory_links": ["policy_generator"],
                    "hotkeys": True,
                    "trigger_type": "policy_focused",
                    "specific_response": True
                }
            },
            {
                "name": "Policy Generation Trigger - English",
                "query": "Generate a policy quote for me",
                "expected": {
                    "language": "english", 
                    "mandatory_links": ["policy_generator"],
                    "hotkeys": True,
                    "trigger_type": "policy_focused",
                    "specific_response": True
                }
            },
            {
                "name": "Product Comparison Trigger",
                "query": "市场上保险产品的对比分析",
                "expected": {
                    "language": "chinese",
                    "mandatory_links": ["product_comparison"],
                    "hotkeys": True,
                    "trigger_type": "comparison"
                }
            },
            {
                "name": "Industry Report Trigger - Market Status",
                "query": "保险市场现状如何？",
                "expected": {
                    "language": "chinese",
                    "mandatory_links": ["industry_report"],
                    "hotkeys": True,
                    "trigger_type": "industry"
                }
            },
            {
                "name": "Industry Report Trigger - Development Trends",
                "query": "保险行业发展趋势？",
                "expected": {
                    "language": "chinese",
                    "mandatory_links": ["industry_report"],
                    "hotkeys": True,
                    "trigger_type": "industry"
                }
            },
            {
                "name": "Industry Report Trigger - Market Size",
                "query": "保险市场规模？",
                "expected": {
                    "language": "chinese",
                    "mandatory_links": ["industry_report"],
                    "hotkeys": True,
                    "trigger_type": "industry"
                }
            }
        ]
    
    async def run_comprehensive_test(self):
        """Run comprehensive system prompt compliance test"""
        
        print("🧪 CLAIR SYSTEM PROMPT COMPLIANCE TEST")
        print("=" * 80)
        print("Testing Chinese language enforcement, mandatory links, and hotkeys")
        print(f"Test started at: {datetime.utcnow().isoformat()}")
        print("\n")
        
        results = []
        
        for i, scenario in enumerate(self.test_scenarios, 1):
            print(f"📋 TEST {i}: {scenario['name']}")
            print("-" * 60)
            print(f"Query: {scenario['query']}")
            print(f"Expected Language: {scenario['expected']['language']}")
            print(f"Expected Trigger: {scenario['expected']['trigger_type']}")
            print("\n")
            
            try:
                # Test enforcement directly
                enforcement_result = await self._test_enforcement_directly(scenario)
                
                # Test full AI service
                ai_result = await self._test_full_ai_service(scenario)
                
                # Analyze results
                test_result = self._analyze_test_result(scenario, enforcement_result, ai_result)
                results.append(test_result)
                
                # Display results
                self._display_test_result(test_result)
                
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
    
    async def _test_enforcement_directly(self, scenario):
        """Test the enforcer directly"""
        mock_response = "This is a mock response for testing."
        
        enforced_response, enforcement_result = clair_prompt_enforcer.enforce_system_prompt(
            scenario["query"], mock_response
        )
        
        return {
            "original_response": mock_response,
            "enforced_response": enforced_response,
            "enforcement_result": enforcement_result
        }
    
    async def _test_full_ai_service(self, scenario):
        """Test the full AI service"""
        result = await ai_service.process_query_with_ultra_intelligence(
            query=scenario["query"],
            context="",
            session_id=f"test_session_{hash(scenario['query'])}"
        )
        
        return result
    
    def _analyze_test_result(self, scenario, enforcement_result, ai_result):
        """Analyze test results against expectations"""
        
        expected = scenario["expected"]
        enforcement = enforcement_result["enforcement_result"]
        ai_enforcement = ai_result.get("clair_enforcement", {})
        
        analysis = {
            "test_name": scenario["name"],
            "status": "completed",
            "query": scenario["query"],
            "expectations": expected,
            
            # Language enforcement analysis
            "language_analysis": {
                "expected_language": expected["language"],
                "needs_chinese_detected": enforcement.needs_chinese,
                "language_correct": (
                    (expected["language"] == "chinese" and enforcement.needs_chinese) or
                    (expected["language"] == "english" and not enforcement.needs_chinese)
                )
            },
            
            # Trigger detection analysis
            "trigger_analysis": {
                "expected_trigger": expected["trigger_type"],
                "detected_trigger": enforcement.trigger_type,
                "trigger_correct": enforcement.trigger_type == expected["trigger_type"]
            },
            
            # Mandatory links analysis
            "link_analysis": {
                "expected_links": expected.get("mandatory_links", []),
                "detected_links": enforcement.mandatory_links,
                "links_correct": set(enforcement.mandatory_links) == set(expected.get("mandatory_links", []))
            },
            
            # Hotkeys analysis
            "hotkey_analysis": {
                "expected_hotkeys": expected.get("hotkeys", False),
                "hotkeys_present": len(enforcement.required_hotkeys) > 0,
                "hotkeys_correct": len(enforcement.required_hotkeys) == 5,
                "l_key_present": any(h.get("key") == "L" for h in enforcement.required_hotkeys)
            },
            
            # Response content analysis
            "response_analysis": {
                "enforcement_applied": enforcement.enforcement_applied,
                "ai_enforcement_applied": ai_enforcement.get("enforcement_applied", False),
                "specific_response_expected": expected.get("specific_response", False),
                "has_policy_tool_link": "iul-sim.vercel.app" in ai_result["answer"],
                "has_comparison_link": "product-comp-adv-bjed.vercel.app" in ai_result["answer"],
                "has_industry_report_link": "industry-report.vercel.app" in ai_result["answer"]
            },
            
            # Overall compliance
            "compliance_score": 0.0
        }
        
        # Calculate compliance score
        score = 0.0
        total_checks = 0
        
        # Language compliance (25%)
        if analysis["language_analysis"]["language_correct"]:
            score += 0.25
        total_checks += 1
        
        # Trigger detection (20%)
        if analysis["trigger_analysis"]["trigger_correct"]:
            score += 0.20
        total_checks += 1
        
        # Mandatory links (25%)
        if analysis["link_analysis"]["links_correct"]:
            score += 0.25
        total_checks += 1
        
        # Hotkeys (20%)
        if analysis["hotkey_analysis"]["hotkeys_correct"] and analysis["hotkey_analysis"]["l_key_present"]:
            score += 0.20
        total_checks += 1
        
        # Enforcement application (10%)
        if analysis["response_analysis"]["ai_enforcement_applied"]:
            score += 0.10
        total_checks += 1
        
        analysis["compliance_score"] = score
        
        return analysis
    
    def _display_test_result(self, analysis):
        """Display detailed test results"""
        
        print("🔍 ANALYSIS RESULTS:")
        
        # Language analysis
        lang = analysis["language_analysis"]
        lang_status = "✅" if lang["language_correct"] else "❌"
        print(f"  {lang_status} Language Detection: Expected {lang['expected_language']}, Chinese needed: {lang['needs_chinese_detected']}")
        
        # Trigger analysis
        trigger = analysis["trigger_analysis"]
        trigger_status = "✅" if trigger["trigger_correct"] else "❌"
        print(f"  {trigger_status} Trigger Detection: Expected {trigger['expected_trigger']}, Got {trigger['detected_trigger']}")
        
        # Link analysis
        links = analysis["link_analysis"]
        link_status = "✅" if links["links_correct"] else "❌"
        print(f"  {link_status} Mandatory Links: Expected {links['expected_links']}, Got {links['detected_links']}")
        
        # Hotkey analysis
        hotkeys = analysis["hotkey_analysis"]
        hotkey_status = "✅" if hotkeys["hotkeys_correct"] and hotkeys["l_key_present"] else "❌"
        print(f"  {hotkey_status} Hotkeys: Present {hotkeys['hotkeys_present']}, Count {len(analysis['trigger_analysis'])}, L-key {hotkeys['l_key_present']}")
        
        # Response analysis
        response = analysis["response_analysis"]
        print(f"  🔧 Enforcement Applied: Direct {response['enforcement_applied']}, AI Service {response['ai_enforcement_applied']}")
        
        # Specific link checks
        if response["has_policy_tool_link"]:
            print("  🔗 Policy Tool Link: ✅ Present")
        if response["has_comparison_link"]:
            print("  🔗 Comparison Link: ✅ Present")
        if response["has_industry_report_link"]:  
            print("  🔗 Industry Report Link: ✅ Present")
        
        # Overall score
        score = analysis["compliance_score"]
        score_status = "🎉" if score >= 0.9 else "✅" if score >= 0.8 else "⚠️" if score >= 0.6 else "❌"
        print(f"\n  {score_status} COMPLIANCE SCORE: {score:.1%}")
    
    def _generate_summary_report(self, results):
        """Generate comprehensive summary report"""
        
        print("📊 SYSTEM PROMPT COMPLIANCE SUMMARY")
        print("=" * 80)
        
        successful_tests = [r for r in results if r["status"] == "completed"]
        failed_tests = [r for r in results if r["status"] == "failed"]
        
        print(f"📈 OVERALL PERFORMANCE:")
        print(f"  ✅ Successful Tests: {len(successful_tests)}/{len(results)} ({len(successful_tests)/len(results)*100:.1f}%)")
        
        if successful_tests:
            # Calculate averages
            avg_compliance = sum(r["compliance_score"] for r in successful_tests) / len(successful_tests)
            
            language_correct = sum(1 for r in successful_tests if r["language_analysis"]["language_correct"])
            trigger_correct = sum(1 for r in successful_tests if r["trigger_analysis"]["trigger_correct"])
            links_correct = sum(1 for r in successful_tests if r["link_analysis"]["links_correct"])
            hotkeys_correct = sum(1 for r in successful_tests if r["hotkey_analysis"]["hotkeys_correct"])
            
            print(f"\n🎯 COMPLIANCE METRICS:")
            print(f"  Language Enforcement: {language_correct}/{len(successful_tests)} ({language_correct/len(successful_tests)*100:.1f}%)")
            print(f"  Trigger Detection: {trigger_correct}/{len(successful_tests)} ({trigger_correct/len(successful_tests)*100:.1f}%)")
            print(f"  Mandatory Links: {links_correct}/{len(successful_tests)} ({links_correct/len(successful_tests)*100:.1f}%)")
            print(f"  Hotkey Display: {hotkeys_correct}/{len(successful_tests)} ({hotkeys_correct/len(successful_tests)*100:.1f}%)")
            print(f"  Average Compliance: {avg_compliance:.1%}")
            
            # Test specific scenarios
            policy_tests = [r for r in successful_tests if "policy" in r["test_name"].lower()]
            comparison_tests = [r for r in successful_tests if "comparison" in r["test_name"].lower()]
            industry_tests = [r for r in successful_tests if "industry" in r["test_name"].lower()]
            
            print(f"\n🔍 SCENARIO ANALYSIS:")
            if policy_tests:
                avg_policy_compliance = sum(r["compliance_score"] for r in policy_tests) / len(policy_tests)
                print(f"  Policy Generation: {avg_policy_compliance:.1%} compliance")
            
            if comparison_tests:
                avg_comparison_compliance = sum(r["compliance_score"] for r in comparison_tests) / len(comparison_tests)
                print(f"  Product Comparison: {avg_comparison_compliance:.1%} compliance")
            
            if industry_tests:
                avg_industry_compliance = sum(r["compliance_score"] for r in industry_tests) / len(industry_tests)
                print(f"  Industry Reports: {avg_industry_compliance:.1%} compliance")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['test_name']}: {test.get('error', 'Unknown error')}")
        
        print(f"\n📝 SYSTEM STATUS:")
        if len(successful_tests) == len(results) and avg_compliance >= 0.9:
            print("  🎉 CLAIR SYSTEM PROMPT: FULLY COMPLIANT")
        elif len(successful_tests) >= len(results) * 0.8 and avg_compliance >= 0.8:
            print("  ✅ CLAIR SYSTEM PROMPT: MOSTLY COMPLIANT")
        else:
            print("  ⚠️ CLAIR SYSTEM PROMPT: NEEDS IMPROVEMENT")
        
        print(f"\nTest completed at: {datetime.utcnow().isoformat()}")

async def run_test():
    """Run the system prompt compliance test"""
    tester = ClairSystemPromptTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    print("Starting Clair System Prompt Compliance Test...")
    asyncio.run(run_test())