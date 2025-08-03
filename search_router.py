# Enhanced Search Router - Advanced Document Search with Performance Optimization

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

from core import log_debug, track_function_entry, bucket, index_endpoint
from ai_service import embed_text, ai_service
from config import DEPLOYED_INDEX_ID, TOP_K, SIMILARITY_THRESHOLD, SEARCH_CONFIG, ENHANCED_INSURANCE_CONFIG
from cache_service import cache_service
from enhanced_search_service import faceted_search_engine, autocomplete_service
from performance_monitor import performance_monitor

router = APIRouter(prefix="/search", tags=["search"])

class EnhancedSearchEngine:
    """Advanced search with life insurance domain expertise"""
    
    def __init__(self):
        self.config = ENHANCED_INSURANCE_CONFIG
        self.search_config = SEARCH_CONFIG
    
    def calculate_document_relevance(self, document_path: str, entities: Dict[str, List[str]]) -> float:
        """Calculate document relevance based on entities and document type"""
        relevance_score = 1.0
        
        # Document type boost
        for doc_type, doc_config in self.config["DOCUMENT_CLASSIFICATION"].items():
            for indicator in doc_config["indicators"]:
                if indicator.lower() in document_path.lower():
                    relevance_score *= doc_config["search_boost"]
                    break
        
        # Entity-based relevance
        if entities["product_types"]:
            for product_type in entities["product_types"]:
                if product_type.replace('_', ' ') in document_path.lower():
                    relevance_score *= 1.5
        
        return min(relevance_score, 3.0)  # Cap at 3.0
    
    def enhance_search_results(self, search_results: List[Dict], entities: Dict[str, List[str]]) -> List[Dict]:
        """Enhance search results with domain-specific scoring"""
        enhanced_results = []
        
        for result in search_results:
            # Calculate enhanced relevance
            document_relevance = self.calculate_document_relevance(result["document_path"], entities)
            
            # Combine scores
            final_score = result["similarity_score"] * document_relevance
            
            enhanced_result = {
                **result,
                "final_score": final_score,
                "document_relevance": document_relevance,
                "boost_factors": self._get_boost_factors(result["document_path"], entities)
            }
            enhanced_results.append(enhanced_result)
        
        # Sort by final score
        enhanced_results.sort(key=lambda x: x["final_score"], reverse=True)
        return enhanced_results
    
    def _get_boost_factors(self, document_path: str, entities: Dict[str, List[str]]) -> Dict[str, str]:
        """Get boost factors applied to a document"""
        factors = {}
        
        # Document type factors
        for doc_type, doc_config in self.config["DOCUMENT_CLASSIFICATION"].items():
            for indicator in doc_config["indicators"]:
                if indicator.lower() in document_path.lower():
                    factors["document_type"] = f"{doc_type} ({doc_config['search_boost']}x)"
                    break
        
        # Entity factors
        if entities["product_types"]:
            matching_products = [p for p in entities["product_types"] if p.replace('_', ' ') in document_path.lower()]
            if matching_products:
                factors["product_match"] = f"{', '.join(matching_products)} (1.5x)"
        
        return factors

search_engine = EnhancedSearchEngine()

@router.post("/")
async def search_documents(request: Request):
    """Advanced document search with life insurance expertise"""
    track_function_entry("search_documents")
    
    try:
        data = await request.json()
        query = data.get("query", "")
        filters = data.get("filters", [])
        limit = data.get("limit", TOP_K)
        include_entities = data.get("include_entities", True)
        
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query not provided")
        
        log_debug("Processing search query", {
            "query": query,
            "filters": filters,
            "limit": limit
        })
        
        # Extract entities if requested
        entities = {}
        if include_entities:
            entities = ai_service.classifier.extract_entities(query)
        
        # Perform vector search
        search_results = []
        if index_endpoint:
            try:
                query_vec = embed_text(query)
                
                # Prepare search parameters
                search_params = {
                    "deployed_index_id": DEPLOYED_INDEX_ID,
                    "queries": [query_vec],
                    "num_neighbors": limit * 2  # Get more results for filtering
                }
                
                # Add filters if specified
                if filters:
                    restricts = []
                    for filepath in filters:
                        restricts.append({"namespace": "filepath", "allow_list": [filepath]})
                    search_params["filter"] = restricts
                
                # Perform search
                vector_results = index_endpoint.find_neighbors(**search_params)
                
                # Process results
                if vector_results and len(vector_results) > 0:
                    neighbors = vector_results[0]
                    for neighbor in neighbors:
                        similarity_score = 1 - neighbor.distance
                        if similarity_score >= SIMILARITY_THRESHOLD:
                            # Get chunk content
                            chunk_blob = bucket.blob(neighbor.id)
                            if chunk_blob.exists():
                                chunk_text = chunk_blob.download_as_text()
                                
                                # Extract document path from chunk ID
                                document_path = "/".join(neighbor.id.split("/")[1:-1])  # Remove 'chunks/' and chunk number
                                
                                search_results.append({
                                    "chunk_id": neighbor.id,
                                    "document_path": document_path,
                                    "similarity_score": similarity_score,
                                    "content": chunk_text[:500] + "..." if len(chunk_text) > 500 else chunk_text,
                                    "full_content": chunk_text
                                })
                
            except Exception as e:
                log_debug("Vector search failed", {"error": str(e)})
        
        # Enhance results with domain expertise
        if search_results and entities:
            search_results = search_engine.enhance_search_results(search_results, entities)
        
        # Limit results
        search_results = search_results[:limit]
        
        return {
            "query": query,
            "results": search_results,
            "total_found": len(search_results),
            "entities": entities if include_entities else {},
            "search_metadata": {
                "similarity_threshold": SIMILARITY_THRESHOLD,
                "vector_search_available": index_endpoint is not None,
                "filters_applied": filters
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_debug("ERROR in search", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not perform search: {str(e)}")

@router.post("/similar")
async def find_similar_documents(request: Request):
    """Find documents similar to a given document"""
    track_function_entry("find_similar_documents")
    
    try:
        data = await request.json()
        document_path = data.get("document_path", "")
        limit = data.get("limit", 5)
        
        if not document_path:
            raise HTTPException(status_code=400, detail="Document path not provided")
        
        # Find chunks from the given document
        chunk_prefix = f"chunks/{document_path}/"
        
        if not bucket:
            raise HTTPException(status_code=500, detail="Storage not available")
        
        chunk_blobs = list(bucket.list_blobs(prefix=chunk_prefix))
        if not chunk_blobs:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Use the first chunk as the query vector
        first_chunk = chunk_blobs[0]
        chunk_text = first_chunk.download_as_text()
        
        # Perform similarity search
        query_vec = embed_text(chunk_text)
        similar_results = []
        
        if index_endpoint:
            try:
                search_params = {
                    "deployed_index_id": DEPLOYED_INDEX_ID,
                    "queries": [query_vec],
                    "num_neighbors": limit + 10  # Get extra to filter out self-matches
                }
                
                vector_results = index_endpoint.find_neighbors(**search_params)
                
                if vector_results and len(vector_results) > 0:
                    for neighbor in vector_results[0]:
                        # Skip chunks from the same document
                        neighbor_doc_path = "/".join(neighbor.id.split("/")[1:-1])
                        if neighbor_doc_path == document_path:
                            continue
                        
                        similarity_score = 1 - neighbor.distance
                        if similarity_score >= SIMILARITY_THRESHOLD:
                            similar_results.append({
                                "document_path": neighbor_doc_path,
                                "similarity_score": similarity_score,
                                "chunk_id": neighbor.id
                            })
                        
                        if len(similar_results) >= limit:
                            break
                
            except Exception as e:
                log_debug("Similar document search failed", {"error": str(e)})
        
        return {
            "source_document": document_path,
            "similar_documents": similar_results,
            "total_found": len(similar_results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_debug("ERROR finding similar documents", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not find similar documents: {str(e)}")

@router.post("/entities")
async def extract_entities_from_query(request: Request):
    """Extract entities from a search query"""
    track_function_entry("extract_entities_from_query")
    
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query not provided")
        
        # Extract entities
        entities = ai_service.classifier.extract_entities(query)
        
        # Classify intent
        intent_data = ai_service.classifier.classify_intent(query)
        
        return {
            "query": query,
            "entities": entities,
            "intent_classification": {
                "intent": intent_data["intent"],
                "confidence": intent_data["confidence"],
                "strategy": intent_data["strategy"]
            },
            "entity_summary": {
                "total_entities": sum(len(v) for v in entities.values()),
                "entity_types": [k for k, v in entities.items() if v]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_debug("ERROR extracting entities", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not extract entities: {str(e)}")

@router.get("/stats")
async def get_search_statistics():
    """Get search system statistics"""
    track_function_entry("get_search_statistics")
    
    try:
        # Get document counts by type
        document_stats = {"total_documents": 0, "by_type": {}}
        
        if bucket:
            # Count documents
            doc_blobs = list(bucket.list_blobs(prefix="documents/"))
            document_stats["total_documents"] = len(doc_blobs)
            
            # Count chunks
            chunk_blobs = list(bucket.list_blobs(prefix="chunks/"))
            document_stats["total_chunks"] = len(chunk_blobs)
            
            # Categorize by file type
            type_counts = {}
            for blob in doc_blobs:
                ext = blob.name.split('.')[-1].lower() if '.' in blob.name else 'unknown'
                type_counts[ext] = type_counts.get(ext, 0) + 1
            
            document_stats["by_type"] = type_counts
        
        return {
            "search_config": {
                "similarity_threshold": SIMILARITY_THRESHOLD,
                "top_k": TOP_K,
                "semantic_weight": SEARCH_CONFIG["semantic_weight"],
                "keyword_weight": SEARCH_CONFIG["keyword_weight"]
            },
            "document_statistics": document_stats,
            "insurance_domain": {
                "product_types": len(ENHANCED_INSURANCE_CONFIG["PRODUCT_TYPES"]),
                "intent_patterns": len(ENHANCED_INSURANCE_CONFIG["ADVANCED_INTENTS"]),
                "entity_types": len(ENHANCED_INSURANCE_CONFIG["ENTITY_RECOGNITION"])
            },
            "system_status": {
                "vector_search_available": index_endpoint is not None,
                "storage_available": bucket is not None
            }
        }
        
    except Exception as e:
        log_debug("ERROR getting search statistics", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not get search statistics: {str(e)}")

# Enhanced Search Endpoints with Performance Optimization

@router.post("/advanced")
async def advanced_faceted_search(request: Request):
    """Advanced faceted search with multiple filtering dimensions"""
    track_function_entry("advanced_faceted_search")
    
    try:
        data = await request.json()
        query = data.get("query", "")
        facet_filters = data.get("facet_filters", {})
        limit = data.get("limit", TOP_K)
        
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query not provided")
        
        # Add to autocomplete history
        autocomplete_service.add_to_history(query)
        
        # Perform faceted search
        result = await faceted_search_engine.search_with_facets(
            query=query,
            facet_filters=facet_filters,
            limit=limit
        )
        
        log_debug("Advanced search completed", {
            "query": query,
            "facets": facet_filters,
            "results": len(result.get("results", [])),
            "cache_hit": result.get("search_metrics", {}).get("cache_hit", False)
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log_debug("ERROR in advanced search", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Advanced search failed: {str(e)}")

@router.get("/autocomplete")
async def get_autocomplete_suggestions(q: str, limit: int = 5):
    """Get auto-complete suggestions for search queries"""
    track_function_entry("get_autocomplete_suggestions")
    
    try:
        if len(q.strip()) < 2:
            return {"suggestions": []}
        
        suggestions = autocomplete_service.get_suggestions(q, limit)
        
        return {
            "query": q,
            "suggestions": suggestions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_debug("ERROR getting autocomplete", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {str(e)}")

@router.get("/facets")
async def get_available_facets():
    """Get available facets for filtering"""
    track_function_entry("get_available_facets")
    
    try:
        return {
            "facets": faceted_search_engine.facets,
            "description": {
                "document_type": "Type of document (guide, application, policy, etc.)",
                "product_type": "Life insurance product type",
                "topic": "Main topic or subject area",
                "complexity": "Content complexity level",
                "audience": "Target audience for the content"
            }
        }
        
    except Exception as e:
        log_debug("ERROR getting facets", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not get facets: {str(e)}")

@router.get("/performance")
async def get_search_performance():
    """Get search performance metrics and analytics"""
    track_function_entry("get_search_performance")
    
    try:
        # Get cache statistics
        cache_stats = cache_service.get_cache_statistics()
        
        # Get performance dashboard
        performance_dashboard = performance_monitor.get_performance_dashboard(time_window_minutes=60)
        
        # Get real-time metrics
        real_time_metrics = performance_monitor.get_real_time_metrics()
        
        return {
            "cache_performance": cache_stats,
            "api_performance": performance_dashboard,
            "real_time_metrics": real_time_metrics,
            "search_optimization": {
                "faceted_search_enabled": True,
                "autocomplete_enabled": True,
                "query_optimization_enabled": True,
                "embedding_cache_enabled": True
            }
        }
        
    except Exception as e:
        log_debug("ERROR getting search performance", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not get performance metrics: {str(e)}")

@router.post("/clear_cache")
async def clear_search_cache():
    """Clear search-related caches"""
    track_function_entry("clear_search_cache")
    
    try:
        cache_service.clear_all_caches()
        
        return {
            "message": "Search caches cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_debug("ERROR clearing cache", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Could not clear cache: {str(e)}")