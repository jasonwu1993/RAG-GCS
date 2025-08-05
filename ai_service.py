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
                   TOP_P, PRESENCE_PENALTY, FREQUENCY_PENALTY, REQUEST_TIMEOUT)
from core import log_debug, track_function_entry

def get_openai_client():
    """Get OpenAI client dynamically to avoid import-time dependency issues"""
    try:
        from core import openai_client
        if openai_client is None:
            # Try to initialize if not done yet
            from core import initialize_openai_client
            initialize_openai_client()
            from core import openai_client
        return openai_client
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

# Import hotkey handler
try:
    from hotkey_handler import hotkey_handler
    hotkey_handler_available = True
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
        self.classifier = AIQueryClassifier()
        self.generator = AIResponseGenerator()
        self.conversation_manager = ConversationManager()
        self.internet_service = InternetSearchService()
        self.validator = ResponseValidator()
        
        # Initialize ultra-intelligent routing system
        if intelligent_routing_available:
            self.query_intelligence = QueryIntelligenceEngine()
            self.multi_source_orchestrator = MultiSourceOrchestrator()
            self.synthesis_engine = InformationSynthesisEngine()
            self.ultra_intelligence_enabled = True
        else:
            self.ultra_intelligence_enabled = False
        
        # Initialize Clair system prompt enforcer
        self.prompt_enforcer_enabled = prompt_enforcer_available
        
        # Initialize hotkey handler - DISABLED to let GPT handle hotkeys with full context
        self.hotkey_handler_enabled = False  # Was: hotkey_handler_available
    
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
            # Determine language preference
            conversation_history = []
            if CONVERSATION_MEMORY_ENABLED:
                conversation_history = self.conversation_manager.get_conversation_context(session_id)
            
            # Check if previous conversation was in Chinese
            needs_chinese = True
            for msg in conversation_history[-6:]:  # Check last 3 exchanges
                if msg.get("role") == "user" and self._detect_english_simple(msg.get("content", "")):
                    needs_chinese = False
                    break
            
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
            
            # 7. Generate ultra-intelligent response
            client = get_openai_client()
            if not client:
                raise Exception("OpenAI client not available")
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
            
            # 8. Save conversation for natural flow
            if CONVERSATION_MEMORY_ENABLED:
                self.conversation_manager.add_exchange(session_id, query, answer)
            
            # 9. Apply Clair system prompt enforcement
            if self.prompt_enforcer_enabled:
                answer, enforcement_result = clair_prompt_enforcer.enforce_system_prompt(query, answer)
            else:
                enforcement_result = None
            
            # 10. Validate response compliance
            validation_results = self.validator.validate_response_compliance(query, answer)
            
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
        """Clean GPT-like conversation processing following OpenAI best practices"""
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
        
        # 2. Build messages array following OpenAI Chat Completions best practices
        messages = [
            {"role": "system", "content": CLAIR_SYSTEM_PROMPT_ACTIVE}
        ]
        
        # Add conversation history for context
        messages.extend(conversation_history)
        
        # 3. Add current user message with enhanced context handling
        if context.strip():
            # Context Available scenario - reference specific documents
            user_message = f"""CONTEXT FROM OFFICIAL DOCUMENTS:
{context}

CLIENT QUESTION: {query}

Please provide advice based on the specific policy information above. Reference exact provisions, rates, and terms where available."""
        else:
            # Context Limited scenario - use general knowledge with disclaimers
            user_message = f"""CLIENT QUESTION: {query}

Note: No specific policy documents are available for this query. Please provide general industry guidance and emphasize the need for document verification."""
        
        messages.append({"role": "user", "content": user_message})
        
        # 4. Generate response using optimal GPT-like parameters
        try:
            client = get_openai_client()
            if not client:
                raise Exception("OpenAI client not available")
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
            
            # 5. Save conversation for natural flow
            if CONVERSATION_MEMORY_ENABLED:
                self.conversation_manager.add_exchange(session_id, query, answer)
            
            # 6. Apply Clair system prompt enforcement
            if self.prompt_enforcer_enabled:
                answer, enforcement_result = clair_prompt_enforcer.enforce_system_prompt(query, answer)
            else:
                enforcement_result = None
            
            # 7. Validate response compliance
            validation_results = self.validator.validate_response_compliance(query, answer)
            
            # 8. Return enhanced result with compliance validation
            result = {
                "answer": answer,
                "query": query,
                "session_id": session_id,
                "conversation_aware": len(conversation_history) > 0,
                "context_used": bool(context.strip()),
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
            log_debug("Error in conversation processing", {"error": str(e)})
            # Clean fallback response
            return {
                "answer": "I apologize, but I'm experiencing a technical issue. Could you please try asking your question again?",
                "query": query,
                "session_id": session_id,
                "conversation_aware": False,
                "context_used": False,
                "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global AI service instance
ai_service = IntelligentAIService()

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