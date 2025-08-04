# Chat Router - AI-Powered Question Answering with Intelligent Routing
# Preserves ALL original /ask functionality while adding SOTA enhancements

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, List, Any
from datetime import datetime

# Safe imports from core with fallbacks
try:
    from core import log_debug, track_function_entry, bucket, index_endpoint
    core_available = True
except ImportError as e:
    print(f"⚠️ Core import failed in chat_router: {e}")
    core_available = False
    def log_debug(msg, data=None): print(f"[DEBUG] {msg}")
    def track_function_entry(name): pass
    bucket = None
    index_endpoint = None
# Safe imports for services
try:
    from ai_service import ai_service, embed_text
    ai_service_available = True
except ImportError as e:
    print(f"⚠️ AI service import failed: {e}")
    ai_service_available = False
    ai_service = None
    def embed_text(text): return []

try:
    from config import DEPLOYED_INDEX_ID, TOP_K, SIMILARITY_THRESHOLD, CLAIR_GREETING
    config_available = True
except ImportError as e:
    print(f"⚠️ Config import failed: {e}")
    config_available = False
    DEPLOYED_INDEX_ID = None
    TOP_K = 5
    SIMILARITY_THRESHOLD = 0.8
    CLAIR_GREETING = "Hello! I'm Clair, your AI financial advisor."

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/greeting")
async def get_clair_greeting():
    """Get Clair's greeting message"""
    track_function_entry("get_clair_greeting")
    
    return {
        "greeting": CLAIR_GREETING,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/ask")
async def enhanced_ask_question(request: Request):
    """Enhanced ask endpoint with intelligent routing - preserves original functionality"""
    track_function_entry("enhanced_ask_question")
    
    try:
        data = await request.json()
        query = data.get("query", "")
        filters = data.get("filters", [])
        
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query not provided")
        
        log_debug("Processing enhanced query", {
            "query": query,
            "filters": filters,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        relevant_chunks = []
        context_metadata = {}
        highest_score = -1.0
        
        # Try vector search if index is available (preserved from original)
        if index_endpoint:
            try:
                query_vec = embed_text(query)
                
                # Prepare search parameters
                search_params = {
                    "deployed_index_id": DEPLOYED_INDEX_ID,
                    "queries": [query_vec],
                    "num_neighbors": TOP_K
                }
                
                # Add filters if specified
                if filters:
                    restricts = []
                    for filepath in filters:
                        restricts.append({"namespace": "filepath", "allow_list": [filepath]})
                    search_params["filter"] = restricts
                
                # Perform search
                search_results = index_endpoint.find_neighbors(**search_params)
                
                # Process results (preserved original logic)
                if search_results and len(search_results) > 0:
                    neighbors = search_results[0]
                    for neighbor in neighbors:
                        similarity_score = 1 - neighbor.distance
                        if similarity_score >= SIMILARITY_THRESHOLD:
                            chunk_blob = bucket.blob(neighbor.id)
                            if chunk_blob.exists():
                                chunk_text = chunk_blob.download_as_text()
                                relevant_chunks.append(chunk_text)
                        if similarity_score > highest_score:
                            highest_score = similarity_score
                
                context_metadata = {
                    "chunks_found": len(relevant_chunks),
                    "highest_similarity": highest_score,
                    "search_method": "vector_search"
                }
                
            except Exception as e:
                log_debug("Vector search failed", {"error": str(e)})
                context_metadata = {
                    "chunks_found": 0,
                    "search_method": "vector_search_failed",
                    "error": str(e)
                }
        
        # Prepare context for AI processing
        context = "\n\n---\n\n".join(relevant_chunks) if relevant_chunks else ""
        
        # Extract session ID for conversation awareness
        session_id = data.get("session_id", f"session_{int(datetime.utcnow().timestamp())}")
        
        # Use Ultra-intelligent AI service for response generation with multi-source routing
        ai_result = await ai_service.process_query_with_ultra_intelligence(
            query=query, 
            context=context, 
            session_id=session_id,
            vertex_search_func=lambda q: {"context": context, "highest_similarity_score": highest_score, "documents_found": len(relevant_chunks)},
            filters=filters
        )
        
        # Ultra-intelligent response format with multi-source metadata
        response = {
            "answer": ai_result["answer"],
            "session_id": session_id,
            "context_used": bool(context.strip()),
            "conversation_aware": ai_result.get("conversation_aware", False),
            "ultra_intelligence_enabled": ai_result.get("ultra_intelligence_metadata", {}).get("multi_source_enabled", False),
            "query_analysis": ai_result.get("ultra_intelligence_metadata", {}).get("query_analysis", {}),
            "information_synthesis": ai_result.get("ultra_intelligence_metadata", {}).get("information_synthesis", {}),
            "sources_consulted": ai_result.get("ultra_intelligence_metadata", {}).get("sources_used", []),
            "documents_found": len(relevant_chunks),
            "highest_similarity_score": highest_score,
            "filters_applied": filters,
            
            # GPT-level capabilities
            "capabilities": ai_result.get("gpt_level_features", {
                "conversation_memory": True,
                "internet_access": True,
                "enhanced_reasoning": True,
                "domain_expertise": "life_insurance"
            }),
            "processing": {
                "processing_time": ai_result["processing_time_seconds"],
                "token_usage": ai_result.get("token_usage", {}),
                "timestamp": ai_result["timestamp"]
            },
            "metadata": context_metadata
        }
        
        log_debug("GPT-level query processing completed", {
            "session_id": session_id,
            "conversation_aware": ai_result.get("conversation_aware", False),
            "internet_enhanced": ai_result.get("internet_enhanced", False),
            "documents_used": len(relevant_chunks),
            "tokens_used": ai_result.get("token_usage", {}).get("total_tokens", 0)
        })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log_debug("ERROR in enhanced ask endpoint", {"error": str(e)})
        
        # Fallback response (preserves original behavior)
        return {
            "answer": "I'm experiencing technical difficulties generating a response. Please try again.",
            "context_used": False,
            "documents_found": 0,
            "error": str(e),
            "fallback_mode": True
        }

@router.post("/conversation/clear")
async def clear_conversation(request: Request):
    """Clear conversation history for a session"""
    track_function_entry("clear_conversation")
    
    try:
        data = await request.json()
        session_id = data.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        ai_service.conversation_manager.clear_conversation(session_id)
        
        return {
            "message": "Conversation history cleared",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_debug("Error clearing conversation", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not clear conversation: {str(e)}")

@router.get("/conversation/status/{session_id}")
async def get_conversation_status(session_id: str):
    """Get conversation status and history length"""
    track_function_entry("get_conversation_status")
    
    try:
        conversation_history = ai_service.conversation_manager.get_conversation_context(session_id)
        
        return {
            "session_id": session_id,
            "conversation_turns": len(conversation_history) // 2,
            "total_messages": len(conversation_history),
            "has_history": len(conversation_history) > 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_debug("Error getting conversation status", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not get conversation status: {str(e)}")

@router.post("/feedback")
async def submit_feedback(request: Request):
    """Collect user feedback for improving the system - preserved from original main.py"""
    track_function_entry("submit_feedback")
    
    try:
        data = await request.json()
        query = data.get("query")
        response = data.get("response")
        feedback_type = data.get("feedback_type")  # 'helpful' or 'not_helpful'
        documents_used = data.get("documents_used", 0)
        
        # Enhanced feedback with intelligence data
        intelligence_data = data.get("intelligence", {})
        
        # Log feedback for analysis (preserved original logic)
        feedback_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "response": response,
            "feedback_type": feedback_type,
            "documents_used": documents_used,
            
            # Enhanced fields
            "intelligence": intelligence_data,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "session_id": data.get("session_id", "unknown")
        }
        
        # For now, just log to console (replace with proper storage)
        log_debug("User Feedback Received", feedback_entry)
        
        # You could store this in Cloud Firestore, BigQuery, or another database
        # Example:
        # feedback_collection.add(feedback_entry)
        
        return {
            "message": "Feedback recorded successfully",
            "feedback_id": f"fb_{int(datetime.utcnow().timestamp())}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_debug("ERROR recording feedback", {"error": str(e)})
        return {
            "message": "Failed to record feedback",
            "error": str(e)
        }

@router.get("/capabilities")
async def get_chat_capabilities():
    """Get current chat system capabilities"""
    track_function_entry("get_chat_capabilities")
    
    try:
        return {
            "ai_features": {
                "intelligent_routing": True,
                "intent_classification": True,
                "entity_extraction": True,
                "domain_expertise": "life_insurance",
                "query_priority_scoring": True
            },
            "search_capabilities": {
                "vector_search": index_endpoint is not None,
                "semantic_similarity": True,
                "document_filtering": True,
                "similarity_threshold": SIMILARITY_THRESHOLD,
                "max_results": TOP_K
            },
            "supported_intents": list(ai_service.classifier.config["ADVANCED_INTENTS"].keys()),
            "supported_entities": list(ai_service.classifier.config["ENTITY_RECOGNITION"].keys()),
            "product_expertise": list(ai_service.classifier.config["PRODUCT_TYPES"].keys()),
            "response_strategies": [
                "comparative_analysis",
                "cost_analysis", 
                "needs_analysis",
                "beneficiary_guidance",
                "policy_administration",
                "tax_analysis",
                "underwriting_guidance",
                "rider_explanation"
            ],
            "system_status": {
                "vector_index_available": index_endpoint is not None,
                "storage_available": bucket is not None,
                "ai_service_ready": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_debug("ERROR getting chat capabilities", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not get capabilities: {str(e)}")

@router.post("/analyze_query")
async def analyze_query_intelligence(request: Request):
    """Analyze a query without generating a response - for debugging/analysis"""
    track_function_entry("analyze_query_intelligence")
    
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query not provided")
        
        # Classify intent
        intent_data = ai_service.classifier.classify_intent(query)
        
        # Extract entities
        entities = ai_service.classifier.extract_entities(query)
        
        # Calculate priority
        priority = ai_service.classifier.calculate_query_priority(query, intent_data)
        
        return {
            "query": query,
            "intent_analysis": {
                "primary_intent": intent_data["intent"],
                "confidence": intent_data["confidence"],
                "response_strategy": intent_data["strategy"],
                "context_requirements": intent_data["context_requirements"],
                "all_detected_intents": intent_data["all_intents"]
            },
            "entity_extraction": {
                "entities": entities,
                "total_entities": sum(len(v) for v in entities.values()),
                "entity_types_found": [k for k, v in entities.items() if v]
            },
            "priority_scoring": {
                "priority_score": priority,
                "priority_level": "high" if priority > 2.0 else "medium" if priority > 1.0 else "low"
            },
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_debug("ERROR analyzing query", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not analyze query: {str(e)}")

# Legacy endpoint for backward compatibility (maps to enhanced version)
@router.post("/legacy_ask")
async def legacy_ask_endpoint(request: Request):
    """Legacy ask endpoint for backward compatibility"""
    return await enhanced_ask_question(request)