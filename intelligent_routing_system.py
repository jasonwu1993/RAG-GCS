#!/usr/bin/env python3
"""
Intelligent Multi-Source Routing System for Clair
Ultra-sophisticated query analysis and information synthesis engine
"""

import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import tiktoken
from core import log_debug, track_function_entry

class InformationSource(Enum):
    """Available information sources"""
    VERTEX_DB = "vertex_database"
    INTERNET_SEARCH = "internet_search"
    KNOWLEDGE_BASE = "knowledge_base"
    HYBRID = "hybrid"

class QueryType(Enum):
    """Types of queries for intelligent routing"""
    POLICY_SPECIFIC = "policy_specific"  # Specific company policies, rates, terms
    MARKET_TRENDS = "market_trends"      # Current market conditions, rates, trends
    REGULATORY = "regulatory"            # Current regulations, compliance changes
    EDUCATIONAL = "educational"          # General insurance concepts, explanations
    COMPARATIVE = "comparative"          # Product comparisons, market analysis
    CURRENT_EVENTS = "current_events"    # Recent news, industry developments
    PERSONALIZED = "personalized"       # Individual advice, recommendations

@dataclass
class QueryAnalysis:
    """Results of intelligent query analysis"""
    query_type: QueryType
    confidence: float
    requires_current_info: bool
    requires_specific_docs: bool
    complexity_score: float
    priority_sources: List[InformationSource]
    search_strategy: str
    estimated_search_time: float

@dataclass
class SourceResult:
    """Result from a single information source"""
    source: InformationSource
    content: str
    relevance_score: float
    recency_score: float
    reliability_score: float
    metadata: Dict[str, Any]
    processing_time: float

class QueryIntelligenceEngine:
    """Ultra-advanced query analysis for intelligent source routing"""
    
    def __init__(self):
        self.enc = tiktoken.get_encoding("cl100k_base")
        
        # Advanced pattern matching for query classification
        self.query_patterns = {
            QueryType.POLICY_SPECIFIC: [
                r"premium.{0,20}rate", r"coverage.{0,20}amount", r"policy.{0,20}term",
                r"specific.{0,20}policy", r"exact.{0,20}cost", r"company.{0,20}policy",
                r"quote", r"benefit.{0,20}schedule", r"rider.{0,20}cost"
            ],
            QueryType.MARKET_TRENDS: [
                r"current.{0,20}rate", r"market.{0,20}trend", r"industry.{0,20}average",
                r"rates.{0,20}going", r"market.{0,20}condition", r"industry.{0,20}outlook",
                r"trending", r"latest.{0,20}rates", r"current.{0,20}market"
            ],
            QueryType.REGULATORY: [
                r"regulation", r"compliance", r"legal.{0,20}requirement", r"law.{0,20}change",
                r"regulatory.{0,20}update", r"fiduciary", r"suitability", r"disclosure"
            ],
            QueryType.EDUCATIONAL: [
                r"what.{0,20}is", r"how.{0,20}does", r"explain", r"difference.{0,20}between",
                r"basic", r"fundamental", r"concept", r"understanding", r"learn"
            ],
            QueryType.COMPARATIVE: [
                r"compare", r"versus", r"vs", r"better", r"difference.{0,20}between",
                r"which.{0,20}should", r"best.{0,20}option", r"pros.{0,20}cons"
            ],
            QueryType.CURRENT_EVENTS: [
                r"recent", r"latest", r"news", r"announcement", r"new.{0,20}product",
                r"industry.{0,20}news", r"recent.{0,20}development", r"2024", r"2025"
            ],
            QueryType.PERSONALIZED: [
                r"should.{0,20}I", r"recommend", r"my.{0,20}situation", r"advice",
                r"right.{0,20}for.{0,20}me", r"best.{0,20}for", r"considering.{0,20}my"
            ]
        }
        
        # Currency indicators for real-time information needs
        self.currency_indicators = [
            "current", "latest", "recent", "today", "now", "2024", "2025",
            "updated", "new", "trending", "market", "rates going"
        ]
        
        # Specificity indicators for document search needs
        self.specificity_indicators = [
            "specific", "exact", "precise", "detailed", "particular",
            "company", "policy", "document", "provision", "clause"
        ]
    
    async def analyze_query(self, query: str, context: str = "") -> QueryAnalysis:
        """Perform ultra-intelligent query analysis"""
        track_function_entry("analyze_query")
        
        query_lower = query.lower()
        
        # 1. Classify query type using advanced pattern matching
        query_type, type_confidence = self._classify_query_type(query_lower)
        
        # 2. Analyze information currency requirements
        requires_current = self._requires_current_info(query_lower)
        
        # 3. Analyze document specificity requirements
        requires_specific = self._requires_specific_docs(query_lower, context)
        
        # 4. Calculate complexity score
        complexity = self._calculate_complexity(query, context)
        
        # 5. Determine optimal sources and strategy
        priority_sources, search_strategy = self._determine_search_strategy(
            query_type, requires_current, requires_specific, complexity
        )
        
        # 6. Estimate processing time
        estimated_time = self._estimate_processing_time(priority_sources, complexity)
        
        analysis = QueryAnalysis(
            query_type=query_type,
            confidence=type_confidence,
            requires_current_info=requires_current,
            requires_specific_docs=requires_specific,
            complexity_score=complexity,
            priority_sources=priority_sources,
            search_strategy=search_strategy,
            estimated_search_time=estimated_time
        )
        
        log_debug("Query analysis completed", {
            "query_type": query_type.value,
            "confidence": type_confidence,
            "requires_current": requires_current,
            "requires_specific": requires_specific,
            "sources": [s.value for s in priority_sources],
            "strategy": search_strategy
        })
        
        return analysis
    
    def _classify_query_type(self, query: str) -> Tuple[QueryType, float]:
        """Classify query type with confidence scoring"""
        type_scores = {}
        
        for query_type, patterns in self.query_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 1.0
                    matches += 1
            
            if matches > 0:
                # Normalize by pattern count and add bonus for multiple matches
                type_scores[query_type] = (score / len(patterns)) + (matches * 0.1)
        
        if not type_scores:
            return QueryType.EDUCATIONAL, 0.5
        
        best_type = max(type_scores.items(), key=lambda x: x[1])
        return best_type[0], min(best_type[1], 1.0)
    
    def _requires_current_info(self, query: str) -> bool:
        """Determine if query requires current/real-time information"""
        return any(indicator in query for indicator in self.currency_indicators)
    
    def _requires_specific_docs(self, query: str, context: str) -> bool:
        """Determine if query requires specific document search"""
        has_context = bool(context.strip())
        has_specificity = any(indicator in query for indicator in self.specificity_indicators)
        
        return has_context or has_specificity
    
    def _calculate_complexity(self, query: str, context: str) -> float:
        """Calculate query complexity score (0.0 to 1.0)"""
        complexity = 0.0
        
        # Length factor
        query_tokens = len(self.enc.encode(query))
        complexity += min(query_tokens / 100, 0.3)
        
        # Question complexity
        question_words = len(re.findall(r'\b(what|how|why|when|where|which|should|could|would)\b', query.lower()))
        complexity += min(question_words * 0.1, 0.2)
        
        # Context factor
        if context:
            context_tokens = len(self.enc.encode(context))
            complexity += min(context_tokens / 1000, 0.3)
        
        # Multi-part questions
        if '?' in query:
            question_count = query.count('?')
            complexity += min(question_count * 0.1, 0.2)
        
        return min(complexity, 1.0)
    
    def _determine_search_strategy(
        self, 
        query_type: QueryType, 
        requires_current: bool, 
        requires_specific: bool, 
        complexity: float
    ) -> Tuple[List[InformationSource], str]:
        """Determine optimal search sources and strategy"""
        
        sources = []
        strategy = ""
        
        if query_type == QueryType.POLICY_SPECIFIC:
            if requires_specific:
                sources = [InformationSource.VERTEX_DB]
                strategy = "vertex_primary"
            else:
                sources = [InformationSource.VERTEX_DB, InformationSource.KNOWLEDGE_BASE]
                strategy = "vertex_with_fallback"
        
        elif query_type == QueryType.MARKET_TRENDS:
            if requires_current:
                sources = [InformationSource.INTERNET_SEARCH]
                strategy = "internet_primary"
            else:
                sources = [InformationSource.INTERNET_SEARCH, InformationSource.KNOWLEDGE_BASE]
                strategy = "internet_with_context"
        
        elif query_type == QueryType.REGULATORY:
            sources = [InformationSource.INTERNET_SEARCH, InformationSource.VERTEX_DB]
            strategy = "hybrid_regulatory"
        
        elif query_type == QueryType.COMPARATIVE:
            if complexity > 0.7:
                sources = [InformationSource.VERTEX_DB, InformationSource.INTERNET_SEARCH]
                strategy = "comprehensive_comparison"
            else:
                sources = [InformationSource.VERTEX_DB, InformationSource.KNOWLEDGE_BASE]
                strategy = "internal_comparison"
        
        elif query_type == QueryType.CURRENT_EVENTS:
            sources = [InformationSource.INTERNET_SEARCH]
            strategy = "internet_only"
        
        elif query_type == QueryType.PERSONALIZED:
            sources = [InformationSource.VERTEX_DB, InformationSource.INTERNET_SEARCH]
            strategy = "personalized_hybrid"
        
        else:  # EDUCATIONAL
            sources = [InformationSource.KNOWLEDGE_BASE]
            strategy = "knowledge_base_primary"
        
        return sources, strategy
    
    def _estimate_processing_time(self, sources: List[InformationSource], complexity: float) -> float:
        """Estimate processing time in seconds"""
        base_time = 1.0
        
        # Source-based time estimation
        source_times = {
            InformationSource.VERTEX_DB: 2.0,
            InformationSource.INTERNET_SEARCH: 3.0,
            InformationSource.KNOWLEDGE_BASE: 0.5
        }
        
        total_time = sum(source_times.get(source, 1.0) for source in sources)
        
        # Complexity multiplier
        complexity_multiplier = 1.0 + (complexity * 0.5)
        
        return total_time * complexity_multiplier

class MultiSourceOrchestrator:
    """Orchestrates parallel information retrieval from multiple sources"""
    
    def __init__(self):
        self.max_concurrent_searches = 3
        self.search_timeout = 10.0
    
    async def execute_search_strategy(
        self, 
        query: str, 
        analysis: QueryAnalysis,
        vertex_search_func: callable = None,
        internet_search_func: callable = None
    ) -> List[SourceResult]:
        """Execute the determined search strategy across multiple sources"""
        track_function_entry("execute_search_strategy")
        
        search_tasks = []
        
        # Create search tasks based on analysis
        if InformationSource.VERTEX_DB in analysis.priority_sources and vertex_search_func:
            task = self._create_vertex_search_task(query, vertex_search_func)
            search_tasks.append(task)
        
        if InformationSource.INTERNET_SEARCH in analysis.priority_sources and internet_search_func:
            task = self._create_internet_search_task(query, internet_search_func)
            search_tasks.append(task)
        
        if InformationSource.KNOWLEDGE_BASE in analysis.priority_sources:
            task = self._create_knowledge_base_task(query, analysis)
            search_tasks.append(task)
        
        # Execute searches in parallel with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*search_tasks, return_exceptions=True),
                timeout=self.search_timeout
            )
            
            # Filter successful results
            successful_results = [r for r in results if isinstance(r, SourceResult)]
            
            log_debug("Multi-source search completed", {
                "total_sources": len(search_tasks),
                "successful_results": len(successful_results),
                "strategy": analysis.search_strategy
            })
            
            return successful_results
            
        except asyncio.TimeoutError:
            log_debug("Search timeout occurred", {"timeout": self.search_timeout})
            return []
    
    async def _create_vertex_search_task(self, query: str, search_func: callable) -> SourceResult:
        """Create Vertex AI search task"""
        start_time = datetime.utcnow()
        
        try:
            # Execute vertex search
            results = await search_func(query)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return SourceResult(
                source=InformationSource.VERTEX_DB,
                content=results.get("context", ""),
                relevance_score=results.get("highest_similarity_score", 0.0),
                recency_score=0.8,  # Assume company docs are reasonably current
                reliability_score=0.95,  # High reliability for official documents
                metadata={"documents_found": results.get("documents_found", 0)},
                processing_time=processing_time
            )
            
        except Exception as e:
            log_debug("Vertex search failed", {"error": str(e)})
            raise e
    
    async def _create_internet_search_task(self, query: str, search_func: callable) -> SourceResult:
        """Create internet search task"""
        start_time = datetime.utcnow()
        
        try:
            # Execute internet search
            results = await search_func(query)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return SourceResult(
                source=InformationSource.INTERNET_SEARCH,
                content=results.get("content", ""),
                relevance_score=results.get("relevance_score", 0.7),
                recency_score=0.95,  # Internet content is typically current
                reliability_score=0.75,  # Lower reliability than official docs
                metadata={"sources": results.get("sources", [])},
                processing_time=processing_time
            )
            
        except Exception as e:
            log_debug("Internet search failed", {"error": str(e)})
            raise e
    
    async def _create_knowledge_base_task(self, query: str, analysis: QueryAnalysis) -> SourceResult:
        """Create knowledge base search task"""
        start_time = datetime.utcnow()
        
        # Simulate knowledge base access (replace with actual implementation)
        knowledge_content = f"General knowledge response for: {query}"
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return SourceResult(
            source=InformationSource.KNOWLEDGE_BASE,
            content=knowledge_content,
            relevance_score=0.6,
            recency_score=0.5,
            reliability_score=0.8,
            metadata={"query_type": analysis.query_type.value},
            processing_time=processing_time
        )

class InformationSynthesisEngine:
    """Advanced information synthesis and ranking system"""
    
    def __init__(self):
        self.enc = tiktoken.get_encoding("cl100k_base")
    
    def synthesize_results(self, results: List[SourceResult], query: str, analysis: QueryAnalysis) -> Dict[str, Any]:
        """Synthesize multiple source results into coherent response context"""
        track_function_entry("synthesize_results")
        
        if not results:
            return {
                "synthesized_content": "",
                "source_breakdown": {},
                "confidence_score": 0.0,
                "synthesis_metadata": {"note": "No results to synthesize"}
            }
        
        # 1. Rank and weight results
        weighted_results = self._rank_and_weight_results(results, analysis)
        
        # 2. Create synthesized content
        synthesized_content = self._create_synthesized_content(weighted_results, query, analysis)
        
        # 3. Calculate overall confidence
        confidence_score = self._calculate_synthesis_confidence(weighted_results)
        
        # 4. Create source breakdown
        source_breakdown = self._create_source_breakdown(weighted_results)
        
        synthesis_result = {
            "synthesized_content": synthesized_content,
            "source_breakdown": source_breakdown,
            "confidence_score": confidence_score,
            "synthesis_metadata": {
                "sources_used": len(results),
                "primary_source": weighted_results[0].source.value if weighted_results else None,
                "synthesis_strategy": analysis.search_strategy,
                "total_processing_time": sum(r.processing_time for r in results)
            }
        }
        
        log_debug("Information synthesis completed", {
            "sources_synthesized": len(results),
            "confidence_score": confidence_score,
            "content_length": len(synthesized_content)
        })
        
        return synthesis_result
    
    def _rank_and_weight_results(self, results: List[SourceResult], analysis: QueryAnalysis) -> List[SourceResult]:
        """Rank and weight results based on query requirements"""
        def calculate_weight(result: SourceResult) -> float:
            weight = 0.0
            
            # Base scores
            weight += result.relevance_score * 0.4
            weight += result.reliability_score * 0.3
            
            # Query-specific weighting
            if analysis.requires_current_info:
                weight += result.recency_score * 0.3
            else:
                weight += result.reliability_score * 0.3
            
            # Source-specific bonuses
            if analysis.requires_specific_docs and result.source == InformationSource.VERTEX_DB:
                weight += 0.2
            
            if analysis.query_type == QueryType.MARKET_TRENDS and result.source == InformationSource.INTERNET_SEARCH:
                weight += 0.2
            
            return min(weight, 1.0)
        
        # Calculate weights and sort
        for result in results:
            result.weight = calculate_weight(result)
        
        return sorted(results, key=lambda r: r.weight, reverse=True)
    
    def _create_synthesized_content(self, results: List[SourceResult], query: str, analysis: QueryAnalysis) -> str:
        """Create synthesized content from multiple sources"""
        if not results:
            return ""
        
        content_parts = []
        
        # Primary source content (highest weighted)
        primary_result = results[0]
        if primary_result.content:
            content_parts.append(f"**Primary Source ({primary_result.source.value}):**\n{primary_result.content}")
        
        # Secondary sources for comprehensive coverage
        for result in results[1:]:
            if result.content and result.weight > 0.5:
                content_parts.append(f"\n**Additional Context ({result.source.value}):**\n{result.content}")
        
        # Combine with strategic separation
        synthesized = "\n\n".join(content_parts)
        
        # Add source attribution summary
        if len(results) > 1:
            sources_summary = ", ".join([r.source.value for r in results])
            synthesized += f"\n\n**Information Sources:** {sources_summary}"
        
        return synthesized
    
    def _calculate_synthesis_confidence(self, results: List[SourceResult]) -> float:
        """Calculate overall confidence in synthesized information"""
        if not results:
            return 0.0
        
        # Weighted average of result confidence scores
        total_weight = sum(r.weight for r in results)
        if total_weight == 0:
            return 0.5
        
        weighted_confidence = sum(r.weight * (r.relevance_score * r.reliability_score) for r in results)
        base_confidence = weighted_confidence / total_weight
        
        # Bonus for multiple high-quality sources
        if len(results) > 1 and all(r.weight > 0.6 for r in results[:2]):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _create_source_breakdown(self, results: List[SourceResult]) -> Dict[str, Any]:
        """Create detailed breakdown of source contributions"""
        breakdown = {}
        
        for result in results:
            breakdown[result.source.value] = {
                "weight": result.weight,
                "relevance_score": result.relevance_score,
                "reliability_score": result.reliability_score,
                "recency_score": result.recency_score,
                "processing_time": result.processing_time,
                "metadata": result.metadata
            }
        
        return breakdown