#!/usr/bin/env python3
"""
Response Cache for Clair AI
Simple caching mechanism to improve response times for common queries
"""

import time
import hashlib
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from core import log_debug, track_function_entry

class ResponseCache:
    """Simple response cache for improving AI response times"""
    
    def __init__(self, max_cache_size: int = 100, cache_ttl_hours: int = 24):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_cache_size = max_cache_size
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        
    def _get_cache_key(self, query: str, session_id: str = "") -> str:
        """Generate cache key from query and session"""
        # Normalize query for better cache hits
        normalized_query = query.lower().strip()
        cache_string = f"{normalized_query}:{session_id}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def get(self, query: str, session_id: str = "") -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        track_function_entry("cache_get")
        
        cache_key = self._get_cache_key(query, session_id)
        
        if cache_key not in self.cache:
            log_debug("Cache miss", {"query": query[:50], "cache_key": cache_key})
            return None
        
        cached_item = self.cache[cache_key]
        cache_time = cached_item.get("timestamp")
        
        # Check if expired
        if datetime.now() - cache_time > self.cache_ttl:
            del self.cache[cache_key]
            log_debug("Cache expired", {"query": query[:50], "cache_key": cache_key})
            return None
        
        log_debug("Cache hit", {
            "query": query[:50], 
            "cache_key": cache_key,
            "age_minutes": (datetime.now() - cache_time).total_seconds() / 60
        })
        
        return cached_item.get("response")
    
    def put(self, query: str, response: Dict[str, Any], session_id: str = "") -> None:
        """Cache response for future use"""
        track_function_entry("cache_put")
        
        # Don't cache if cache is disabled or response is empty
        if not response or not response.get("answer"):
            return
        
        cache_key = self._get_cache_key(query, session_id)
        
        # Implement simple LRU by removing oldest if at capacity
        if len(self.cache) >= self.max_cache_size:
            oldest_key = min(
                self.cache.keys(), 
                key=lambda k: self.cache[k]["timestamp"]
            )
            del self.cache[oldest_key]
            log_debug("Cache eviction", {"evicted_key": oldest_key})
        
        # Store in cache
        self.cache[cache_key] = {
            "response": response,
            "timestamp": datetime.now(),
            "query": query[:100]  # Store truncated query for debugging
        }
        
        log_debug("Response cached", {
            "query": query[:50],
            "cache_key": cache_key,
            "cache_size": len(self.cache)
        })
    
    def clear(self) -> None:
        """Clear all cached responses"""
        cache_size = len(self.cache)
        self.cache.clear()
        log_debug("Cache cleared", {"cleared_items": cache_size})
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        valid_items = 0
        expired_items = 0
        
        for item in self.cache.values():
            if now - item["timestamp"] <= self.cache_ttl:
                valid_items += 1
            else:
                expired_items += 1
        
        return {
            "total_items": len(self.cache),
            "valid_items": valid_items,
            "expired_items": expired_items,
            "max_size": self.max_cache_size,
            "ttl_hours": self.cache_ttl.total_seconds() / 3600
        }

# Global cache instance
response_cache = ResponseCache()