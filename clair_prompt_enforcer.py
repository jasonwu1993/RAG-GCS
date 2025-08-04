#!/usr/bin/env python3
"""
Clair System Prompt Enforcer
Ensures strict compliance with Chinese language rules, mandatory links, and hotkey displays
"""

import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from core import log_debug, track_function_entry

@dataclass
class EnforcementResult:
    """Result of system prompt enforcement"""
    needs_chinese: bool
    mandatory_links: List[str]
    required_hotkeys: List[Dict[str, str]]
    trigger_type: str
    enforcement_applied: bool

class ClairPromptEnforcer:
    """Enforces Clair's system prompt requirements with Chinese language and mandatory links"""
    
    def __init__(self):
        # Language detection patterns
        self.english_patterns = [
            r'\b(what|how|when|where|why|who|which|should|could|would|can|will|do|does|did|is|are|was|were|have|has|had)\b',
            r'\b(the|and|or|but|for|with|from|about|into|through|during|before|after)\b',
            r'\b(insurance|policy|coverage|premium|benefit|claim|quote|plan|rate|cost)\b'
        ]
        
        # Mandatory link triggers
        self.policy_generation_triggers = [
            "生成保单", "出示保单", "制作保单", "保单预算", "保单工具", "新保单", "申请保单",
            "policy quote", "generate policy", "create policy", "policy tool", "new policy"
        ]
        
        self.product_comparison_triggers = [
            "市场", "保险产品", "对比", "价值定位", "竞争", "产品比较", "市场比较",
            "market comparison", "product comparison", "competitive analysis"
        ]
        
        self.industry_report_triggers = [
            "保险市场现状", "保险行业发展趋势", "保险产品市场份额", "保险市场从业人数", 
            "保险市场规模", "行业分析", "市场分析", "行业报告", "市场报告",
            "insurance market", "industry trends", "market analysis", "industry report"
        ]
        
        # Hotkey configurations
        self.hotkey_templates = {
            "general": [
                {"key": "R", "emoji": "🎯", "text": "推荐3个保险计划"},
                {"key": "E", "emoji": "📖", "text": "解释保险方案"},
                {"key": "C", "emoji": "💰", "text": "计算我的费用"},
                {"key": "F", "emoji": "💡", "text": "财务规划建议"},
                {"key": "L", "emoji": "📋", "text": "查看所有快捷键"}
            ],
            "policy_focused": [
                {"key": "A", "emoji": "✅", "text": "继续深入了解"},
                {"key": "S", "emoji": "📄", "text": "需要提交材料"},
                {"key": "C", "emoji": "💰", "text": "费用计算"},
                {"key": "T", "emoji": "👨‍💼", "text": "联系专业顾问"},
                {"key": "L", "emoji": "📋", "text": "所有快捷键"}
            ],
            "comparison": [
                {"key": "R", "emoji": "🎯", "text": "推荐最适合方案"},
                {"key": "E", "emoji": "📊", "text": "详细解释差异"},
                {"key": "C", "emoji": "💰", "text": "费用对比"},
                {"key": "D", "emoji": "📑", "text": "分析产品文档"},
                {"key": "L", "emoji": "📋", "text": "所有快捷键"}
            ],
            "industry": [
                {"key": "Y", "emoji": "🏢", "text": "了解我们机构"},
                {"key": "I", "emoji": "📈", "text": "监管政策解读"},
                {"key": "F", "emoji": "💡", "text": "财务规划建议"},
                {"key": "N", "emoji": "📞", "text": "联系方式"},
                {"key": "L", "emoji": "📋", "text": "所有快捷键"}
            ]
        }
    
    def enforce_system_prompt(self, query: str, response: str) -> Tuple[str, EnforcementResult]:
        """Enforce all system prompt requirements"""
        track_function_entry("enforce_system_prompt")
        
        # 1. Detect user language
        is_english_query = self._detect_english(query)
        
        # 2. Detect mandatory link triggers
        trigger_type, mandatory_links = self._detect_mandatory_links(query)
        
        # 3. Determine if Chinese response is needed
        needs_chinese = not is_english_query
        
        # 4. Select appropriate hotkeys
        hotkeys = self._select_hotkeys(trigger_type, needs_chinese)
        
        # 5. Apply enforcement to response
        enforced_response = self._apply_enforcement(
            response, needs_chinese, mandatory_links, hotkeys, trigger_type
        )
        
        enforcement_result = EnforcementResult(
            needs_chinese=needs_chinese,
            mandatory_links=mandatory_links,
            required_hotkeys=hotkeys,
            trigger_type=trigger_type,
            enforcement_applied=enforced_response != response
        )
        
        log_debug("System prompt enforcement applied", {
            "is_english_query": is_english_query,
            "needs_chinese": needs_chinese,
            "trigger_type": trigger_type,
            "mandatory_links": len(mandatory_links),
            "enforcement_applied": enforcement_result.enforcement_applied
        })
        
        return enforced_response, enforcement_result
    
    def _detect_english(self, text: str) -> bool:
        """Detect if text is primarily in English"""
        # First check for Chinese characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.replace(" ", ""))
        
        if total_chars == 0:
            return False
        
        # If more than 20% Chinese characters, it's NOT English
        if chinese_chars / total_chars > 0.2:
            return False
        
        # Otherwise check for English patterns
        english_matches = 0
        total_words = len(text.split())
        
        if total_words == 0:
            return False
        
        for pattern in self.english_patterns:
            matches = len(re.findall(pattern, text.lower()))
            english_matches += matches
        
        # If more than 30% of words match English patterns, consider it English
        english_ratio = english_matches / total_words if total_words > 0 else 0
        return english_ratio > 0.3
    
    def _detect_mandatory_links(self, query: str) -> Tuple[str, List[str]]:
        """Detect mandatory link requirements based on query content"""
        query_lower = query.lower()
        mandatory_links = []
        trigger_type = "general"
        
        # Check for policy generation triggers
        if any(trigger in query_lower for trigger in self.policy_generation_triggers):
            mandatory_links.append("policy_generator")
            trigger_type = "policy_focused"
        
        # Check for product comparison triggers
        elif any(trigger in query_lower for trigger in self.product_comparison_triggers):
            mandatory_links.append("product_comparison")
            trigger_type = "comparison"
        
        # Check for industry report triggers
        elif any(trigger in query_lower for trigger in self.industry_report_triggers):
            mandatory_links.append("industry_report")
            trigger_type = "industry"
        
        return trigger_type, mandatory_links
    
    def _select_hotkeys(self, trigger_type: str, needs_chinese: bool) -> List[Dict[str, str]]:
        """Select appropriate hotkeys based on context"""
        if trigger_type in self.hotkey_templates:
            hotkeys = self.hotkey_templates[trigger_type].copy()
        else:
            hotkeys = self.hotkey_templates["general"].copy()
        
        # Convert to English if needed
        if not needs_chinese:
            hotkeys = self._translate_hotkeys_to_english(hotkeys)
        
        return hotkeys
    
    def _translate_hotkeys_to_english(self, hotkeys: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Translate hotkeys to English"""
        translation_map = {
            "推荐3个保险计划": "Recommend 3 plans",
            "解释保险方案": "Explain plans",
            "计算我的费用": "Calculate costs",
            "财务规划建议": "Financial advice",
            "查看所有快捷键": "List all hotkeys",
            "继续深入了解": "Tell me more",
            "需要提交材料": "Required documents",
            "费用计算": "Cost calculation",
            "联系专业顾问": "Talk to agent",
            "所有快捷键": "All hotkeys",
            "推荐最适合方案": "Best recommendation",
            "详细解释差异": "Explain differences",
            "费用对比": "Compare costs",
            "分析产品文档": "Analyze documents",
            "了解我们机构": "About our agency",
            "监管政策解读": "Regulatory insights",
            "联系方式": "Contact info"
        }
        
        english_hotkeys = []
        for hotkey in hotkeys:
            english_text = translation_map.get(hotkey["text"], hotkey["text"])
            english_hotkeys.append({
                "key": hotkey["key"],
                "emoji": hotkey["emoji"],
                "text": english_text
            })
        
        return english_hotkeys
    
    def _apply_enforcement(
        self, 
        response: str, 
        needs_chinese: bool, 
        mandatory_links: List[str], 
        hotkeys: List[Dict[str, str]],
        trigger_type: str
    ) -> str:
        """Apply all enforcement rules to the response"""
        
        # Start with the original AI-generated response
        enforced_response = response
        
        # 1. Apply mandatory link insertions
        if "policy_generator" in mandatory_links:
            policy_text = """我已为您准备好个性化的 IUL 保单预算工具。
👉 请点击以下链接打开预算器：
立即启动预算器 (https://iul-sim.vercel.app/)"""
            if needs_chinese:
                enforced_response = policy_text
            else:
                enforced_response = """I have prepared a personalized IUL policy budget tool for you.
👉 Please click the following link to open the calculator:
Launch Calculator (https://iul-sim.vercel.app/)"""
        
        elif "product_comparison" in mandatory_links:
            comparison_link = "\n\n📊 查看详细的产品对比分析：https://product-comp-adv-bjed.vercel.app/"
            if not needs_chinese:
                comparison_link = "\n\n📊 View detailed product comparison analysis: https://product-comp-adv-bjed.vercel.app/"
            enforced_response += comparison_link
        
        elif "industry_report" in mandatory_links:
            if needs_chinese:
                report_link = "\n\n📈 推荐阅读完整的《保险市场分析报告》：https://industry-report.vercel.app/"
            else:
                report_link = "\n\n📈 Recommended reading - Complete Insurance Market Analysis Report: https://industry-report.vercel.app/"
            enforced_response += report_link
        
        # 2. Skip adding hotkeys here - GPT generates contextual ones from system prompt
        # hotkey_section = self._format_hotkeys(hotkeys, needs_chinese)
        # enforced_response += "\n\n" + hotkey_section
        
        # 3. Apply Chinese language enforcement if needed
        if needs_chinese and not self._is_chinese_response(enforced_response):
            enforced_response = self._add_chinese_language_instruction(enforced_response)
        
        return enforced_response
    
    def _format_hotkeys(self, hotkeys: List[Dict[str, str]], needs_chinese: bool) -> str:
        """Format hotkeys display"""
        if needs_chinese:
            header = "💡 快捷建议（可选）："
        else:
            header = "💡 Quick Suggestions (Optional):"
        
        hotkey_lines = []
        for hotkey in hotkeys:
            line = f"**{hotkey['key']}**: {hotkey['emoji']} {hotkey['text']}"
            hotkey_lines.append(line)
        
        return header + "\n" + "\n".join(hotkey_lines)
    
    def _is_chinese_response(self, response: str) -> bool:
        """Check if response contains significant Chinese content"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', response))
        total_chars = len(response)
        
        if total_chars == 0:
            return False
        
        return chinese_chars / total_chars > 0.3
    
    def _add_chinese_language_instruction(self, response: str) -> str:
        """Add instruction to generate Chinese response"""
        instruction = "\n\n[系统提示：请用中文回答客户问题]"
        return response + instruction

# Global enforcer instance
clair_prompt_enforcer = ClairPromptEnforcer()