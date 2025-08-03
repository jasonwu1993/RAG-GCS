# Chat Router - AI-Powered Question Answering with Intelligent Routing
# Preserves ALL original /ask functionality while adding SOTA enhancements

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, List, Any
from datetime import datetime

from core import log_debug, track_function_entry, bucket, index_endpoint
from ai_service import ai_service, embed_text
from config import DEPLOYED_INDEX_ID, TOP_K, SIMILARITY_THRESHOLD, CLAIR_GREETING

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
        
        # Use intelligent AI service for response generation
        ai_result = ai_service.process_query(query, context, filters)
        
        # Combine original response format with enhanced data
        response = {
            "answer": ai_result["answer"],
            "context_used": bool(context.strip()),
            "documents_found": len(relevant_chunks),
            "highest_similarity_score": highest_score,
            "filters_applied": filters,
            
            # Enhanced SOTA features
            "intelligence": {
                "intent": ai_result["intent"],
                "confidence": ai_result["confidence"],
                "strategy": ai_result["strategy"],
                "entities": ai_result["entities"],
                "priority": ai_result["priority"]
            },
            "processing": {
                "processing_time": ai_result["processing_time_seconds"],
                "token_usage": ai_result.get("token_usage", {}),
                "timestamp": ai_result["timestamp"]
            },
            "metadata": context_metadata
        }
        
        log_debug("Enhanced query processing completed", {
            "intent": ai_result["intent"],
            "confidence": ai_result["confidence"],
            "documents_used": len(relevant_chunks)
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