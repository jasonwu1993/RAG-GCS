# Enhanced RAG Clair System Configuration
# SOTA Life Insurance Domain Configuration

import os
from typing import Dict, List, Any

# Environment Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION", "us-central1")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
INDEX_ENDPOINT_ID = os.getenv("INDEX_ENDPOINT_ID")
DEPLOYED_INDEX_ID = os.getenv("DEPLOYED_INDEX_ID")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service-account.json")

# API Configuration
EMBED_MODEL = "text-embedding-3-small"
SIMILARITY_THRESHOLD = 0.75
TOP_K = 3
GPT_MODEL = "gpt-4o"
MAX_TOKENS = 1000
TEMPERATURE = 0.3

# Enhanced Life Insurance Domain Configuration
ENHANCED_INSURANCE_CONFIG = {
    "PRODUCT_TYPES": {
        "term_life": {
            "names": ["term life", "term insurance", "level term", "decreasing term", "renewable term"],
            "features": ["temporary coverage", "lower premiums", "convertible options", "level premiums"],
            "keywords": ["term", "temporary", "convert", "renew", "level", "decreasing"]
        },
        "whole_life": {
            "names": ["whole life", "permanent life", "ordinary life", "straight life"],
            "features": ["lifetime coverage", "cash value", "dividends", "premium stability"],
            "keywords": ["whole", "permanent", "cash value", "dividend", "ordinary", "straight"]
        },
        "universal_life": {
            "names": ["universal life", "flexible premium", "UL insurance"],
            "features": ["flexible premiums", "adjustable death benefit", "cash accumulation", "investment options"],
            "keywords": ["universal", "flexible", "adjustable", "investment", "accumulation"]
        },
        "variable_life": {
            "names": ["variable life", "variable universal", "VUL", "investment life"],
            "features": ["investment control", "market-linked returns", "variable death benefit", "separate accounts"],
            "keywords": ["variable", "investment", "market", "separate account", "VUL"]
        },
        "indexed_universal": {
            "names": ["indexed universal", "IUL", "equity indexed", "market indexed"],
            "features": ["market participation", "downside protection", "flexible premiums", "tax advantages"],
            "keywords": ["indexed", "IUL", "equity", "market participation", "downside protection"]
        }
    },
    
    "ADVANCED_INTENTS": {
        "product_comparison": {
            "patterns": [
                "compare.*life insurance",
                "difference between.*term.*whole",
                "which.*better.*universal.*variable",
                "term vs whole life",
                "should I choose.*IUL.*VUL"
            ],
            "response_strategy": "comparative_analysis",
            "required_context": ["product_features", "cost_analysis", "suitability_factors"]
        },
        "premium_inquiry": {
            "patterns": [
                "how much.*cost",
                "premium.*calculation",
                "price.*life insurance",
                "monthly payment",
                "annual premium"
            ],
            "response_strategy": "cost_analysis",
            "required_context": ["pricing_factors", "underwriting_criteria", "discounts"]
        },
        "coverage_amount": {
            "patterns": [
                "how much coverage",
                "death benefit.*amount",
                "insurance need.*analysis",
                "calculate.*coverage",
                "sufficient.*protection"
            ],
            "response_strategy": "needs_analysis",
            "required_context": ["income_replacement", "debt_coverage", "final_expenses"]
        },
        "beneficiary_questions": {
            "patterns": [
                "beneficiary.*designation",
                "who.*receive.*proceeds",
                "change.*beneficiary",
                "primary.*contingent",
                "revocable.*irrevocable"
            ],
            "response_strategy": "beneficiary_guidance",
            "required_context": ["designation_options", "legal_implications", "tax_considerations"]
        },
        "policy_management": {
            "patterns": [
                "loan.*against.*policy",
                "cash value.*withdrawal",
                "surrender.*policy",
                "lapse.*protection",
                "premium.*payment.*options"
            ],
            "response_strategy": "policy_administration",
            "required_context": ["policy_features", "loan_provisions", "surrender_charges"]
        },
        "tax_implications": {
            "patterns": [
                "tax.*benefits",
                "death benefit.*taxable",
                "cash value.*tax",
                "estate.*tax",
                "1035.*exchange"
            ],
            "response_strategy": "tax_analysis",
            "required_context": ["tax_advantages", "estate_planning", "regulatory_compliance"]
        },
        "underwriting_health": {
            "patterns": [
                "medical.*exam",
                "health.*questions",
                "underwriting.*process",
                "pre-existing.*condition",
                "life expectancy"
            ],
            "response_strategy": "underwriting_guidance",
            "required_context": ["medical_requirements", "risk_assessment", "approval_process"]
        },
        "riders_addons": {
            "patterns": [
                "rider.*options",
                "additional.*benefits",
                "disability.*waiver",
                "accidental.*death",
                "long.*term.*care"
            ],
            "response_strategy": "rider_explanation",
            "required_context": ["available_riders", "costs", "benefit_triggers"]
        }
    },
    
    "DOCUMENT_CLASSIFICATION": {
        "policy_documents": {
            "indicators": ["policy", "contract", "terms", "conditions", "schedule"],
            "priority": 1.0,
            "search_boost": 2.0
        },
        "product_brochures": {
            "indicators": ["brochure", "overview", "summary", "features", "benefits"],
            "priority": 0.9,
            "search_boost": 1.5
        },
        "underwriting_guides": {
            "indicators": ["underwriting", "medical", "health", "application", "requirements"],
            "priority": 0.8,
            "search_boost": 1.3
        },
        "rate_schedules": {
            "indicators": ["rates", "premium", "pricing", "cost", "schedule"],
            "priority": 0.7,
            "search_boost": 1.2
        },
        "regulatory_documents": {
            "indicators": ["regulation", "compliance", "legal", "disclosure", "filing"],
            "priority": 0.6,
            "search_boost": 1.1
        }
    },
    
    "ENTITY_RECOGNITION": {
        "age_patterns": [
            r"\b(\d{1,2})\s*years?\s*old\b",
            r"\bage\s*(\d{1,2})\b",
            r"\b(\d{1,2})\s*year\s*old\b"
        ],
        "amount_patterns": [
            r"\$([0-9,]+(?:\.[0-9]{2})?)",
            r"([0-9,]+)\s*dollars?",
            r"coverage.*?([0-9,]+)"
        ],
        "health_conditions": [
            "diabetes", "heart disease", "cancer", "hypertension", "obesity",
            "smoking", "high cholesterol", "mental health", "substance abuse"
        ],
        "family_roles": [
            "spouse", "children", "dependents", "beneficiaries", "estate",
            "husband", "wife", "son", "daughter", "parent"
        ]
    },
    
    "RESPONSE_TEMPLATES": {
        "product_comparison": """
Based on your inquiry about {products}, here's a comprehensive comparison:

**Key Differences:**
{comparison_points}

**Suitability Factors:**
- {suitability_factor_1}
- {suitability_factor_2}
- {suitability_factor_3}

**Recommendation:**
{recommendation}

*Please consult with a licensed insurance professional for personalized advice.*
        """,
        
        "coverage_analysis": """
**Coverage Analysis for Your Situation:**

**Estimated Need:** ${coverage_amount:,}

**Calculation Factors:**
- Income Replacement: ${income_replacement:,}
- Debt Coverage: ${debt_coverage:,}
- Final Expenses: ${final_expenses:,}
- Education Fund: ${education_fund:,}

**Recommendation:**
{recommendation}

*This is a general estimate. Consult with a financial advisor for detailed planning.*
        """,
        
        "premium_estimate": """
**Premium Estimate Overview:**

**Factors Affecting Your Premium:**
- Age: {age}
- Health Class: {health_class}
- Coverage Amount: ${coverage_amount:,}
- Product Type: {product_type}

**Estimated Range:** ${premium_low:,} - ${premium_high:,} annually

**Ways to Reduce Premiums:**
{cost_reduction_tips}

*Actual premiums depend on underwriting. This is an estimate only.*
        """
    },
    
    "QUERY_ROUTING": {
        "high_priority": {
            "keywords": ["urgent", "immediate", "emergency", "critical", "important"],
            "boost_factor": 2.0
        },
        "product_specific": {
            "keywords": ["term", "whole", "universal", "variable", "indexed"],
            "boost_factor": 1.5
        },
        "financial_planning": {
            "keywords": ["estate", "tax", "retirement", "investment", "planning"],
            "boost_factor": 1.3
        }
    }
}

# Clair's comprehensive system prompt from Clair-sys-prompt.txt
CLAIR_SYSTEM_PROMPT = """You are Clair, an expert AI financial advisor (AI财富专家) specializing in life insurance and financial planning. Your role is to provide accurate, helpful, and personalized advice based on official policy documents and financial regulations.

## Core Expertise Areas:
- Life Insurance Products (Term, Whole, Universal, Variable, Indexed Universal)
- Premium Calculations and Cost Analysis
- Coverage Needs Assessment and Financial Planning
- Underwriting Requirements and Health Assessments
- Policy Management and Administration
- Tax Implications and Estate Planning
- Beneficiary Designations and Legal Considerations
- Insurance Riders and Additional Benefits

## Response Guidelines:
1. **Accuracy First**: Base all advice on the provided document context and official policy information
2. **Clear Communication**: Explain complex insurance concepts in understandable terms
3. **Personalization**: Consider the user's specific situation, age, family status, and financial goals
4. **Compliance**: Always mention that specific details should be verified with actual policy documents
5. **Professional Disclaimer**: Recommend consultation with licensed insurance professionals for final decisions

## When Context is Available:
- Reference specific policy provisions and terms
- Quote exact premium rates and coverage amounts when available
- Cite relevant document sections and page numbers
- Provide detailed explanations based on official documentation

## When Context is Limited:
- Provide general industry knowledge and best practices
- Explain common insurance principles and concepts
- Offer framework for decision-making
- Always note that specific details need verification with actual policy documents

## Specialized Knowledge:
- Life insurance product comparisons and suitability analysis
- Premium factors: age, health, coverage amount, policy type
- Underwriting process: medical exams, health questionnaires, financial requirements
- Tax advantages: death benefits, cash value growth, 1035 exchanges
- Estate planning: beneficiary strategies, trust considerations, tax implications
- Policy optimization: loan options, surrender values, conversion privileges

Remember: You are here to educate, guide, and provide expert analysis while maintaining professional standards and regulatory compliance. Always prioritize the client's best interests and long-term financial security."""

# Greeting message for Clair
CLAIR_GREETING = "Hello, I'm Clair, your trusted and always-on AI financial advisor in wealth planning. How may I assist you today?"

# System prompts for different query types (all use Clair's core prompt as base)
SYSTEM_PROMPTS = {
    "general": CLAIR_SYSTEM_PROMPT,
    "product_comparison": CLAIR_SYSTEM_PROMPT,
    "needs_analysis": CLAIR_SYSTEM_PROMPT,
    "underwriting": CLAIR_SYSTEM_PROMPT,
    "comparative_analysis": CLAIR_SYSTEM_PROMPT,
    "cost_analysis": CLAIR_SYSTEM_PROMPT,
    "beneficiary_guidance": CLAIR_SYSTEM_PROMPT,
    "policy_administration": CLAIR_SYSTEM_PROMPT,
    "tax_analysis": CLAIR_SYSTEM_PROMPT,
    "underwriting_guidance": CLAIR_SYSTEM_PROMPT,
    "rider_explanation": CLAIR_SYSTEM_PROMPT
}

# Search configuration
SEARCH_CONFIG = {
    "semantic_weight": 0.7,
    "keyword_weight": 0.3,
    "recency_boost": 0.1,
    "document_type_boost": 0.2
}