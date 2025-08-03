# Enhanced RAG System - Production-Ready with Advanced Features
# Integrates all enhanced services: caching, performance monitoring, error handling

import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Core imports
from core import (
    initialize_all_services, health_check, get_service_status, 
    global_state, log_debug, track_function_entry
)

# Enhanced services
from cache_service import cache_service, initialize_cache_service
from performance_monitor import performance_monitor, create_request_middleware
from error_handler import error_handler, create_exception_handler
from enhanced_file_processor import batch_manager

# Routers
from search_router import router as search_router
from chat_router import router as chat_router
from documents_router import router as documents_router
from admin_router import router as admin_router

# Version and metadata
VERSION = "7.0-ENHANCED-SOTA"
BUILD_DATE = "2025-01-03"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with enhanced initialization"""
    
    # Startup
    log_debug("🚀 Starting Enhanced RAG System", {
        "version": VERSION,
        "build_date": BUILD_DATE,
        "features": [
            "Multi-layer caching",
            "Performance monitoring", 
            "Advanced error handling",
            "Faceted search",
            "Batch processing",
            "Rate limiting"
        ]
    })
    
    try:
        # Initialize core services
        log_debug("Initializing core services...")
        initialization_results = initialize_all_services()
        
        if not initialization_results["success"]:
            log_debug("❌ Core service initialization failed", initialization_results)
            raise Exception("Failed to initialize core services")
        
        # Initialize enhanced services
        log_debug("Initializing enhanced services...")
        
        # Initialize cache service
        initialize_cache_service()
        log_debug("✅ Cache service initialized")
        
        # Start batch processing queue
        asyncio.create_task(batch_manager.process_queue())
        log_debug("✅ Batch processing queue started")
        
        # Record startup completion
        global_state.startup_time = time.time()
        log_debug("🎉 Enhanced RAG System startup completed", {
            "initialization_time_ms": (time.time() - global_state.startup_time) * 1000,
            "services_initialized": initialization_results
        })
        
        yield
        
    except Exception as e:
        log_debug("💥 Startup failed", {"error": str(e)})
        raise
    
    # Shutdown
    log_debug("🛑 Shutting down Enhanced RAG System")
    
    # Clear caches
    cache_service.clear_all_caches()
    log_debug("✅ Caches cleared")

# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="Enhanced RAG System API",
    description="""
    Advanced Retrieval Augmented Generation system with life insurance domain expertise.
    
    ## Features
    - **Advanced Search**: Faceted search with multiple filtering dimensions
    - **Performance Optimization**: Multi-layer caching and rate limiting
    - **Comprehensive Error Handling**: Detailed error codes and user-friendly messages
    - **Real-time Monitoring**: Performance analytics and system health monitoring
    - **Batch Processing**: Efficient document processing with progress tracking
    - **Auto-complete**: Smart query suggestions and auto-completion
    
    ## Enhanced Capabilities
    - Multi-format document processing (PDF, DOCX, Excel, CSV, JSON)
    - Intelligent query optimization and entity extraction
    - Domain-specific life insurance expertise
    - Circuit breaker protection for external services
    - Comprehensive API analytics and insights
    """,
    version=VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Performance monitoring middleware"""
    middleware_func = create_request_middleware(performance_monitor)
    return await middleware_func(request, call_next)

# Add enhanced exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with detailed error reporting"""
    handler = await create_exception_handler()
    return await handler(request, exc)

# Include enhanced routers
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(admin_router)

# Enhanced root endpoints
@app.get("/", tags=["system"])
async def root():
    """Enhanced system information and capabilities"""
    track_function_entry("root")
    
    try:
        service_status = get_service_status()
        system_health = health_check()
        
        return {
            "service": "Enhanced RAG System API",
            "version": VERSION,
            "build_date": BUILD_DATE,
            "status": "operational",
            "features": {
                "advanced_search": {
                    "faceted_search": True,
                    "autocomplete": True,
                    "query_optimization": True,
                    "entity_extraction": True
                },
                "performance": {
                    "multi_layer_caching": True,
                    "rate_limiting": True,
                    "performance_monitoring": True,
                    "real_time_analytics": True
                },
                "processing": {
                    "batch_processing": True,
                    "multi_format_support": True,
                    "async_processing": True,
                    "progress_tracking": True
                },
                "reliability": {
                    "circuit_breaker": True,
                    "comprehensive_error_handling": True,
                    "health_monitoring": True,
                    "graceful_degradation": True
                }
            },
            "capabilities": {
                "supported_formats": [".pdf", ".docx", ".txt", ".md", ".csv", ".json", ".xlsx"],
                "search_types": ["semantic", "faceted", "similarity", "hybrid"],
                "life_insurance_expertise": True,
                "real_time_sync": True
            },
            "health": system_health,
            "services": service_status,
            "uptime_seconds": (time.time() - global_state.startup_time),
            "api_endpoints": {
                "search": "/search/",
                "advanced_search": "/search/advanced",
                "autocomplete": "/search/autocomplete",
                "chat": "/chat/ask",
                "documents": "/documents/list",
                "admin": "/admin/status",
                "performance": "/search/performance"
            }
        }
        
    except Exception as e:
        log_debug("Error in root endpoint", {"error": str(e)})
        return error_handler.handle_unexpected_error(e)

@app.get("/health", tags=["system"])
async def enhanced_health_check():
    """Enhanced health check with comprehensive system status"""
    track_function_entry("enhanced_health_check")
    
    try:
        # Basic health check
        basic_health = health_check()
        
        # Enhanced metrics
        enhanced_metrics = {
            "cache_performance": cache_service.get_cache_statistics(),
            "api_performance": performance_monitor.get_real_time_metrics(),
            "error_statistics": error_handler.get_error_analytics(hours=1),
            "batch_processing": batch_manager.get_processing_statistics(),
            "system_metrics": {
                "uptime_seconds": (time.time() - global_state.startup_time),
                "total_requests": global_state.request_count,
                "active_requests": len(performance_monitor.active_requests),
                "circuit_breaker_status": global_state.circuit_breaker
            }
        }
        
        # Determine overall health status
        overall_status = "healthy"
        if enhanced_metrics["error_statistics"].get("error_rate_per_hour", 0) > 10:
            overall_status = "degraded"
        if not basic_health.get("database_connection", True):
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "version": VERSION,
            "basic_health": basic_health,
            "enhanced_metrics": enhanced_metrics,
            "recommendations": _get_health_recommendations(enhanced_metrics)
        }
        
    except Exception as e:
        log_debug("Health check failed", {"error": str(e)})
        return error_handler.handle_unexpected_error(e)

def _get_health_recommendations(metrics: dict) -> List[str]:
    """Generate health recommendations based on metrics"""
    recommendations = []
    
    # Cache performance recommendations
    cache_hit_rate = metrics["cache_performance"]["performance"]["hit_rate_percent"]
    if cache_hit_rate < 30:
        recommendations.append("Consider warming up cache with common queries")
    
    # API performance recommendations
    api_metrics = metrics["api_performance"]
    if api_metrics.get("avg_response_time_ms", 0) > 2000:
        recommendations.append("Response times are high - consider performance optimization")
    
    # Error rate recommendations
    error_rate = metrics["error_statistics"].get("error_rate_per_hour", 0)
    if error_rate > 5:
        recommendations.append("Error rate is elevated - check system logs")
    
    if not recommendations:
        recommendations.append("System is performing optimally")
    
    return recommendations

@app.get("/api/capabilities", tags=["system"])
async def get_api_capabilities():
    """Get comprehensive API capabilities and features"""
    track_function_entry("get_api_capabilities")
    
    try:
        return {
            "version": VERSION,
            "build_date": BUILD_DATE,
            "api_features": {
                "search": {
                    "endpoints": ["/search/", "/search/advanced", "/search/similar"],
                    "features": ["semantic_search", "faceted_filtering", "entity_extraction"],
                    "supported_filters": ["document_type", "product_type", "topic", "complexity"]
                },
                "chat": {
                    "endpoints": ["/chat/ask", "/chat/analyze_query"],
                    "features": ["intent_classification", "context_aware_responses", "feedback_collection"],
                    "supported_intents": ["product_comparison", "premium_inquiry", "coverage_amount"]
                },
                "documents": {
                    "endpoints": ["/documents/list", "/documents/sync", "/documents/indexed"],
                    "features": ["multi_format_processing", "batch_operations", "real_time_sync"],
                    "supported_formats": [".pdf", ".docx", ".txt", ".md", ".csv", ".json", ".xlsx"]
                },
                "admin": {
                    "endpoints": ["/admin/status", "/admin/debug", "/admin/performance"],
                    "features": ["health_monitoring", "performance_analytics", "error_tracking"],
                    "analytics": ["real_time_metrics", "error_statistics", "cache_performance"]
                }
            },
            "performance_features": {
                "caching": {
                    "layers": ["search_results", "embeddings", "document_metadata", "entity_extraction"],
                    "ttl_minutes": [30, 120, 60, 30]
                },
                "rate_limiting": {
                    "default": "60/minute",
                    "search": "30/minute", 
                    "chat": "20/minute",
                    "sync": "5/minute"
                },
                "monitoring": {
                    "metrics": ["response_time", "error_rate", "cache_hit_rate", "throughput"],
                    "alerts": ["high_error_rate", "slow_responses", "service_unavailable"]
                }
            },
            "domain_expertise": {
                "life_insurance": {
                    "product_types": 5,
                    "intent_patterns": 8,
                    "entity_types": 6
                }
            }
        }
        
    except Exception as e:
        log_debug("Error getting API capabilities", {"error": str(e)})
        return error_handler.handle_unexpected_error(e)

# Additional utility endpoints
@app.get("/api/stats", tags=["analytics"])
async def get_system_statistics():
    """Get comprehensive system statistics"""
    track_function_entry("get_system_statistics")
    
    try:
        return {
            "system": {
                "version": VERSION,
                "uptime_seconds": (time.time() - global_state.startup_time),
                "total_requests": global_state.request_count,
                "function_calls": global_state.function_calls
            },
            "performance": performance_monitor.get_performance_dashboard(),
            "cache": cache_service.get_cache_statistics(),
            "errors": error_handler.get_error_analytics(),
            "processing": batch_manager.get_processing_statistics()
        }
        
    except Exception as e:
        log_debug("Error getting system statistics", {"error": str(e)})
        return error_handler.handle_unexpected_error(e)

if __name__ == "__main__":
    import uvicorn
    
    log_debug("🚀 Starting Enhanced RAG System server", {
        "version": VERSION,
        "build_date": BUILD_DATE
    })
    
    uvicorn.run(
        "main_enhanced:app",
        host="0.0.0.0",
        port=8080,
        reload=False,  # Disable in production
        log_level="info"
    )