#!/usr/bin/env python3
"""
Hotkey Handler for Clair
Provides specific responses for hotkey shortcuts (R, E, C, F, L)
"""

from typing import Dict, Optional
from core import log_debug, track_function_entry

class HotkeyHandler:
    """Handles hotkey shortcuts with specific responses"""
    
    def __init__(self):
        self.hotkey_responses = {
            "R": {
                "chinese": """🎯 **推荐3个保险计划**

基于市场上的主流产品，我为您推荐以下三种保险计划：

**1. 全能保障计划**
- 适合：30-45岁家庭支柱
- 特点：高保额人寿 + 重疾 + 意外
- 优势：全面保障，保费合理

**2. 财富传承计划** 
- 适合：高净值人士
- 特点：分红型终身寿险
- 优势：保障 + 投资，财富传承

**3. 基础保障计划**
- 适合：年轻人或预算有限
- 特点：定期寿险 + 医疗险
- 优势：保费低廉，基础保障

为了给您更精准的推荐，请告诉我您的年龄和家庭情况。""",
                
                "english": """🎯 **Recommend 3 Insurance Plans**

Based on mainstream market products, I recommend these three insurance plans:

**1. Comprehensive Protection Plan**
- Suitable for: 30-45 year old family breadwinners
- Features: High life coverage + critical illness + accident
- Benefits: Complete protection, reasonable premiums

**2. Wealth Legacy Plan**
- Suitable for: High net worth individuals  
- Features: Dividend whole life insurance
- Benefits: Protection + investment, wealth transfer

**3. Basic Protection Plan**
- Suitable for: Young people or limited budget
- Features: Term life + medical insurance
- Benefits: Low premiums, basic coverage

For more precise recommendations, please tell me your age and family situation."""
            },
            
            "E": {
                "chinese": """📖 **保险方案详细解释**

让我为您详细解释不同类型的保险方案：

**人寿保险类型：**
- **定期寿险**：固定期限，保费低，适合年轻人
- **终身寿险**：终身保障，有现金价值，适合财富传承
- **万能险**：保障+投资，灵活性高

**保障范围：**
- **身故保障**：意外或疾病身故赔付
- **重疾保障**：重大疾病提前给付
- **医疗保障**：住院医疗费用报销

**选择要点：**
1. 根据家庭责任确定保额
2. 根据预算选择保险类型
3. 考虑未来需求变化

需要我详细解释某个特定方案吗？""",
                
                "english": """📖 **Detailed Insurance Plan Explanation**

Let me explain different types of insurance plans in detail:

**Life Insurance Types:**
- **Term Life**: Fixed period, low premiums, suitable for young people
- **Whole Life**: Lifetime coverage, cash value, suitable for wealth transfer
- **Universal Life**: Protection + investment, high flexibility

**Coverage Scope:**
- **Death Benefit**: Payout for accidental or illness death
- **Critical Illness**: Advance payment for major diseases
- **Medical Coverage**: Hospitalization expense reimbursement

**Selection Points:**
1. Determine coverage amount based on family responsibilities
2. Choose insurance type based on budget
3. Consider future needs changes

Would you like me to explain any specific plan in detail?"""
            },
            
            "C": {
                "chinese": """💰 **费用计算说明**

保险费用计算涉及多个因素：

**主要影响因素：**
- **年龄**：年龄越大，保费越高
- **性别**：男性通常费率略高
- **健康状况**：影响核保结果
- **保额**：保额越高，保费越高
- **保险期间**：终身比定期费用高

**费用预估示例：**
- 30岁男性，100万保额定期寿险：约500-800元/年
- 30岁女性，50万重疾险：约3000-5000元/年
- 35岁男性，200万终身寿险：约8000-15000元/年

**准确报价需要：**
1. 详细个人信息
2. 健康状况评估
3. 具体产品选择

我已为您准备好个性化的 IUL 保单预算工具。
👉 请点击以下链接打开预算器：
立即启动预算器 (https://iul-sim.vercel.app/)""",
                
                "english": """💰 **Cost Calculation Explanation**

Insurance cost calculation involves multiple factors:

**Main Influencing Factors:**
- **Age**: Higher age, higher premiums
- **Gender**: Males typically have slightly higher rates
- **Health Status**: Affects underwriting results
- **Coverage Amount**: Higher coverage, higher premiums
- **Insurance Period**: Whole life costs more than term

**Cost Estimation Examples:**
- 30-year-old male, $1M term life: ~$500-800/year
- 30-year-old female, $500K critical illness: ~$3000-5000/year
- 35-year-old male, $2M whole life: ~$8000-15000/year

**Accurate Quote Requires:**
1. Detailed personal information
2. Health status assessment
3. Specific product selection

I have prepared a personalized IUL policy budget tool for you.
👉 Please click the following link to open the calculator:
Launch Calculator (https://iul-sim.vercel.app/)"""
            },
            
            "F": {
                "chinese": """💡 **财务规划建议**

保险在财务规划中的重要作用：

**1. 风险管理**
- 转移人身风险
- 保护家庭财务安全
- 避免因意外导致财务危机

**2. 资产保护**
- 债务隔离功能
- 法律保护资产
- 确保财富传承

**3. 税务优化**
- 保险理赔免税
- 减少遗产税负担
- 优化税务结构

**4. 现金流管理**
- 提供紧急资金
- 补充养老收入
- 子女教育储备

**建议配置比例：**
- 年收入的10-15%用于保险
- 保额为年收入的5-10倍
- 重疾险覆盖3-5年支出

需要制定详细的财务规划方案吗？""",
                
                "english": """💡 **Financial Planning Advice**

Important role of insurance in financial planning:

**1. Risk Management**
- Transfer personal risks
- Protect family financial security
- Avoid financial crisis due to accidents

**2. Asset Protection**
- Debt isolation function
- Legal asset protection
- Ensure wealth transfer

**3. Tax Optimization**
- Insurance claims are tax-free
- Reduce estate tax burden
- Optimize tax structure

**4. Cash Flow Management**
- Provide emergency funds
- Supplement retirement income
- Children's education reserves

**Recommended Allocation:**
- 10-15% of annual income for insurance
- Coverage 5-10 times annual income
- Critical illness covers 3-5 years expenses

Would you like to develop a detailed financial planning strategy?"""
            },
            
            "L": {
                "chinese": """📋 **所有快捷键**

以下是所有可用的快捷建议：

**保险规划类：**
- **R**: 🎯 推荐3个保险计划
- **E**: 📖 解释保险方案
- **C**: 💰 计算我的费用

**财务服务类：**
- **F**: 💡 财务规划建议
- **P**: 📋 查看产品对比
- **M**: 📊 市场分析报告

**客户服务类：**
- **A**: 📞 联系专业顾问
- **Q**: ❓ 常见问题解答
- **H**: 🏥 健康告知指导

**工具与链接：**
- **T**: 🧮 保单预算工具
- **D**: 📑 产品详细资料
- **S**: 📄 申请材料清单

直接输入字母即可快速获取相应服务！""",
                
                "english": """📋 **All Hotkeys**

Here are all available quick suggestions:

**Insurance Planning:**
- **R**: 🎯 Recommend 3 plans
- **E**: 📖 Explain plans
- **C**: 💰 Calculate costs

**Financial Services:**
- **F**: 💡 Financial advice
- **P**: 📋 Product comparison
- **M**: 📊 Market analysis

**Customer Service:**
- **A**: 📞 Contact agent
- **Q**: ❓ FAQ
- **H**: 🏥 Health disclosure

**Tools & Links:**
- **T**: 🧮 Policy calculator
- **D**: 📑 Product details
- **S**: 📄 Application materials

Simply type the letter to get the corresponding service!"""
            }
        }
    
    def is_hotkey(self, query: str) -> bool:
        """Check if query is a single-letter hotkey"""
        return query.strip().upper() in self.hotkey_responses
    
    def get_hotkey_response(self, query: str, needs_chinese: bool = True) -> Optional[str]:
        """Get specific response for hotkey"""
        track_function_entry("get_hotkey_response")
        
        hotkey = query.strip().upper()
        if hotkey not in self.hotkey_responses:
            return None
        
        language = "chinese" if needs_chinese else "english"
        response = self.hotkey_responses[hotkey][language]
        
        log_debug("Hotkey response generated", {
            "hotkey": hotkey,
            "language": language,
            "response_length": len(response)
        })
        
        return response

# Global hotkey handler instance
hotkey_handler = HotkeyHandler()