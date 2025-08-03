# Advanced Caching Service for RAG System
# Implements multi-layer caching for search results, embeddings, and document data

import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
import asyncio
from threading import Lock
import pickle
import gzip

from core import log_debug, track_function_entry

class LRUCache:
    """Thread-safe LRU Cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = Lock()
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        return time.time() - self.timestamps[key] > self.default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            if key in self.cache and not self._is_expired(key):
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]
            elif key in self.cache:
                # Remove expired item
                del self.cache[key]
                del self.timestamps[key]
            return None
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Put item in cache"""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.max_size:
                    # Remove least recently used item
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    del self.timestamps[oldest_key]
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        with self.lock:
            return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            expired_count = sum(1 for key in self.cache.keys() if self._is_expired(key))
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "expired_entries": expired_count,
                "memory_efficiency": (len(self.cache) - expired_count) / self.max_size if self.max_size > 0 else 0
            }

class AdvancedCacheService:
    """Multi-layer caching service for RAG system"""
    
    def __init__(self):
        # Different cache layers with different TTLs
        self.search_results_cache = LRUCache(max_size=500, default_ttl=1800)  # 30 minutes
        self.embedding_cache = LRUCache(max_size=2000, default_ttl=7200)      # 2 hours
        self.document_metadata_cache = LRUCache(max_size=1000, default_ttl=3600)  # 1 hour
        self.entity_extraction_cache = LRUCache(max_size=800, default_ttl=1800)   # 30 minutes
        self.frequent_queries_cache = LRUCache(max_size=200, default_ttl=86400)   # 24 hours
        
        # Cache statistics
        self.hit_count = 0
        self.miss_count = 0
        self.lock = Lock()
        
        log_debug("Advanced cache service initialized")
    
    def _generate_cache_key(self, prefix: str, data: Any) -> str:
        """Generate deterministic cache key"""
        if isinstance(data, dict):
            # Sort dict for consistent hashing
            data_str = json.dumps(data, sort_keys=True)
        elif isinstance(data, list):
            data_str = json.dumps(sorted(data) if all(isinstance(x, str) for x in data) else data)
        else:
            data_str = str(data)
        
        hash_obj = hashlib.md5(data_str.encode('utf-8'))
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get_search_results(self, query: str, filters: List[str], limit: int) -> Optional[Dict[str, Any]]:
        """Get cached search results"""
        cache_key = self._generate_cache_key("search", {
            "query": query.lower().strip(),
            "filters": sorted(filters),
            "limit": limit
        })
        
        result = self.search_results_cache.get(cache_key)
        if result:
            with self.lock:
                self.hit_count += 1
            log_debug("Search cache hit", {"query": query[:50], "key": cache_key[:16]})
        else:
            with self.lock:
                self.miss_count += 1
        
        return result
    
    def cache_search_results(self, query: str, filters: List[str], limit: int, results: Dict[str, Any]) -> None:
        """Cache search results"""
        cache_key = self._generate_cache_key("search", {
            "query": query.lower().strip(),
            "filters": sorted(filters),
            "limit": limit
        })
        
        # Add cache metadata
        cached_data = {
            **results,
            "cached_at": datetime.utcnow().isoformat(),
            "cache_key": cache_key
        }
        
        self.search_results_cache.put(cache_key, cached_data)
        log_debug("Search results cached", {"query": query[:50], "results_count": len(results.get("results", []))})
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding"""
        cache_key = self._generate_cache_key("embed", text.strip().lower())
        
        result = self.embedding_cache.get(cache_key)
        if result:
            with self.lock:
                self.hit_count += 1
            log_debug("Embedding cache hit", {"text": text[:50]})
        else:
            with self.lock:
                self.miss_count += 1
        
        return result
    
    def cache_embedding(self, text: str, embedding: List[float]) -> None:
        """Cache embedding"""
        cache_key = self._generate_cache_key("embed", text.strip().lower())
        self.embedding_cache.put(cache_key, embedding)
        log_debug("Embedding cached", {"text": text[:50], "vector_dim": len(embedding)})
    
    def get_document_metadata(self, document_path: str) -> Optional[Dict[str, Any]]:
        """Get cached document metadata"""
        cache_key = self._generate_cache_key("doc_meta", document_path)
        return self.document_metadata_cache.get(cache_key)
    
    def cache_document_metadata(self, document_path: str, metadata: Dict[str, Any]) -> None:
        """Cache document metadata"""
        cache_key = self._generate_cache_key("doc_meta", document_path)
        self.document_metadata_cache.put(cache_key, metadata)
        log_debug("Document metadata cached", {"path": document_path})
    
    def get_entity_extraction(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached entity extraction"""
        cache_key = self._generate_cache_key("entities", query.strip().lower())
        
        result = self.entity_extraction_cache.get(cache_key)
        if result:
            with self.lock:
                self.hit_count += 1
        else:
            with self.lock:
                self.miss_count += 1
        
        return result
    
    def cache_entity_extraction(self, query: str, entities: Dict[str, Any]) -> None:
        """Cache entity extraction results"""
        cache_key = self._generate_cache_key("entities", query.strip().lower())
        self.entity_extraction_cache.put(cache_key, entities)
        log_debug("Entity extraction cached", {"query": query[:50], "entities": len(entities)})
    
    def get_frequent_query(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached frequent query result"""
        return self.frequent_queries_cache.get(f"freq:{query_hash}")
    
    def cache_frequent_query(self, query_hash: str, result: Dict[str, Any]) -> None:
        """Cache frequent query with extended TTL"""
        self.frequent_queries_cache.put(f"freq:{query_hash}", result, ttl=86400)  # 24 hours
    
    def invalidate_document(self, document_path: str) -> None:
        """Invalidate all caches related to a document"""
        # Clear document metadata
        cache_key = self._generate_cache_key("doc_meta", document_path)
        self.document_metadata_cache.cache.pop(cache_key, None)
        
        # Clear search results that might include this document
        # Note: This is a simplified approach. In production, you might want more sophisticated invalidation
        self.search_results_cache.clear()
        
        log_debug("Document cache invalidated", {"document": document_path})
    
    def warm_up_cache(self, common_queries: List[str]) -> None:
        """Pre-warm cache with common queries"""
        log_debug("Starting cache warm-up", {"queries": len(common_queries)})
        # This would be called during startup with frequently used queries
        for query in common_queries:
            # Pre-generate cache keys for faster lookup
            self._generate_cache_key("search", {"query": query.lower().strip(), "filters": [], "limit": 3})
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "performance": {
                    "hit_count": self.hit_count,
                    "miss_count": self.miss_count,
                    "hit_rate_percent": round(hit_rate, 2),
                    "total_requests": total_requests
                },
                "cache_layers": {
                    "search_results": self.search_results_cache.get_stats(),
                    "embeddings": self.embedding_cache.get_stats(),
                    "document_metadata": self.document_metadata_cache.get_stats(),
                    "entity_extraction": self.entity_extraction_cache.get_stats(),
                    "frequent_queries": self.frequent_queries_cache.get_stats()
                },
                "memory_usage": {
                    "total_entries": (
                        self.search_results_cache.size() +
                        self.embedding_cache.size() +
                        self.document_metadata_cache.size() +
                        self.entity_extraction_cache.size() +
                        self.frequent_queries_cache.size()
                    )
                }
            }
    
    def clear_all_caches(self) -> None:
        """Clear all cache layers"""
        self.search_results_cache.clear()
        self.embedding_cache.clear()
        self.document_metadata_cache.clear()
        self.entity_extraction_cache.clear()
        self.frequent_queries_cache.clear()
        
        with self.lock:
            self.hit_count = 0
            self.miss_count = 0
        
        log_debug("All caches cleared")

# Global cache service instance
cache_service = AdvancedCacheService()

# Cache warming queries for life insurance domain
COMMON_LIFE_INSURANCE_QUERIES = [
    "term life insurance",
    "whole life insurance",
    "universal life insurance",
    "life insurance premium",
    "death benefit",
    "beneficiary designation",
    "cash value",
    "policy loan",
    "conversion option",
    "underwriting process"
]

def initialize_cache_service():
    """Initialize and warm up the cache service"""
    cache_service.warm_up_cache(COMMON_LIFE_INSURANCE_QUERIES)
    log_debug("Cache service initialized and warmed up")