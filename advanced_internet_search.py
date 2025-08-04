#!/usr/bin/env python3
"""
Advanced Internet Search Service for Clair
Multi-source web search with intelligent content extraction and synthesis
"""

import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urljoin, urlparse
from dataclasses import dataclass
import hashlib
from core import log_debug, track_function_entry

@dataclass
class SearchResult:
    """Individual search result from web sources"""
    title: str
    url: str
    snippet: str
    content: str
    source_domain: str
    relevance_score: float
    recency_score: float
    reliability_score: float
    metadata: Dict[str, Any]

class AdvancedInternetSearchService:
    """Multi-source internet search with intelligent content synthesis"""
    
    def __init__(self):
        self.search_engines = {
            "duckduckgo": "https://api.duckduckgo.com/",
            "serpapi": "https://serpapi.com/search",  # Requires API key
        }
        
        # Trusted financial information sources
        self.trusted_financial_sources = {
            "investopedia.com": 0.95,
            "nerdwallet.com": 0.90,
            "fool.com": 0.85,
            "bankrate.com": 0.90,
            "sec.gov": 0.98,
            "irs.gov": 0.98,
            "consumerreports.org": 0.88,
            "forbes.com": 0.85,
            "wsj.com": 0.90,
            "bloomberg.com": 0.88
        }
        
        # Life insurance specific sources
        self.insurance_sources = {
            "iii.org": 0.95,  # Insurance Information Institute
            "naic.org": 0.93,  # National Association of Insurance Commissioners
            "actuary.org": 0.90,
            "limra.com": 0.88,
            "lifehappens.org": 0.85
        }
        
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        self.max_results_per_source = 5
        self.request_timeout = 10
    
    async def search_multiple_sources(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search multiple sources and synthesize results"""
        track_function_entry("search_multiple_sources")
        
        # Check cache first
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.utcnow() - cache_entry["timestamp"] < timedelta(seconds=self.cache_ttl):
                log_debug("Using cached search results", {"query": query})
                return cache_entry["results"]
        
        search_tasks = []
        
        # Create search tasks for different approaches
        search_tasks.extend([
            self._search_duckduckgo(query),
            self._search_financial_sites(query),
            self._search_insurance_sites(query),
            self._search_government_sources(query)
        ])
        
        try:
            # Execute searches in parallel
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine and process results
            all_results = []
            for result_set in search_results:
                if isinstance(result_set, list):
                    all_results.extend(result_set)
            
            # Rank and filter results
            ranked_results = self._rank_search_results(all_results, query)
            top_results = ranked_results[:max_results]
            
            # Synthesize content
            synthesized_content = await self._synthesize_search_content(top_results, query)
            
            final_result = {
                "content": synthesized_content,
                "sources": [{"title": r.title, "url": r.url, "domain": r.source_domain} for r in top_results],
                "relevance_score": sum(r.relevance_score for r in top_results) / len(top_results) if top_results else 0.0,
                "total_sources": len(top_results),
                "search_metadata": {
                    "query": query,
                    "search_time": datetime.utcnow().isoformat(),
                    "sources_searched": len(search_tasks),
                    "results_found": len(all_results)
                }
            }
            
            # Cache results
            self.cache[cache_key] = {
                "results": final_result,
                "timestamp": datetime.utcnow()
            }
            
            log_debug("Multi-source search completed", {
                "query": query,
                "total_results": len(all_results),
                "top_results": len(top_results),
                "avg_relevance": final_result["relevance_score"]
            })
            
            return final_result
            
        except Exception as e:
            log_debug("Multi-source search failed", {"error": str(e)})
            return {
                "content": f"I encountered an issue searching for current information about: {query}. I'll provide guidance based on my knowledge base.",
                "sources": [],
                "relevance_score": 0.0,
                "total_sources": 0,
                "error": str(e)
            }
    
    async def _search_duckduckgo(self, query: str) -> List[SearchResult]:
        """Search using DuckDuckGo Instant Answer API"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as session:
                params = {
                    "q": query + " life insurance financial planning",
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1"
                }
                
                async with session.get(self.search_engines["duckduckgo"], params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_duckduckgo_results(data, query)
        except Exception as e:
            log_debug("DuckDuckGo search failed", {"error": str(e)})
        
        return []
    
    async def _search_financial_sites(self, query: str) -> List[SearchResult]:
        """Search specific financial information sites"""
        results = []
        
        # Search key financial sites directly
        for domain, reliability in self.trusted_financial_sources.items():
            site_results = await self._search_specific_site(query, domain, reliability)
            results.extend(site_results)
        
        return results
    
    async def _search_insurance_sites(self, query: str) -> List[SearchResult]:
        """Search insurance-specific authoritative sources"""
        results = []
        
        for domain, reliability in self.insurance_sources.items():
            site_results = await self._search_specific_site(query, domain, reliability)
            results.extend(site_results)
        
        return results
    
    async def _search_government_sources(self, query: str) -> List[SearchResult]:
        """Search government and regulatory sources"""
        gov_sources = {
            "sec.gov": 0.98,
            "irs.gov": 0.98,
            "treasury.gov": 0.95,
            "consumerfinance.gov": 0.93
        }
        
        results = []
        for domain, reliability in gov_sources.items():
            site_results = await self._search_specific_site(query, domain, reliability)
            results.extend(site_results)
        
        return results
    
    async def _search_specific_site(self, query: str, domain: str, reliability: float) -> List[SearchResult]:
        """Search a specific website using site-specific search"""
        try:
            # Use Google-style site search
            search_query = f"site:{domain} {query}"
            
            # Simulate web search results (in production, use actual search API)
            # This is a placeholder for demonstration
            results = []
            
            # Create mock results for demonstration
            if "investopedia.com" in domain:
                results.append(SearchResult(
                    title=f"Life Insurance Guide - {query}",
                    url=f"https://{domain}/life-insurance-guide",
                    snippet=f"Comprehensive guide to {query} and life insurance planning...",
                    content=f"Detailed information about {query} from Investopedia's financial experts...",
                    source_domain=domain,
                    relevance_score=0.85,
                    recency_score=0.8,
                    reliability_score=reliability,
                    metadata={"source_type": "financial_education"}
                ))
            
            return results[:2]  # Limit results per site
            
        except Exception as e:
            log_debug(f"Site search failed for {domain}", {"error": str(e)})
            return []
    
    def _parse_duckduckgo_results(self, data: Dict[str, Any], query: str) -> List[SearchResult]:
        """Parse DuckDuckGo API response"""
        results = []
        
        # Process abstract (if available)
        if data.get("Abstract"):
            results.append(SearchResult(
                title="DuckDuckGo Instant Answer",
                url=data.get("AbstractURL", ""),
                snippet=data.get("Abstract", ""),
                content=data.get("Abstract", ""),
                source_domain="duckduckgo.com",
                relevance_score=0.7,
                recency_score=0.6,
                reliability_score=0.75,
                metadata={"type": "instant_answer"}
            ))
        
        # Process related topics
        for topic in data.get("RelatedTopics", [])[:3]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(SearchResult(
                    title=topic.get("Text", "")[:100],
                    url=topic.get("FirstURL", ""),
                    snippet=topic.get("Text", ""),
                    content=topic.get("Text", ""),
                    source_domain=self._extract_domain(topic.get("FirstURL", "")),
                    relevance_score=0.6,
                    recency_score=0.5,
                    reliability_score=0.7,
                    metadata={"type": "related_topic"}
                ))
        
        return results
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urlparse(url).netloc
        except:
            return "unknown"
    
    def _rank_search_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Rank search results by relevance, reliability, and recency"""
        def calculate_score(result: SearchResult) -> float:
            # Base scoring
            score = (
                result.relevance_score * 0.4 +
                result.reliability_score * 0.4 +
                result.recency_score * 0.2
            )
            
            # Domain authority bonus
            domain = result.source_domain.lower()
            if any(trusted in domain for trusted in self.trusted_financial_sources.keys()):
                score += 0.1
            if any(insurance in domain for insurance in self.insurance_sources.keys()):
                score += 0.15
            
            # Content quality indicators
            if len(result.content) > 200:
                score += 0.05
            if query.lower() in result.content.lower():
                score += 0.1
            
            return min(score, 1.0)
        
        # Calculate scores and sort
        for result in results:
            result.final_score = calculate_score(result)
        
        return sorted(results, key=lambda r: r.final_score, reverse=True)
    
    async def _synthesize_search_content(self, results: List[SearchResult], query: str) -> str:
        """Synthesize content from multiple search results"""
        if not results:
            return f"No current information found for: {query}"
        
        content_parts = []
        
        # Group results by reliability
        high_reliability = [r for r in results if r.reliability_score >= 0.9]
        medium_reliability = [r for r in results if 0.7 <= r.reliability_score < 0.9]
        
        # Primary content from high-reliability sources
        if high_reliability:
            content_parts.append("**Authoritative Sources:**")
            for result in high_reliability[:2]:
                content_parts.append(f"• {result.title} ({result.source_domain}): {result.snippet}")
        
        # Supporting content from medium-reliability sources
        if medium_reliability:
            content_parts.append("\n**Additional Context:**")
            for result in medium_reliability[:2]:
                content_parts.append(f"• {result.snippet} (Source: {result.source_domain})")
        
        # Add source attribution
        unique_domains = list(set(r.source_domain for r in results))
        if len(unique_domains) > 1:
            content_parts.append(f"\n**Sources consulted:** {', '.join(unique_domains[:5])}")
        
        synthesized = "\n".join(content_parts)
        
        return synthesized if synthesized else f"Limited current information available for: {query}"

# Global instance
advanced_internet_search = AdvancedInternetSearchService()