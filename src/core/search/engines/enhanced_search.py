# Enhanced Search Service with Advanced Features
# Implements faceted search, auto-complete, query suggestions, and performance optimization

import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from dataclasses import dataclass

from core import log_debug, track_function_entry, bucket, index_endpoint
from cache_service import cache_service
from ai_service import embed_text, ai_service
from config import DEPLOYED_INDEX_ID, TOP_K, SIMILARITY_THRESHOLD, ENHANCED_INSURANCE_CONFIG

@dataclass
class SearchMetrics:
    """Search performance metrics"""
    query_time: float
    cache_hit: bool
    results_count: int
    embedding_time: float
    vector_search_time: float
    post_processing_time: float
    total_chunks_searched: int

class QueryOptimizer:
    """Optimize and preprocess search queries"""
    
    def __init__(self):
        self.stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 
            'to', 'was', 'will', 'with', 'about', 'what', 'how', 'when', 'where'
        }
        self.insurance_synonyms = {
            'insurance': ['coverage', 'policy', 'protection'],
            'premium': ['cost', 'payment', 'price', 'rate'],
            'benefit': ['payout', 'proceeds', 'amount'],
            'death': ['mortality', 'final'],
            'cash': ['savings', 'accumulation', 'value']
        }
    
    def optimize_query(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Optimize query for better search results"""
        track_function_entry("optimize_query")
        
        original_query = query
        query = query.lower().strip()
        
        # Extract metadata
        metadata = {
            "original_length": len(original_query),
            "query_type": self._detect_query_type(query),
            "key_terms": self._extract_key_terms(query),
            "complexity": self._calculate_complexity(query)
        }
        
        # Apply optimizations
        optimized_query = self._expand_synonyms(query)
        optimized_query = self._handle_negations(optimized_query)
        optimized_query = self._boost_important_terms(optimized_query)
        
        log_debug("Query optimized", {
            "original": original_query,
            "optimized": optimized_query,
            "metadata": metadata
        })
        
        return optimized_query, metadata
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of query"""
        comparison_patterns = ['vs', 'versus', 'compare', 'difference', 'better']
        cost_patterns = ['cost', 'price', 'premium', 'how much', 'expensive']
        explanation_patterns = ['what is', 'how does', 'explain', 'define']
        
        if any(pattern in query for pattern in comparison_patterns):
            return "comparison"
        elif any(pattern in query for pattern in cost_patterns):
            return "cost_inquiry"
        elif any(pattern in query for pattern in explanation_patterns):
            return "explanation"
        else:
            return "general"
    
    def _extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from query"""
        words = re.findall(r'\b\w+\b', query)
        key_terms = [word for word in words if word not in self.stopwords and len(word) > 2]
        return key_terms[:5]  # Top 5 key terms
    
    def _calculate_complexity(self, query: str) -> float:
        """Calculate query complexity score"""
        word_count = len(query.split())
        unique_terms = len(set(query.split()))
        has_operators = any(op in query for op in ['and', 'or', 'not', '"'])
        
        complexity = (word_count * 0.3 + unique_terms * 0.5 + (2 if has_operators else 0)) / 10
        return min(complexity, 1.0)
    
    def _expand_synonyms(self, query: str) -> str:
        """Expand query with domain-specific synonyms"""
        for term, synonyms in self.insurance_synonyms.items():
            if term in query:
                # Add primary synonym for better matching
                primary_synonym = synonyms[0]
                if primary_synonym not in query:
                    query += f" {primary_synonym}"
        return query
    
    def _handle_negations(self, query: str) -> str:
        """Handle negation patterns"""
        negation_patterns = ['not', 'without', 'exclude', 'except']
        for pattern in negation_patterns:
            if pattern in query:
                # Mark negated terms for special handling
                query = query.replace(pattern, f"[NEG]{pattern}[/NEG]")
        return query
    
    def _boost_important_terms(self, query: str) -> str:
        """Boost important life insurance terms"""
        important_terms = ['term', 'whole', 'universal', 'variable', 'indexed', 'premium', 'death benefit']
        for term in important_terms:
            if term in query:
                query = query.replace(term, f"{term} {term}")  # Duplicate for emphasis
        return query

class FacetedSearchEngine:
    """Advanced faceted search with multiple filtering dimensions"""
    
    def __init__(self):
        self.facets = {
            "document_type": ["guide", "application", "policy", "brochure", "form"],
            "product_type": list(ENHANCED_INSURANCE_CONFIG["PRODUCT_TYPES"].keys()),
            "topic": ["premium", "benefit", "underwriting", "claims", "conversion"],
            "complexity": ["basic", "intermediate", "advanced"],
            "audience": ["consumer", "agent", "underwriter", "claims"]
        }
        self.query_optimizer = QueryOptimizer()
    
    async def search_with_facets(self, query: str, facet_filters: Dict[str, List[str]] = None, 
                                limit: int = TOP_K) -> Dict[str, Any]:
        """Perform faceted search with multiple dimensions"""
        track_function_entry("search_with_facets")
        start_time = datetime.now()
        
        # Check cache first
        cache_key_data = {
            "query": query,
            "facets": facet_filters or {},
            "limit": limit
        }
        
        cached_result = cache_service.get_search_results(query, [], limit)
        if cached_result and not facet_filters:  # Use cache for simple queries
            cached_result["cache_hit"] = True
            return cached_result
        
        # Optimize query
        optimized_query, query_metadata = self.query_optimizer.optimize_query(query)
        
        # Get entity extraction (with caching)
        entities = cache_service.get_entity_extraction(query)
        if not entities:
            entities = ai_service.classifier.extract_entities(query)
            cache_service.cache_entity_extraction(query, entities)
        
        # Perform vector search
        search_results = []
        embedding_time = 0
        vector_search_time = 0
        
        if index_endpoint:
            # Get embedding (with caching)
            embedding_start = datetime.now()
            query_vec = cache_service.get_embedding(optimized_query)
            if not query_vec:
                query_vec = embed_text(optimized_query)
                cache_service.cache_embedding(optimized_query, query_vec)
            embedding_time = (datetime.now() - embedding_start).total_seconds()
            
            # Vector search
            vector_start = datetime.now()
            search_results = await self._perform_vector_search(query_vec, limit * 3)  # Get more for filtering
            vector_search_time = (datetime.now() - vector_start).total_seconds()
        
        # Apply facet filters
        if facet_filters:
            search_results = self._apply_facet_filters(search_results, facet_filters)
        
        # Post-process and enhance results
        post_process_start = datetime.now()
        enhanced_results = self._enhance_search_results(search_results, entities, query_metadata)
        enhanced_results = enhanced_results[:limit]
        
        # Calculate facet counts
        facet_counts = self._calculate_facet_counts(search_results)
        post_processing_time = (datetime.now() - post_process_start).total_seconds()
        
        # Create metrics
        total_time = (datetime.now() - start_time).total_seconds()
        metrics = SearchMetrics(
            query_time=total_time,
            cache_hit=False,
            results_count=len(enhanced_results),
            embedding_time=embedding_time,
            vector_search_time=vector_search_time,
            post_processing_time=post_processing_time,
            total_chunks_searched=len(search_results)
        )
        
        result = {
            "query": query,
            "optimized_query": optimized_query,
            "results": enhanced_results,
            "facets": facet_counts,
            "entities": entities,
            "query_metadata": query_metadata,
            "search_metrics": {
                "total_time_ms": round(total_time * 1000, 2),
                "cache_hit": False,
                "results_found": len(enhanced_results),
                "total_chunks_searched": len(search_results),
                "performance_breakdown": {
                    "embedding_time_ms": round(embedding_time * 1000, 2),
                    "vector_search_time_ms": round(vector_search_time * 1000, 2),
                    "post_processing_time_ms": round(post_processing_time * 1000, 2)
                }
            }
        }
        
        # Cache results for simple queries
        if not facet_filters:
            cache_service.cache_search_results(query, [], limit, result)
        
        log_debug("Faceted search completed", {
            "query": query,
            "results": len(enhanced_results),
            "total_time_ms": round(total_time * 1000, 2),
            "cache_hit": False
        })
        
        return result
    
    async def _perform_vector_search(self, query_vec: List[float], limit: int) -> List[Dict[str, Any]]:
        """Perform vector search with error handling"""
        try:
            search_params = {
                "deployed_index_id": DEPLOYED_INDEX_ID,
                "queries": [query_vec],
                "num_neighbors": limit
            }
            
            vector_results = index_endpoint.find_neighbors(**search_params)
            
            search_results = []
            if vector_results and len(vector_results) > 0:
                neighbors = vector_results[0]
                for neighbor in neighbors:
                    similarity_score = 1 - neighbor.distance
                    if similarity_score >= SIMILARITY_THRESHOLD:
                        # Get chunk content
                        chunk_blob = bucket.blob(neighbor.id)
                        if chunk_blob.exists():
                            chunk_text = chunk_blob.download_as_text()
                            document_path = "/".join(neighbor.id.split("/")[1:-1])
                            
                            search_results.append({
                                "chunk_id": neighbor.id,
                                "document_path": document_path,
                                "similarity_score": similarity_score,
                                "content": chunk_text[:500] + "..." if len(chunk_text) > 500 else chunk_text,
                                "full_content": chunk_text,
                                "facet_data": self._extract_facet_data(document_path, chunk_text)
                            })
            
            return search_results
            
        except Exception as e:
            log_debug("Vector search failed", {"error": str(e)})
            return []
    
    def _extract_facet_data(self, document_path: str, content: str) -> Dict[str, str]:
        """Extract facet information from document path and content"""
        facet_data = {}
        
        # Document type
        path_lower = document_path.lower()
        for doc_type in self.facets["document_type"]:
            if doc_type in path_lower:
                facet_data["document_type"] = doc_type
                break
        
        # Product type
        for product_type in self.facets["product_type"]:
            product_variants = ENHANCED_INSURANCE_CONFIG["PRODUCT_TYPES"][product_type]["names"]
            if any(variant.lower() in content.lower() for variant in product_variants):
                facet_data["product_type"] = product_type
                break
        
        # Topic
        content_lower = content.lower()
        for topic in self.facets["topic"]:
            if topic in content_lower:
                facet_data["topic"] = topic
                break
        
        # Complexity (based on document structure and content)
        if any(term in content_lower for term in ["overview", "introduction", "basic"]):
            facet_data["complexity"] = "basic"
        elif any(term in content_lower for term in ["detailed", "comprehensive", "advanced"]):
            facet_data["complexity"] = "advanced"
        else:
            facet_data["complexity"] = "intermediate"
        
        return facet_data
    
    def _apply_facet_filters(self, results: List[Dict[str, Any]], 
                            facet_filters: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Apply facet filters to search results"""
        filtered_results = []
        
        for result in results:
            facet_data = result.get("facet_data", {})
            matches_all_filters = True
            
            for facet_name, filter_values in facet_filters.items():
                if facet_name in facet_data:
                    if facet_data[facet_name] not in filter_values:
                        matches_all_filters = False
                        break
                else:
                    # If facet data is missing, exclude by default
                    matches_all_filters = False
                    break
            
            if matches_all_filters:
                filtered_results.append(result)
        
        return filtered_results
    
    def _enhance_search_results(self, results: List[Dict[str, Any]], entities: Dict[str, Any], 
                               query_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhance search results with additional scoring and metadata"""
        enhanced_results = []
        
        for result in results:
            # Calculate enhanced relevance score
            relevance_multiplier = 1.0
            
            # Boost based on query type
            if query_metadata["query_type"] == "comparison":
                if any(term in result["content"].lower() for term in ["vs", "compare", "difference"]):
                    relevance_multiplier *= 1.3
            
            # Boost based on key terms
            key_terms_found = sum(1 for term in query_metadata["key_terms"] 
                                 if term in result["content"].lower())
            relevance_multiplier *= (1 + key_terms_found * 0.1)
            
            # Calculate final score
            final_score = result["similarity_score"] * relevance_multiplier
            
            enhanced_result = {
                **result,
                "final_score": final_score,
                "relevance_multiplier": relevance_multiplier,
                "key_terms_matched": key_terms_found,
                "boost_factors": self._get_boost_factors(result, entities, query_metadata)
            }
            
            enhanced_results.append(enhanced_result)
        
        # Sort by final score
        enhanced_results.sort(key=lambda x: x["final_score"], reverse=True)
        return enhanced_results
    
    def _get_boost_factors(self, result: Dict[str, Any], entities: Dict[str, Any], 
                          query_metadata: Dict[str, Any]) -> List[str]:
        """Get list of boost factors applied"""
        factors = []
        
        # Entity matches
        if entities.get("product_types"):
            for product in entities["product_types"]:
                if product.replace('_', ' ') in result["content"].lower():
                    factors.append(f"Product match: {product}")
        
        # Query type boost
        if query_metadata["query_type"] != "general":
            factors.append(f"Query type: {query_metadata['query_type']}")
        
        # Document type boost
        facet_data = result.get("facet_data", {})
        if facet_data.get("document_type"):
            factors.append(f"Document type: {facet_data['document_type']}")
        
        return factors
    
    def _calculate_facet_counts(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """Calculate facet counts for filtering UI"""
        facet_counts = {}
        
        for facet_name in self.facets:
            facet_counts[facet_name] = defaultdict(int)
        
        for result in results:
            facet_data = result.get("facet_data", {})
            for facet_name, facet_value in facet_data.items():
                if facet_name in facet_counts:
                    facet_counts[facet_name][facet_value] += 1
        
        # Convert defaultdict to regular dict
        return {facet: dict(counts) for facet, counts in facet_counts.items()}

class AutoCompleteService:
    """Auto-complete and query suggestion service"""
    
    def __init__(self):
        self.common_terms = set()
        self.query_history = []
        self.max_history = 1000
        self._build_term_index()
    
    def _build_term_index(self):
        """Build index of common terms"""
        # Life insurance domain terms
        insurance_terms = [
            "term life insurance", "whole life insurance", "universal life insurance",
            "variable life insurance", "indexed universal life", "death benefit",
            "cash value", "premium payment", "beneficiary designation", "policy loan",
            "conversion option", "underwriting process", "medical exam", "suicide clause",
            "contestability period", "grace period", "lapse", "reinstatement"
        ]
        
        for term in insurance_terms:
            words = term.split()
            for i in range(len(words)):
                for j in range(i + 1, len(words) + 1):
                    phrase = " ".join(words[i:j])
                    self.common_terms.add(phrase.lower())
    
    def get_suggestions(self, partial_query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get auto-complete suggestions"""
        track_function_entry("get_suggestions")
        
        partial_lower = partial_query.lower().strip()
        suggestions = []
        
        # Find matching terms
        matching_terms = [term for term in self.common_terms 
                         if term.startswith(partial_lower)]
        
        # Sort by relevance (length and frequency)
        matching_terms.sort(key=lambda x: (len(x), -self._get_term_frequency(x)))
        
        for term in matching_terms[:limit]:
            suggestions.append({
                "text": term,
                "type": "term",
                "confidence": self._calculate_suggestion_confidence(term, partial_query)
            })
        
        # Add query history matches
        history_matches = [q for q in self.query_history 
                          if partial_lower in q.lower() and q.lower() != partial_lower]
        
        for query in history_matches[:limit - len(suggestions)]:
            suggestions.append({
                "text": query,
                "type": "history",
                "confidence": 0.8
            })
        
        log_debug("Auto-complete suggestions generated", {
            "partial_query": partial_query,
            "suggestions_count": len(suggestions)
        })
        
        return suggestions
    
    def add_to_history(self, query: str):
        """Add query to history for future suggestions"""
        if query and len(query.strip()) > 2:
            self.query_history.append(query.strip())
            if len(self.query_history) > self.max_history:
                self.query_history.pop(0)
    
    def _get_term_frequency(self, term: str) -> int:
        """Get frequency of term in query history"""
        return sum(1 for query in self.query_history if term in query.lower())
    
    def _calculate_suggestion_confidence(self, suggestion: str, partial_query: str) -> float:
        """Calculate confidence score for suggestion"""
        if not partial_query:
            return 0.5
        
        partial_lower = partial_query.lower()
        suggestion_lower = suggestion.lower()
        
        # Exact prefix match gets higher score
        if suggestion_lower.startswith(partial_lower):
            prefix_ratio = len(partial_lower) / len(suggestion_lower)
            return min(0.9, 0.5 + prefix_ratio * 0.4)
        
        # Contains match gets lower score
        if partial_lower in suggestion_lower:
            return 0.6
        
        return 0.3

# Global service instances
faceted_search_engine = FacetedSearchEngine()
autocomplete_service = AutoCompleteService()