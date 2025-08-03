# AI Service with Intelligent Query Classification and Routing
# Enhanced with SOTA Life Insurance Domain Expertise

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import tiktoken
from openai import OpenAI
from shared.config.base_config import ENHANCED_INSURANCE_CONFIG, SYSTEM_PROMPTS, GPT_MODEL, MAX_TOKENS, TEMPERATURE, EMBED_MODEL
from shared.utils.core_utils import log_debug, track_function_entry, openai_client

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
            
            # Prepare user prompt
            if enhanced_context.strip():
                user_prompt = f"CONTEXT:\n---\n{enhanced_context}\n---\n\nQUESTION: {query}"
            else:
                user_prompt = f"QUESTION: {query}\n\nNote: No specific document context available. Please provide general guidance and mention that specific details should be verified with actual policy documents."
            
            log_debug("Generating AI response", {
                "intent": intent_data["intent"],
                "strategy": intent_data["strategy"],
                "entities_found": len([e for e in entities.values() if e]),
                "context_length": len(enhanced_context)
            })
            
            # Call OpenAI
            response = openai_client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
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

class IntelligentAIService:
    """Main AI service with intelligent routing and response generation"""
    
    def __init__(self):
        self.classifier = AIQueryClassifier()
        self.generator = AIResponseGenerator()
    
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

# Global AI service instance
ai_service = IntelligentAIService()

def embed_text(text: str) -> List[float]:
    """Create embeddings with error handling"""
    track_function_entry("embed_text")
    
    try:
        if not text or not text.strip():
            return [0.0] * 1536
        
        response = openai_client.embeddings.create(
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