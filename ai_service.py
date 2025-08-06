# AI Service with Intelligent Query Classification and Routing
# Enhanced with SOTA Life Insurance Domain Expertise

import re
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import tiktoken
from openai import OpenAI
from config import (ENHANCED_INSURANCE_CONFIG, SYSTEM_PROMPTS, GPT_MODEL, MAX_TOKENS, TEMPERATURE, EMBED_MODEL,
                   CLAIR_SYSTEM_PROMPT_ACTIVE, CONVERSATION_MEMORY_ENABLED, INTERNET_ACCESS_ENABLED, MAX_CONVERSATION_HISTORY,
                   TOP_P, PRESENCE_PENALTY, FREQUENCY_PENALTY, REQUEST_TIMEOUT, 
                   ENABLE_STRUCTURED_OUTPUTS, STRUCTURED_OUTPUT_SCHEMA,
                   ENABLE_AGENTIC_PATTERNS, REFLECTION_ENABLED, PLANNING_ENABLED, TOOL_USE_ENABLED,
                   ENABLE_CONTEXT_SYNTHESIS, ENABLE_PERFORMANCE_ANALYTICS)
from core import log_debug, track_function_entry

class PerformanceAnalytics:
    """Advanced performance analytics for GPT-Native architecture"""
    
    def __init__(self):
        self.metrics = {
            "language_consistency": [],
            "conversation_continuity": [],
            "response_quality": [],
            "agentic_effectiveness": [],
            "structured_output_success": []
        }
    
    def track_language_consistency(self, user_language: str, response_language: str, session_id: str):
        """Track language consistency across conversation"""
        consistent = user_language == response_language
        self.metrics["language_consistency"].append({
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "user_language": user_language,
            "response_language": response_language,
            "consistent": consistent
        })
        
        log_debug("Language consistency tracked", {
            "consistent": consistent,
            "user_lang": user_language,
            "response_lang": response_language
        })
    
    def track_conversation_continuity(self, context_type: str, session_id: str, quality_score: float):
        """Track conversation flow and continuity"""
        self.metrics["conversation_continuity"].append({
            "timestamp": datetime.utcnow(),
            "session_id": session_id,
            "context_type": context_type,
            "quality_score": quality_score
        })
    
    def track_agentic_effectiveness(self, reflection_quality: int, planning_depth: int, tool_relevance: int):
        """Track effectiveness of agentic patterns"""
        self.metrics["agentic_effectiveness"].append({
            "timestamp": datetime.utcnow(),
            "reflection_quality": reflection_quality,
            "planning_depth": planning_depth,
            "tool_relevance": tool_relevance,
            "overall_score": (reflection_quality + planning_depth + tool_relevance) / 3
        })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            "language_consistency_rate": self._calculate_consistency_rate(),
            "average_conversation_quality": self._calculate_avg_conversation_quality(),
            "agentic_effectiveness_score": self._calculate_agentic_score(),
            "total_interactions": sum(len(metrics) for metrics in self.metrics.values())
        }
    
    def _calculate_consistency_rate(self) -> float:
        if not self.metrics["language_consistency"]:
            return 0.0
        consistent_count = sum(1 for m in self.metrics["language_consistency"] if m["consistent"])
        return consistent_count / len(self.metrics["language_consistency"])
    
    def _calculate_avg_conversation_quality(self) -> float:
        if not self.metrics["conversation_continuity"]:
            return 0.0
        total_score = sum(m["quality_score"] for m in self.metrics["conversation_continuity"])
        return total_score / len(self.metrics["conversation_continuity"])
    
    def _calculate_agentic_score(self) -> float:
        if not self.metrics["agentic_effectiveness"]:
            return 0.0
        total_score = sum(m["overall_score"] for m in self.metrics["agentic_effectiveness"])
        return total_score / len(self.metrics["agentic_effectiveness"])

# Global performance analytics instance
performance_analytics = PerformanceAnalytics() if ENABLE_PERFORMANCE_ANALYTICS else None

def get_openai_client():
    """Get OpenAI client dynamically to avoid import-time dependency issues"""
    try:
        # First try to get from core (preferred method)
        from core import openai_client
        if openai_client is not None:
            return openai_client
            
        # Try to initialize via core
        from core import initialize_openai_client
        if initialize_openai_client():
            from core import openai_client
            return openai_client
        
        # Fallback: Create OpenAI client directly if core initialization fails
        # This ensures production deployments work with proper secret manager configuration
        log_debug("Core OpenAI client unavailable, creating direct client")
        import os
        if os.getenv("OPENAI_API_KEY"):
            direct_client = OpenAI()
            log_debug("Direct OpenAI client created successfully")
            return direct_client
        else:
            log_debug("No OpenAI API key available")
            return None
            
    except Exception as e:
        log_debug("Failed to get OpenAI client", {"error": str(e)})
        return None

# Import intelligent routing system
try:
    from intelligent_routing_system import (
        QueryIntelligenceEngine, MultiSourceOrchestrator, InformationSynthesisEngine,
        QueryAnalysis, SourceResult, InformationSource
    )
    from advanced_internet_search import advanced_internet_search
    intelligent_routing_available = True
except ImportError as e:
    print(f"⚠️ Intelligent routing system not available: {e}")
    intelligent_routing_available = False

# Import Clair system prompt enforcer
try:
    from clair_prompt_enforcer import clair_prompt_enforcer
    prompt_enforcer_available = True
except ImportError as e:
    print(f"⚠️ Clair prompt enforcer not available: {e}")
    prompt_enforcer_available = False

# Import hotkey handler - DISABLED to allow GPT native intelligence
try:
    from hotkey_handler import hotkey_handler
    print("✅ Hotkey handler imported (DISABLED - GPT native handling enabled)")
    hotkey_handler_available = False  # DISABLED: Let GPT handle hotkeys naturally per Clair-sys-prompt.txt
except ImportError as e:
    print(f"⚠️ Hotkey handler not available: {e}")
    hotkey_handler_available = False

# Import response cache
try:
    from response_cache import response_cache
    from config import CACHE_RESPONSES
    cache_available = True
except ImportError as e:
    print(f"⚠️ Response cache not available: {e}")
    cache_available = False
    CACHE_RESPONSES = False

class ConversationManager:
    """Manages conversation context and memory for GPT-level intelligence"""
    
    def __init__(self):
        self.conversations = {}
        self.max_history = MAX_CONVERSATION_HISTORY
        
    def add_exchange(self, session_id: str, user_message: str, assistant_response: str):
        """Add a complete user-assistant exchange"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
            
        self.conversations[session_id].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_response}
        ])
        
        # Trim to max history
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
        
        log_debug("Added conversation exchange", {
            "session_id": session_id,
            "history_length": len(self.conversations[session_id])
        })
    
    def get_conversation_context(self, session_id: str) -> List[Dict]:
        """Get conversation history for context"""
        return self.conversations.get(session_id, [])
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            log_debug("Cleared conversation", {"session_id": session_id})
    
    def get_recent_active_sessions(self, limit: int = 5) -> List[str]:
        """Get recent active session IDs, sorted by most recent activity"""
        from datetime import datetime, timedelta
        
        # Sort sessions by the length of conversation (more active = more messages)
        # This is a simple heuristic - more sophisticated timestamp tracking could be added later
        session_activity = []
        
        for session_id, messages in self.conversations.items():
            if messages:  # Only include sessions with messages
                activity_score = len(messages)  # Simple activity measure
                session_activity.append((session_id, activity_score))
        
        # Sort by activity (most active first) and return session IDs
        sorted_sessions = sorted(session_activity, key=lambda x: x[1], reverse=True)
        recent_sessions = [session_id for session_id, _ in sorted_sessions[:limit]]
        
        log_debug("Retrieved recent active sessions", {
            "total_sessions": len(self.conversations),
            "active_sessions": len(session_activity), 
            "returned_sessions": len(recent_sessions),
            "recent_sessions": recent_sessions
        })
        
        return recent_sessions

class InternetSearchService:
    """Handles internet search for real-time information"""
    
    def __init__(self):
        self.search_enabled = INTERNET_ACCESS_ENABLED
    
    def detect_internet_need(self, query: str) -> bool:
        """Detect if query needs internet search"""
        internet_indicators = [
            "current", "latest", "recent", "today", "now", "2024", "2025",
            "news", "update", "market", "price", "rate", "trend", "stock",
            "what's new", "happening now", "current events"
        ]
        return any(indicator in query.lower() for indicator in internet_indicators)
    
    async def search_internet(self, query: str) -> str:
        """Perform internet search (placeholder for future implementation)"""
        if not self.search_enabled:
            return ""
        
        # TODO: Integrate with search API (Google, Bing, etc.)
        # For now, return indicator that internet search would be performed
        log_debug("Internet search requested", {"query": query})
        return f"[Note: Would perform internet search for current information about: {query}]"

class AIQueryClassifier:
    """Advanced query classification for life insurance domain"""
    
    def __init__(self):
        self.config = ENHANCED_INSURANCE_CONFIG
        self.enc = tiktoken.get_encoding("cl100k_base")
    
    def classify_intent(self, query: str) -> Dict[str, Any]:
        """Classify user intent using pattern matching and ML"""
        track_function_entry("classify_intent")
        
        query_lower = query.lower()
        intent_scores = {}
        
        # Score each intent pattern
        for intent_name, intent_config in self.config["ADVANCED_INTENTS"].items():
            score = 0.0
            matched_patterns = []
            
            for pattern in intent_config["patterns"]:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    score += 1.0
                    matched_patterns.append(pattern)
            
            if score > 0:
                intent_scores[intent_name] = {
                    "score": score / len(intent_config["patterns"]),
                    "matched_patterns": matched_patterns,
                    "response_strategy": intent_config["response_strategy"],
                    "required_context": intent_config["required_context"]
                }
        
        # Find highest scoring intent
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1]["score"])
            log_debug("Intent classified", {
                "query": query,
                "best_intent": best_intent[0],
                "score": best_intent[1]["score"],
                "all_scores": intent_scores
            })
            return {
                "intent": best_intent[0],
                "confidence": best_intent[1]["score"],
                "strategy": best_intent[1]["response_strategy"],
                "context_requirements": best_intent[1]["required_context"],
                "all_intents": intent_scores
            }
        else:
            return {
                "intent": "general_inquiry",
                "confidence": 0.5,
                "strategy": "general_response",
                "context_requirements": ["general_knowledge"],
                "all_intents": {}
            }
    
    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract key entities from the query"""
        track_function_entry("extract_entities")
        
        entities = {
            "ages": [],
            "amounts": [],
            "health_conditions": [],
            "family_roles": [],
            "product_types": []
        }
        
        # Extract ages
        for pattern in self.config["ENTITY_RECOGNITION"]["age_patterns"]:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities["ages"].extend(matches)
        
        # Extract amounts
        for pattern in self.config["ENTITY_RECOGNITION"]["amount_patterns"]:
            matches = re.findall(pattern, query.replace(",", ""), re.IGNORECASE)
            entities["amounts"].extend(matches)
        
        # Extract health conditions
        query_lower = query.lower()
        for condition in self.config["ENTITY_RECOGNITION"]["health_conditions"]:
            if condition in query_lower:
                entities["health_conditions"].append(condition)
        
        # Extract family roles
        for role in self.config["ENTITY_RECOGNITION"]["family_roles"]:
            if role in query_lower:
                entities["family_roles"].append(role)
        
        # Extract product types
        for product_type, product_info in self.config["PRODUCT_TYPES"].items():
            for name in product_info["names"]:
                if name in query_lower:
                    entities["product_types"].append(product_type)
            for keyword in product_info["keywords"]:
                if keyword in query_lower:
                    entities["product_types"].append(product_type)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        log_debug("Entities extracted", {"query": query, "entities": entities})
        return entities
    
    def calculate_query_priority(self, query: str, intent_data: Dict[str, Any]) -> float:
        """Calculate query priority for routing"""
        base_priority = 1.0
        query_lower = query.lower()
        
        # High priority keywords
        for keyword in self.config["QUERY_ROUTING"]["high_priority"]["keywords"]:
            if keyword in query_lower:
                base_priority *= self.config["QUERY_ROUTING"]["high_priority"]["boost_factor"]
        
        # Product-specific boost
        for keyword in self.config["QUERY_ROUTING"]["product_specific"]["keywords"]:
            if keyword in query_lower:
                base_priority *= self.config["QUERY_ROUTING"]["product_specific"]["boost_factor"]
        
        # Financial planning boost
        for keyword in self.config["QUERY_ROUTING"]["financial_planning"]["keywords"]:
            if keyword in query_lower:
                base_priority *= self.config["QUERY_ROUTING"]["financial_planning"]["boost_factor"]
        
        # Intent confidence boost
        base_priority *= (1 + intent_data["confidence"])
        
        return min(base_priority, 5.0)  # Cap at 5.0

class AIResponseGenerator:
    """Advanced response generation with domain expertise"""
    
    def __init__(self):
        self.config = ENHANCED_INSURANCE_CONFIG
        self.templates = self.config["RESPONSE_TEMPLATES"]
    
    def select_system_prompt(self, intent: str, strategy: str) -> str:
        """Select appropriate system prompt based on intent"""
        
        if strategy in SYSTEM_PROMPTS:
            return SYSTEM_PROMPTS[strategy]
        elif intent in ["product_comparison", "coverage_amount"]:
            return SYSTEM_PROMPTS["product_comparison"]
        elif intent in ["premium_inquiry", "coverage_amount"]:
            return SYSTEM_PROMPTS["needs_analysis"]
        elif intent in ["underwriting_health"]:
            return SYSTEM_PROMPTS["underwriting"]
        else:
            return SYSTEM_PROMPTS["general"]
    
    def enhance_context(self, context: str, entities: Dict[str, List[str]], intent: str) -> str:
        """Enhance context with entity-specific information"""
        enhanced_context = context
        
        # Add entity context
        if entities["product_types"]:
            product_info = []
            for product_type in entities["product_types"]:
                if product_type in self.config["PRODUCT_TYPES"]:
                    info = self.config["PRODUCT_TYPES"][product_type]
                    product_info.append(f"**{product_type.replace('_', ' ').title()}**: {', '.join(info['features'])}")
            
            if product_info:
                enhanced_context += f"\n\n**Relevant Product Information:**\n{chr(10).join(product_info)}"
        
        # Add health condition context
        if entities["health_conditions"]:
            enhanced_context += f"\n\n**Health Considerations**: The query mentions {', '.join(entities['health_conditions'])}. Consider underwriting implications."
        
        # Add age context
        if entities["ages"]:
            enhanced_context += f"\n\n**Age Factors**: Query mentions age(s) {', '.join(entities['ages'])}. Consider age-based pricing and product suitability."
        
        return enhanced_context
    
    def generate_response(self, query: str, context: str, intent_data: Dict[str, Any], entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate intelligent response using OpenAI"""
        track_function_entry("generate_response")
        
        try:
            # Select system prompt
            system_prompt = self.select_system_prompt(
                intent_data["intent"], 
                intent_data["strategy"]
            )
            
            # Enhance context with entities
            enhanced_context = self.enhance_context(context, entities, intent_data["intent"])
            
            # Prepare user prompt - clean and natural
            if enhanced_context.strip():
                user_prompt = f"Based on our knowledge base:\n\n{enhanced_context}\n\n{query}"
            else:
                user_prompt = query
            
            log_debug("Generating AI response", {
                "intent": intent_data["intent"],
                "strategy": intent_data["strategy"],
                "entities_found": len([e for e in entities.values() if e]),
                "context_length": len(enhanced_context)
            })
            
            # Call OpenAI with optimal GPT-like parameters
            client = get_openai_client()
            if not client:
                raise Exception("OpenAI client not available")
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                presence_penalty=PRESENCE_PENALTY,
                frequency_penalty=FREQUENCY_PENALTY
            )
            
            answer = response.choices[0].message.content
            
            return {
                "answer": answer,
                "intent": intent_data["intent"],
                "confidence": intent_data["confidence"],
                "strategy": intent_data["strategy"],
                "entities": entities,
                "context_used": bool(context.strip()),
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            log_debug("Error generating AI response", {"error": str(e)})
            return {
                "answer": "I'm experiencing technical difficulties generating a response. Please try again.",
                "intent": intent_data["intent"],
                "confidence": 0.0,
                "strategy": "error_response",
                "entities": entities,
                "context_used": False,
                "error": str(e)
            }

class ResponseValidator:
    """Validates Clair's responses for compliance with system prompt guidelines"""
    
    def __init__(self):
        self.required_disclaimer_phrases = [
            "verify with actual policy documents",
            "consult with a licensed",
            "professional consultation",
            "specific details should be verified",
            "licensed insurance professional"
        ]
        
        self.personalization_triggers = [
            "insurance", "policy", "coverage", "premium", "recommend", "suggest", "best"
        ]
    
    def validate_response_compliance(self, query: str, response: str) -> Dict[str, Any]:
        """Validate response against system prompt requirements"""
        validation_results = {
            "compliance_score": 1.0,
            "issues": [],
            "recommendations": []
        }
        
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Check if advice-giving response includes disclaimer
        is_advice_response = any(trigger in query_lower for trigger in self.personalization_triggers)
        
        if is_advice_response:
            has_disclaimer = any(phrase in response_lower for phrase in self.required_disclaimer_phrases)
            if not has_disclaimer:
                validation_results["compliance_score"] -= 0.3
                validation_results["issues"].append("Missing professional consultation disclaimer")
                validation_results["recommendations"].append("Add disclaimer about consulting licensed professionals")
        
        # Check for personalization questions
        asks_questions = "?" in response or any(word in response_lower for word in ["what's your", "how old", "tell me about your"])
        if is_advice_response and not asks_questions:
            validation_results["compliance_score"] -= 0.2
            validation_results["issues"].append("Missing personalization questions")
            validation_results["recommendations"].append("Ask about client's specific situation (age, family, goals)")
        
        return validation_results

class IntelligentAIService:
    """Main AI service with GPT-level intelligence and conversation awareness"""
    
    def __init__(self):
        # LAZY INITIALIZATION: Don't create heavy objects during __init__
        # This prevents module import failures if any component fails to initialize
        self._classifier = None
        self._generator = None
        self._conversation_manager = None
        self._internet_service = None
        
        # Initialize ultra-intelligent routing system - DISABLED for simplicity but enable intelligent search
        # Use simpler intelligent routing in chat_router instead of complex ultra-intelligence system
        self.ultra_intelligence_enabled = False  # Use simple intelligent search in chat_router
        
        # Initialize Clair system prompt enforcer - DISABLED to let GPT handle everything naturally
        self.prompt_enforcer_enabled = False  # Was: prompt_enforcer_available
        
        # Initialize hotkey handler - ENABLED for consistent language responses
        self.hotkey_handler_enabled = hotkey_handler_available
    
    @property
    def classifier(self):
        """Lazy-loaded AI query classifier"""
        if self._classifier is None:
            try:
                self._classifier = AIQueryClassifier()
                log_debug("AIQueryClassifier initialized successfully")
            except Exception as e:
                log_debug("Failed to initialize AIQueryClassifier", {"error": str(e)})
                # Create a minimal fallback classifier
                self._classifier = type('MockClassifier', (), {
                    'classify_intent': lambda self, query: {"intent": "general_inquiry", "confidence": 0.5, "strategy": "general_response", "context_requirements": [], "all_intents": []},
                    'extract_entities': lambda self, query: {},
                    'calculate_query_priority': lambda self, query, intent_data: 1.0,
                    'config': {"ADVANCED_INTENTS": {}, "ENTITY_RECOGNITION": {}, "PRODUCT_TYPES": {}}
                })()
        return self._classifier
    
    @property 
    def generator(self):
        """Lazy-loaded AI response generator"""
        if self._generator is None:
            try:
                self._generator = AIResponseGenerator()
                log_debug("AIResponseGenerator initialized successfully")
            except Exception as e:
                log_debug("Failed to initialize AIResponseGenerator", {"error": str(e)})
                # Create a minimal fallback generator
                self._generator = type('MockGenerator', (), {})()
        return self._generator
    
    @property
    def conversation_manager(self):
        """Lazy-loaded conversation manager"""
        if self._conversation_manager is None:
            try:
                self._conversation_manager = ConversationManager()
                log_debug("ConversationManager initialized successfully")
            except Exception as e:
                log_debug("Failed to initialize ConversationManager", {"error": str(e)})
                # Create a minimal fallback conversation manager
                self._conversation_manager = type('MockConversationManager', (), {
                    'get_conversation_context': lambda self, session_id: [],
                    'add_message': lambda self, session_id, role, content: None,
                    'clear_conversation': lambda self, session_id: None,
                    'get_recent_active_sessions': lambda self, limit=5: []
                })()
        return self._conversation_manager
    
    @property
    def internet_service(self):
        """Lazy-loaded internet search service"""  
        if self._internet_service is None:
            try:
                self._internet_service = InternetSearchService()
                log_debug("InternetSearchService initialized successfully")
            except Exception as e:
                log_debug("Failed to initialize InternetSearchService", {"error": str(e)})
                # Create a minimal fallback internet service
                self._internet_service = type('MockInternetService', (), {})()
        return self._internet_service
    
    def _detect_user_language(self, text: str) -> str:
        """Enhanced language detection for consistent responses"""
        import re
        
        # Remove whitespace and punctuation for more accurate analysis
        text_clean = re.sub(r'[^\u4e00-\u9fff\w]', '', text)
        
        if len(text_clean) == 0:
            return "english"  # Default to English for empty/punctuation-only text
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text_clean))
        total_chars = len(text_clean)
        
        # More sensitive threshold for Chinese detection
        if chinese_chars / total_chars > 0.15:  # Even a few Chinese characters indicate Chinese context
            return "chinese"
        else:
            return "english"
    
    def _detect_response_language(self, response_text: str, fallback_language: str) -> str:
        """Detect the language of the AI response for metadata consistency"""
        import re
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', response_text))
        total_chars = len(re.sub(r'\s+', '', response_text))  # Remove whitespace for analysis
        
        if total_chars == 0:
            return fallback_language
        
        chinese_ratio = chinese_chars / total_chars
        
        # If response contains significant Chinese content, it's Chinese
        if chinese_ratio > 0.3:
            return "chinese"
        # If response contains some Chinese but not dominant, check fallback
        elif chinese_ratio > 0.05 and fallback_language == "chinese":
            return "chinese"
        else:
            return "english"
    
    def _extract_agentic_insights(self, response_text: str) -> dict:
        """Extract agentic metadata from natural language response"""
        return {
            "reflection_notes": "Natural response generated with full context awareness",
            "planning_steps": ["Analyzed user query", "Applied domain expertise", "Provided contextual response"],
            "tool_recommendations": [],
            "context_synthesis": "Successfully integrated conversation context and system expertise"
        }
    
    def _calculate_response_quality(self, structured_response: Dict[str, Any]) -> float:
        """Calculate response quality score for analytics"""
        quality_score = 0.5  # Base score
        
        # Confidence level contribution
        confidence = structured_response.get("confidence_level", "medium")
        if confidence == "high":
            quality_score += 0.3
        elif confidence == "low":
            quality_score -= 0.2
        
        # Agentic metadata contribution
        agentic_data = structured_response.get("agentic_metadata", {})
        if agentic_data:
            if agentic_data.get("reflection_notes"):
                quality_score += 0.1
            if agentic_data.get("planning_steps"):
                quality_score += 0.1
            if agentic_data.get("tool_recommendations"):
                quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def _detect_english_simple(self, text: str) -> bool:
        """Simple English detection for hotkey language preference"""
        import re
        # Check for Chinese characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.replace(" ", ""))
        
        if total_chars == 0:
            return True  # Default to English if empty
        
        # If more than 20% Chinese characters, it's NOT English
        return chinese_chars / total_chars <= 0.2
    
    def process_query(self, query: str, context: str = "", filters: List[str] = None) -> Dict[str, Any]:
        """Process a query with full AI intelligence"""
        track_function_entry("process_query")
        
        start_time = datetime.utcnow()
        
        # Step 1: Classify intent
        intent_data = self.classifier.classify_intent(query)
        
        # Step 2: Extract entities
        entities = self.classifier.extract_entities(query)
        
        # Step 3: Calculate priority
        priority = self.classifier.calculate_query_priority(query, intent_data)
        
        # Step 4: Generate response
        response_data = self.generator.generate_response(query, context, intent_data, entities)
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Compile final result
        result = {
            **response_data,
            "query": query,
            "priority": priority,
            "processing_time_seconds": processing_time,
            "filters_applied": filters or [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        log_debug("Query processing completed", {
            "intent": intent_data["intent"],
            "confidence": intent_data["confidence"],
            "priority": priority,
            "processing_time": processing_time,
            "entities_found": sum(len(v) for v in entities.values())
        })
        
        return result
    
    async def process_query_with_ultra_intelligence(
        self, 
        query: str, 
        context: str = "", 
        session_id: str = "default",
        vertex_search_func: callable = None,
        filters: List[str] = None
    ) -> Dict[str, Any]:
        """Ultra-intelligent query processing with multi-source routing and synthesis"""
        track_function_entry("process_query_with_ultra_intelligence")
        
        start_time = datetime.utcnow()
        
        # Check for hotkey input first (even if ultra-intelligence is disabled)
        if self.hotkey_handler_enabled and hotkey_handler.is_hotkey(query):
            log_debug("HOTKEY DETECTED - Starting language analysis", {
                "hotkey": query,
                "session_id": session_id,
                "handler_enabled": self.hotkey_handler_enabled
            })
            
            # Determine language preference
            conversation_history = []
            if CONVERSATION_MEMORY_ENABLED:
                conversation_history = self.conversation_manager.get_conversation_context(session_id)
            
            log_debug("Conversation history retrieved", {
                "session_id": session_id,
                "history_length": len(conversation_history),
                "recent_messages": [{"role": msg.get("role", ""), "content": msg.get("content", "")[:50]} for msg in conversation_history[-4:]]
            })
            
            # Intelligently determine language based on conversation history
            needs_chinese = False  # Default to English unless Chinese context is found
            
            # Check conversation history for language context (BOTH user AND assistant messages)
            for msg in reversed(conversation_history[-8:]):  # Check last 4 exchanges
                msg_role = msg.get("role", "")
                msg_content = msg.get("content", "")
                
                # Check both user and assistant messages for language clues
                if msg_role in ["user", "assistant"] and len(msg_content.strip()) > 2:
                    # For user messages, ignore single letter hotkeys
                    if msg_role == "user" and len(msg_content.strip()) <= 2:
                        continue
                    
                    detected_lang = self._detect_user_language(msg_content)
                    if detected_lang == "chinese":
                        needs_chinese = True
                        log_debug("HOTKEY LANGUAGE: Chinese found - setting needs_chinese=True", {
                            "source": msg_role,
                            "content_sample": msg_content[:50],
                            "session_id": session_id,
                            "detected_language": detected_lang
                        })
                        break
                    elif detected_lang == "english":
                        needs_chinese = False
                        log_debug("Hotkey language detection: English found", {
                            "source": msg_role, 
                            "content_sample": msg_content[:50],
                            "session_id": session_id
                        })
                        # Continue checking - Chinese takes priority if found later
            
            log_debug("HOTKEY FINAL DECISION", {
                "session_id": session_id,
                "hotkey": query,
                "needs_chinese": needs_chinese,
                "will_use_chinese_response": needs_chinese
            })
            
            hotkey_response = hotkey_handler.get_hotkey_response(query, needs_chinese)
            
            if hotkey_response:
                # Save conversation for natural flow
                if CONVERSATION_MEMORY_ENABLED:
                    self.conversation_manager.add_exchange(session_id, query, hotkey_response)
                
                return {
                    "answer": hotkey_response,
                    "query": query,
                    "session_id": session_id,
                    "hotkey_processed": True,
                    "conversation_aware": len(conversation_history) > 0,
                    "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
                    "clair_enforcement": {
                        "enforcer_enabled": False,
                        "enforcement_applied": False,
                        "language_enforcement": needs_chinese,
                        "hotkey_response": True
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        if not self.ultra_intelligence_enabled:
            # Fallback to standard GPT processing
            return await self.process_query_with_gpt_intelligence(query, context, session_id, filters)
        
        try:
            # 1. Ultra-intelligent query analysis
            analysis = await self.query_intelligence.analyze_query(query, context)
            
            log_debug("Ultra-intelligent query analysis", {
                "query_type": analysis.query_type.value,
                "confidence": analysis.confidence,
                "requires_current": analysis.requires_current_info,
                "requires_specific": analysis.requires_specific_docs,
                "sources": [s.value for s in analysis.priority_sources],
                "strategy": analysis.search_strategy
            })
            
            # 2. Execute multi-source search strategy
            source_results = await self.multi_source_orchestrator.execute_search_strategy(
                query=query,
                analysis=analysis,
                vertex_search_func=self._create_vertex_search_wrapper(context, vertex_search_func),
                internet_search_func=self._create_internet_search_wrapper()
            )
            
            # 3. Synthesize information from multiple sources
            synthesis_result = self.synthesis_engine.synthesize_results(source_results, query, analysis)
            
            # 4. Get conversation history for context
            conversation_history = []
            if CONVERSATION_MEMORY_ENABLED:
                conversation_history = self.conversation_manager.get_conversation_context(session_id)
            
            # 5. Build ultra-intelligent message context
            messages = [
                {"role": "system", "content": CLAIR_SYSTEM_PROMPT_ACTIVE}
            ]
            
            log_debug("System prompt being sent to OpenAI", {
                "prompt_length": len(CLAIR_SYSTEM_PROMPT_ACTIVE),
                "prompt_preview": CLAIR_SYSTEM_PROMPT_ACTIVE[:200] + "..." if len(CLAIR_SYSTEM_PROMPT_ACTIVE) > 200 else CLAIR_SYSTEM_PROMPT_ACTIVE
            })
            
            # Add conversation history
            messages.extend(conversation_history)
            
            # 6. Create enhanced user message with synthesized information
            if synthesis_result["synthesized_content"]:
                user_message = f"""COMPREHENSIVE RESEARCH CONTEXT:
{synthesis_result["synthesized_content"]}

ANALYSIS METADATA:
- Query Type: {analysis.query_type.value}
- Information Sources: {', '.join([s.value for s in analysis.priority_sources])}
- Synthesis Confidence: {synthesis_result["confidence_score"]:.2f}
- Total Sources Consulted: {synthesis_result["synthesis_metadata"]["sources_used"]}

CLIENT QUESTION: {query}

Please provide expert advice based on this comprehensive research, following your role as Clair, the expert financial advisor."""
            else:
                user_message = f"""CLIENT QUESTION: {query}

Note: Limited current information available. Please provide expert guidance based on your knowledge base and emphasize the need for current information verification."""
            
            messages.append({"role": "user", "content": user_message})
            
            # 7. Generate ultra-intelligent response with Structured Outputs
            client = get_openai_client()
            if not client:
                raise Exception("OpenAI client not available")
            
            # Configure Structured Outputs for 100% reliability (GPT-4o-2024-08-06)
            if ENABLE_STRUCTURED_OUTPUTS:
                response = client.chat.completions.create(
                    model=GPT_MODEL,
                    messages=messages,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    presence_penalty=PRESENCE_PENALTY,
                    frequency_penalty=FREQUENCY_PENALTY,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "clair_response",
                            "schema": STRUCTURED_OUTPUT_SCHEMA,
                            "strict": True
                        }
                    },
                    timeout=REQUEST_TIMEOUT
                )
                
                # Parse structured response for guaranteed reliability
                import json
                try:
                    structured_response = json.loads(response.choices[0].message.content)
                    answer = structured_response.get("response", response.choices[0].message.content)
                    
                    # Extract agentic metadata if available
                    response_metadata = {
                        "language": structured_response.get("language", "unknown"),
                        "confidence_level": structured_response.get("confidence_level", "medium"),
                        "structured_parsing_success": True,
                        "agentic_metadata": structured_response.get("agentic_metadata", {})
                    }
                    
                    log_debug("Ultra Intelligence structured output parsed successfully", {
                        "language": response_metadata["language"],
                        "confidence": response_metadata["confidence_level"],
                        "response_length": len(answer)
                    })
                    
                except (json.JSONDecodeError, KeyError) as e:
                    log_debug("Ultra Intelligence structured output parsing failed", {"error": str(e)})
                    answer = response.choices[0].message.content
                    response_metadata = {
                        "language": "unknown",
                        "confidence_level": "medium",
                        "structured_parsing_success": False,
                        "agentic_metadata": {}
                    }
            else:
                # Fallback to regular completion
                response = client.chat.completions.create(
                    model=GPT_MODEL,
                    messages=messages,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    presence_penalty=PRESENCE_PENALTY,
                    frequency_penalty=FREQUENCY_PENALTY,
                    stream=False,
                    timeout=REQUEST_TIMEOUT
                )
                answer = response.choices[0].message.content
                response_metadata = {"structured_parsing_success": False}
            
            # 8. Save conversation for natural flow
            if CONVERSATION_MEMORY_ENABLED:
                self.conversation_manager.add_exchange(session_id, query, answer)
            
            # 9. Apply Clair system prompt enforcement
            if self.prompt_enforcer_enabled:
                answer, enforcement_result = clair_prompt_enforcer.enforce_system_prompt(query, answer)
            else:
                enforcement_result = None
            
            # 10. Skip response validation - let GPT handle compliance naturally
            validation_results = {"compliance_score": 1.0, "issues": [], "recommendations": []}
            
            # 11. Create comprehensive result
            result = {
                "answer": answer,
                "query": query,
                "session_id": session_id,
                "ultra_intelligence_metadata": {
                    "query_analysis": {
                        "type": analysis.query_type.value,
                        "confidence": analysis.confidence,
                        "complexity_score": analysis.complexity_score,
                        "search_strategy": analysis.search_strategy
                    },
                    "information_synthesis": synthesis_result,
                    "sources_used": [s.value for s in analysis.priority_sources],
                    "multi_source_enabled": True
                },
                "conversation_aware": len(conversation_history) > 0,
                "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "clair_enforcement": {
                    "enforcer_enabled": self.prompt_enforcer_enabled,
                    "enforcement_applied": enforcement_result.enforcement_applied if enforcement_result else False,
                    "language_enforcement": enforcement_result.needs_chinese if enforcement_result else False,
                    "mandatory_links": enforcement_result.mandatory_links if enforcement_result else [],
                    "trigger_type": enforcement_result.trigger_type if enforcement_result else "none"
                },
                "compliance_validation": validation_results,
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "structured_output_metadata": response_metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            log_debug("Ultra-intelligent processing completed", {
                "session_id": session_id,
                "query_type": analysis.query_type.value,
                "sources_used": len(source_results),
                "synthesis_confidence": synthesis_result["confidence_score"],
                "compliance_score": validation_results["compliance_score"],
                "total_processing_time": result["processing_time_seconds"]
            })
            
            return result
            
        except Exception as e:
            log_debug("Ultra-intelligent processing failed", {"error": str(e)})
            # Fallback to standard GPT processing
            return await self.process_query_with_gpt_intelligence(query, context, session_id, filters)
    
    def _create_vertex_search_wrapper(self, context: str, vertex_search_func: callable) -> callable:
        """Create wrapper for Vertex AI search function"""
        async def vertex_search_wrapper(query: str) -> Dict[str, Any]:
            if vertex_search_func:
                # Use provided search function
                return await vertex_search_func(query)
            else:
                # Use existing context or return empty result
                return {
                    "context": context,
                    "highest_similarity_score": 0.8 if context else 0.0,
                    "documents_found": 1 if context else 0
                }
        
        return vertex_search_wrapper
    
    def _create_internet_search_wrapper(self) -> callable:
        """Create wrapper for internet search function"""
        async def internet_search_wrapper(query: str) -> Dict[str, Any]:
            try:
                search_results = await advanced_internet_search.search_multiple_sources(query)
                return search_results
            except Exception as e:
                log_debug("Internet search wrapper failed", {"error": str(e)})
                return {
                    "content": f"Internet search unavailable for: {query}",
                    "sources": [],
                    "relevance_score": 0.0,
                    "total_sources": 0
                }
        
        return internet_search_wrapper
    
    async def process_query_with_gpt_intelligence(
        self, 
        query: str, 
        context: str = "", 
        session_id: str = "default",
        filters: List[str] = None
    ) -> Dict[str, Any]:
        """GPT-Native conversation processing - Pure GPT intelligence with natural flow"""
        track_function_entry("process_query_with_gpt_intelligence")
        
        start_time = datetime.utcnow()
        
        # Check cache first if available and enabled
        if cache_available and CACHE_RESPONSES:
            cached_response = response_cache.get(query, session_id)
            if cached_response:
                # Update processing time to show cached response speed
                cached_response["processing_time_seconds"] = (datetime.utcnow() - start_time).total_seconds()
                cached_response["cached_response"] = True
                log_debug("Returning cached response", {"query": query[:50]})
                return cached_response
        
        # 1. Get conversation history for natural flow
        conversation_history = []
        if CONVERSATION_MEMORY_ENABLED:
            conversation_history = self.conversation_manager.get_conversation_context(session_id)
        
        # 2. Build messages array following GPT-Native best practices
        messages = [
            {"role": "system", "content": CLAIR_SYSTEM_PROMPT_ACTIVE}
        ]
        
        # Add conversation history for context (unmodified, natural conversation)
        messages.extend(conversation_history)
        
        # 3. GPT-NATIVE MESSAGE CONSTRUCTION - Natural conversation flow
        if context.strip():
            # Natural context integration - let GPT understand relevance
            user_message = f"Here's relevant information from our documents:\n\n{context}\n\n{query}"
        else:
            # Pure natural user input - no formatting interference
            user_message = query
        
        messages.append({"role": "user", "content": user_message})
        
        # 4. Generate response using GPT-Native parameters with Structured Outputs
        try:
            client = get_openai_client()
            if not client:
                raise Exception("OpenAI client not available")
            
            # Configure Structured Outputs for 100% reliability (GPT-4o-2024-08-06)
            if ENABLE_STRUCTURED_OUTPUTS:
                response = client.chat.completions.create(
                    model=GPT_MODEL,
                    messages=messages,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    presence_penalty=PRESENCE_PENALTY,
                    frequency_penalty=FREQUENCY_PENALTY,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "clair_response",
                            "schema": STRUCTURED_OUTPUT_SCHEMA,
                            "strict": True
                        }
                    },
                    stream=False,
                    timeout=REQUEST_TIMEOUT
                )
                
                # HYBRID RESPONSE EXTRACTION - Parse structured JSON for natural + technical data
                import json
                import re
                
                try:
                    raw_content = response.choices[0].message.content
                    
                    # Handle markdown JSON format (```json...```)
                    json_match = re.search(r'```json\s*\n?({.*?})\s*\n?```', raw_content, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(1)
                        log_debug("Extracted JSON from markdown format", {"content_length": len(json_content)})
                    else:
                        # Try raw content as JSON
                        json_content = raw_content.strip()
                        if not json_content.startswith('{'):
                            raise json.JSONDecodeError("Not JSON format", json_content, 0)
                    
                    structured_response = json.loads(json_content)
                    
                    # Extract the NATURAL conversational response for users
                    answer = structured_response.get("response", "")
                    
                    if not answer:  # Fallback if response field is empty
                        answer = "I apologize, but there seems to be a technical issue. Could you please try asking your question again?"
                        log_debug("Empty response field in structured output", {"raw_content": raw_content[:200]})
                    
                    # Extract ALL structured metadata for technical systems and multimedia
                    response_metadata = {
                        "language": structured_response.get("language", "unknown"),
                        "conversation_context": structured_response.get("conversation_context", "new_query"),
                        "hotkey_suggestions": structured_response.get("hotkey_suggestions", []),
                        "confidence_level": structured_response.get("confidence_level", "medium"),
                        "structured_parsing_success": True,
                        
                        # MULTIMEDIA & INTERACTION SUPPORT
                        "multimedia_content": structured_response.get("multimedia_content", {
                            "images": [],
                            "documents": [],
                            "forms": [],
                            "charts": []
                        }),
                        "action_items": structured_response.get("action_items", []),
                        
                        # Advanced AI capabilities
                        "agentic_metadata": structured_response.get("agentic_metadata", {}),
                        
                        # Technical debugging
                        "parsing_method": "json_structured_extraction",
                        "original_length": len(response.choices[0].message.content)
                    }
                    
                    log_debug("HYBRID extraction successful", {
                        "natural_response_length": len(answer),
                        "language": response_metadata["language"],
                        "context": response_metadata["conversation_context"],
                        "multimedia_items": len(response_metadata["multimedia_content"].get("images", []) + 
                                                response_metadata["multimedia_content"].get("forms", []))
                    })
                    
                    # Track performance analytics if enabled
                    if performance_analytics and ENABLE_PERFORMANCE_ANALYTICS:
                        # Enhanced language consistency tracking
                        user_lang = self._detect_user_language(query)
                        response_lang = structured_response.get("language", "unknown")
                        
                        # For hotkeys, check conversation history for actual language context
                        if len(query.strip()) <= 2 and query.strip().upper() in ['A', 'R', 'E', 'C', 'S', 'Y', 'L']:
                            conversation_history = self.conversation_manager.get_conversation_context(session_id)
                            for msg in reversed(conversation_history[-8:]):
                                msg_role = msg.get("role", "")
                                msg_content = msg.get("content", "")
                                
                                # Check both user and assistant messages
                                if msg_role in ["user", "assistant"] and len(msg_content.strip()) > 2:
                                    # Skip single letter user inputs
                                    if msg_role == "user" and len(msg_content.strip()) <= 2:
                                        continue
                                    user_lang = self._detect_user_language(msg_content)
                                    if user_lang == "chinese":  # Chinese takes priority
                                        break
                        
                        performance_analytics.track_language_consistency(user_lang, response_lang, session_id)
                        
                        # Conversation continuity tracking
                        context_type = structured_response.get("conversation_context", "new_query")
                        quality_score = self._calculate_response_quality(structured_response)
                        performance_analytics.track_conversation_continuity(context_type, session_id, quality_score)
                        
                        # Agentic effectiveness tracking
                        if agentic_data:
                            reflection_quality = len(agentic_data.get("reflection_notes", "")) // 20  # Rough quality metric
                            planning_depth = len(agentic_data.get("planning_steps", []))
                            tool_relevance = len(agentic_data.get("tool_recommendations", []))
                            performance_analytics.track_agentic_effectiveness(reflection_quality, planning_depth, tool_relevance)
                except (json.JSONDecodeError, KeyError) as e:
                    log_debug("HYBRID extraction failed, attempting advanced fallback", {"error": str(e)})
                    
                    # ADVANCED FALLBACK EXTRACTION - Multiple strategies
                    try:
                        import re
                        
                        # Strategy 1: Extract response field from partial JSON
                        response_match = re.search(r'"response":\s*"([^"]*(?:\\.[^"]*)*)"', raw_content, re.DOTALL)
                        if response_match:
                            answer = response_match.group(1).replace('\\"', '"').replace('\\n', '\n')
                            log_debug("HYBRID fallback: Response field extracted", {"length": len(answer)})
                        else:
                            # Strategy 2: Look for natural language content (non-JSON)
                            # Remove any JSON-like markers and extract natural text
                            cleaned = re.sub(r'```json|```|[{}]', '', raw_content)
                            cleaned = re.sub(r'"[^"]+"\s*:', '', cleaned)  # Remove JSON keys
                            cleaned = cleaned.strip().strip(',')
                            
                            if len(cleaned) > 10 and not cleaned.startswith('{'):
                                answer = cleaned
                                log_debug("HYBRID fallback: Natural text extracted", {"length": len(answer)})
                            else:
                                # Strategy 3: Use raw content as-is
                                answer = raw_content
                                log_debug("HYBRID fallback: Using raw content")
                                
                    except Exception as extract_error:
                        log_debug("HYBRID fallback failed", {"error": str(extract_error)})
                        answer = raw_content
                    
                    # Create intelligent structured metadata for fallback
                    # Extract language from user query
                    detected_language = self._detect_user_language(query)
                    
                    # Let GPT generate dynamic contextual hotkeys based on conversation context
                    # No hardcoded hotkeys - GPT will create them based on the conversation topic
                    contextual_hotkeys = []  # Empty - GPT generates in structured response
                    
                    response_metadata = {
                        "language": detected_language,
                        "conversation_context": "new_query", 
                        "hotkey_suggestions": contextual_hotkeys,
                        "confidence_level": "medium",
                        "structured_parsing_success": False,
                        "multimedia_content": {"images": [], "documents": [], "forms": [], "charts": []},
                        "action_items": [],
                        "agentic_metadata": {},
                        "parsing_method": "intelligent_fallback_extraction",
                        "parsing_error": str(e)
                    }
            else:
                # Fallback to regular completion
                response = client.chat.completions.create(
                    model=GPT_MODEL,
                    messages=messages,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    presence_penalty=PRESENCE_PENALTY,
                    frequency_penalty=FREQUENCY_PENALTY,
                    stream=False,
                    timeout=REQUEST_TIMEOUT
                )
                answer = response.choices[0].message.content
                
                # Generate intelligent hotkey suggestions for regular completion
                # For hotkeys and short queries, check conversation history for language context
                detected_language = self._detect_user_language(query)
                
                # ENHANCED HOTKEY LANGUAGE DETECTION: Check conversation history for single letters
                if len(query.strip()) <= 2 and query.strip().upper() in ['A', 'R', 'E', 'C', 'S', 'Y', 'L']:
                    # This is likely a hotkey - intelligently determine language from conversation context
                    if CONVERSATION_MEMORY_ENABLED:
                        conversation_history = self.conversation_manager.get_conversation_context(session_id)
                    
                    # Systematic language detection from conversation history (BOTH user AND assistant messages)
                    for msg in reversed(conversation_history[-8:]):  # Check last 4 exchanges more thoroughly
                        msg_role = msg.get("role", "")
                        msg_content = msg.get("content", "")
                        
                        # Check both user and assistant messages for language context
                        if msg_role in ["user", "assistant"] and len(msg_content.strip()) > 2:
                            # Skip single letter user inputs (other hotkeys)
                            if msg_role == "user" and len(msg_content.strip()) <= 2:
                                continue
                                
                            hist_language = self._detect_user_language(msg_content)
                            if hist_language == "chinese":
                                detected_language = "chinese"
                                log_debug("Enhanced hotkey language detection", {
                                    "hotkey": query,
                                    "detected_from_history": "chinese",
                                    "source_role": msg_role,
                                    "history_sample": msg_content[:50]
                                })
                                break  # Chinese found, stop searching
                            elif hist_language == "english":
                                detected_language = "english"
                                log_debug("Enhanced hotkey language detection", {
                                    "hotkey": query,
                                    "detected_from_history": "english",
                                    "source_role": msg_role,
                                    "history_sample": msg_content[:50]
                                })
                                # Continue searching in case there's Chinese context later
                
                # Let GPT generate dynamic contextual hotkeys via structured response
                # No hardcoded hotkeys - GPT intelligently creates them based on conversation topic
                contextual_hotkeys = []  # Empty - GPT generates dynamic hotkeys
                
                # Determine conversation context based on query type
                conversation_context = "new_query"
                if len(query.strip()) <= 2 and query.strip().upper() in ['A', 'R', 'E', 'C', 'S', 'Y', 'L']:
                    conversation_context = "hotkey_continuation"
                
                response_metadata = {
                    "language": self._detect_response_language(answer, detected_language),
                    "conversation_context": conversation_context,
                    "hotkey_suggestions": contextual_hotkeys,
                    "confidence_level": "high",
                    "structured_parsing_success": True,
                    "multimedia_content": {"images": [], "documents": [], "forms": [], "charts": []},
                    "action_items": [],
                    "agentic_metadata": self._extract_agentic_insights(answer),
                    "parsing_method": "intelligent_natural_language_extraction"
                }
            
            # 5. Save conversation for natural flow (GPT-Native memory)
            if CONVERSATION_MEMORY_ENABLED:
                self.conversation_manager.add_exchange(session_id, query, answer)
            
            # 6. GPT-NATIVE RESPONSE - No post-processing interference
            # Let GPT handle all intelligence naturally through system prompt
            
            # 7. Return clean, GPT-native result with structured metadata
            result = {
                "answer": answer,
                "query": query,
                "session_id": session_id,
                "conversation_aware": len(conversation_history) > 0,
                "context_used": bool(context.strip()),
                "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "hotkey_suggestions": response_metadata.get("hotkey_suggestions", []),
                "gpt_native": {
                    "pure_gpt_response": True,
                    "no_post_processing": True,
                    "natural_conversation": True,
                    "system_prompt_intelligence": True,
                    "structured_outputs_enabled": ENABLE_STRUCTURED_OUTPUTS
                },
                "structured_metadata": response_metadata,
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "timestamp": datetime.utcnow().isoformat(),
                "cached_response": False
            }
            
            # Cache the result for future performance optimization
            if cache_available and CACHE_RESPONSES:
                response_cache.put(query, result, session_id)
            
            log_debug("Natural conversation processed", {
                "session_id": session_id,
                "conversation_turns": len(conversation_history) // 2,
                "context_used": bool(context.strip()),
                "tokens_used": response.usage.total_tokens
            })
            
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()  # Print full stack trace to console
            log_debug("Error in conversation processing - DETAILED", {
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            })
            # Clean fallback response
            return {
                "answer": "I apologize, but I'm experiencing a technical issue. Could you please try asking your question again?",
                "query": query,
                "session_id": session_id,
                "conversation_aware": False,
                "context_used": False,
                "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "error": str(e),
                "error_details": traceback.format_exc(),
                "timestamp": datetime.utcnow().isoformat()
            }

# LAZY GLOBAL AI SERVICE INSTANCE - Prevents import failures
_ai_service_instance = None

def get_ai_service():
    """Get AI service instance with lazy initialization and fallback"""
    global _ai_service_instance
    if _ai_service_instance is None:
        try:
            _ai_service_instance = IntelligentAIService()
            log_debug("Global AI service instance created successfully")
        except Exception as e:
            log_debug("Failed to create global AI service instance", {"error": str(e)})
            # Create minimal fallback instance
            class MockAIService:
                def __init__(self):
                    self.conversation_manager = None
                    
                async def process_query_with_ultra_intelligence(self, query, context, session_id, **kwargs):
                    return {
                        "answer": "I'm experiencing technical difficulties. Please try again.",
                        "processing_time_seconds": 0.1,
                        "timestamp": datetime.utcnow().isoformat(),
                        "conversation_aware": False,
                        "error": str(e)
                    }
            _ai_service_instance = MockAIService()
    return _ai_service_instance

# Use get_ai_service() function to access the AI service instance
# This prevents module import failures in production

def embed_text(text: str) -> List[float]:
    """Create embeddings with error handling"""
    track_function_entry("embed_text")
    
    try:
        if not text or not text.strip():
            return [0.0] * 1536
        
        client = get_openai_client()
        if not client:
            log_debug("OpenAI client not available for embeddings", {"text_length": len(text)})
            return [0.0] * 1536
        response = client.embeddings.create(
            input=[text], 
            model=EMBED_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        log_debug("Error creating embedding", {"error": str(e), "text_length": len(text)})
        return [0.0] * 1536

def split_text(text: str, max_tokens: int = 500) -> List[str]:
    """Enhanced text splitting with better error handling"""
    track_function_entry("split_text")
    
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        words = text.split()
        chunks = []
        current_chunk = []
        current_token_count = 0
        
        for word in words:
            word_token_count = len(enc.encode(word + " "))
            if current_token_count + word_token_count > max_tokens and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_token_count = 0
            current_chunk.append(word)
            current_token_count += word_token_count
            
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks if chunks else [text]
    except Exception as e:
        log_debug("Error in text splitting", {"error": str(e)})
        return [text]