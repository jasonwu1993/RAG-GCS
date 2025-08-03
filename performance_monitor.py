# API Performance Monitoring and Analytics Service
# Comprehensive monitoring, rate limiting, and performance analytics

import time
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
from dataclasses import dataclass, asdict
from threading import Lock
import json

from core import log_debug, track_function_entry, global_state

@dataclass
class RequestMetrics:
    """Individual request metrics"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: datetime
    user_agent: str
    ip_address: str
    query_params: Dict[str, Any]
    response_size_bytes: int
    cache_hit: bool = False
    error_type: Optional[str] = None

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_minute: int = 60, burst_size: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self.lock = Lock()
    
    def is_allowed(self, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed"""
        with self.lock:
            now = time.time()
            
            # Add tokens based on time elapsed
            time_passed = now - self.last_update
            tokens_to_add = time_passed * (self.requests_per_minute / 60.0)
            self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True, {
                    "allowed": True,
                    "tokens_remaining": int(self.tokens),
                    "reset_time": now + (60.0 / self.requests_per_minute)
                }
            else:
                return False, {
                    "allowed": False,
                    "tokens_remaining": 0,
                    "reset_time": now + (60.0 / self.requests_per_minute),
                    "retry_after": (1 - self.tokens) * (60.0 / self.requests_per_minute)
                }

class PerformanceAnalyzer:
    """Analyze performance patterns and trends"""
    
    def __init__(self):
        self.metrics_history: List[RequestMetrics] = []
        self.max_history = 10000
        self.lock = Lock()
        
        # Performance thresholds
        self.slow_request_threshold_ms = 2000
        self.error_rate_threshold = 0.05  # 5%
        self.cache_hit_target = 0.3  # 30%
    
    def add_request_metric(self, metric: RequestMetrics):
        """Add request metric to history"""
        with self.lock:
            self.metrics_history.append(metric)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
    
    def get_performance_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get performance summary for time window"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        with self.lock:
            recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"error": "No metrics available for time window"}
        
        # Calculate basic statistics
        response_times = [m.response_time_ms for m in recent_metrics]
        status_codes = [m.status_code for m in recent_metrics]
        cache_hits = [m.cache_hit for m in recent_metrics]
        
        error_count = sum(1 for code in status_codes if code >= 400)
        cache_hit_count = sum(1 for hit in cache_hits if hit)
        
        # Endpoint performance
        endpoint_stats = defaultdict(lambda: {"count": 0, "total_time": 0, "errors": 0})
        for metric in recent_metrics:
            endpoint_stats[metric.endpoint]["count"] += 1
            endpoint_stats[metric.endpoint]["total_time"] += metric.response_time_ms
            if metric.status_code >= 400:
                endpoint_stats[metric.endpoint]["errors"] += 1
        
        # Calculate averages
        for endpoint in endpoint_stats:
            stats = endpoint_stats[endpoint]
            stats["avg_response_time"] = stats["total_time"] / stats["count"]
            stats["error_rate"] = stats["errors"] / stats["count"]
        
        return {
            "time_window_minutes": time_window_minutes,
            "total_requests": len(recent_metrics),
            "performance": {
                "avg_response_time_ms": statistics.mean(response_times),
                "median_response_time_ms": statistics.median(response_times),
                "p95_response_time_ms": self._calculate_percentile(response_times, 95),
                "p99_response_time_ms": self._calculate_percentile(response_times, 99),
                "min_response_time_ms": min(response_times),
                "max_response_time_ms": max(response_times)
            },
            "reliability": {
                "total_errors": error_count,
                "error_rate": error_count / len(recent_metrics),
                "success_rate": 1 - (error_count / len(recent_metrics))
            },
            "cache_performance": {
                "total_cache_hits": cache_hit_count,
                "cache_hit_rate": cache_hit_count / len(recent_metrics),
                "cache_miss_count": len(recent_metrics) - cache_hit_count
            },
            "endpoint_breakdown": dict(endpoint_stats),
            "alerts": self._generate_alerts(recent_metrics, endpoint_stats)
        }
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100.0) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _generate_alerts(self, metrics: List[RequestMetrics], 
                        endpoint_stats: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate performance alerts"""
        alerts = []
        
        # Check overall error rate
        error_count = sum(1 for m in metrics if m.status_code >= 400)
        error_rate = error_count / len(metrics) if metrics else 0
        
        if error_rate > self.error_rate_threshold:
            alerts.append({
                "type": "error_rate",
                "severity": "high" if error_rate > 0.1 else "medium",
                "message": f"Error rate ({error_rate:.1%}) exceeds threshold ({self.error_rate_threshold:.1%})",
                "value": error_rate,
                "threshold": self.error_rate_threshold
            })
        
        # Check slow requests
        slow_requests = [m for m in metrics if m.response_time_ms > self.slow_request_threshold_ms]
        if slow_requests:
            slow_rate = len(slow_requests) / len(metrics)
            if slow_rate > 0.1:  # More than 10% slow requests
                alerts.append({
                    "type": "slow_requests",
                    "severity": "medium",
                    "message": f"{slow_rate:.1%} of requests are slow (>{self.slow_request_threshold_ms}ms)",
                    "value": slow_rate,
                    "slow_count": len(slow_requests)
                })
        
        # Check cache hit rate
        cache_hits = [m for m in metrics if m.cache_hit]
        cache_hit_rate = len(cache_hits) / len(metrics) if metrics else 0
        
        if cache_hit_rate < self.cache_hit_target:
            alerts.append({
                "type": "low_cache_hit_rate",
                "severity": "low",
                "message": f"Cache hit rate ({cache_hit_rate:.1%}) below target ({self.cache_hit_target:.1%})",
                "value": cache_hit_rate,
                "target": self.cache_hit_target
            })
        
        # Check endpoint-specific issues
        for endpoint, stats in endpoint_stats.items():
            if stats["error_rate"] > 0.1:  # 10% error rate for specific endpoint
                alerts.append({
                    "type": "endpoint_errors",
                    "severity": "high",
                    "message": f"High error rate for {endpoint}: {stats['error_rate']:.1%}",
                    "endpoint": endpoint,
                    "error_rate": stats["error_rate"]
                })
        
        return alerts

class PerformanceMonitor:
    """Main performance monitoring service"""
    
    def __init__(self):
        self.analyzer = PerformanceAnalyzer()
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.active_requests: Dict[str, datetime] = {}
        self.lock = Lock()
        
        # Default rate limiter
        self.default_rate_limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        
        # Endpoint-specific rate limits
        self.endpoint_rate_limits = {
            "/search/": RateLimiter(requests_per_minute=30, burst_size=5),
            "/chat/ask": RateLimiter(requests_per_minute=20, burst_size=3),
            "/documents/sync": RateLimiter(requests_per_minute=5, burst_size=2)
        }
        
        log_debug("Performance monitor initialized")
    
    def check_rate_limit(self, client_id: str, endpoint: str) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit for client and endpoint"""
        # Get appropriate rate limiter
        rate_limiter = self.endpoint_rate_limits.get(endpoint, self.default_rate_limiter)
        
        # Check if allowed
        allowed, limit_info = rate_limiter.is_allowed(client_id)
        
        if not allowed:
            log_debug("Rate limit exceeded", {
                "client_id": client_id,
                "endpoint": endpoint,
                "limit_info": limit_info
            })
        
        return allowed, limit_info
    
    def start_request_tracking(self, request_id: str, endpoint: str, method: str, 
                              client_ip: str, user_agent: str) -> str:
        """Start tracking a request"""
        with self.lock:
            self.active_requests[request_id] = datetime.now()
        
        return request_id
    
    def end_request_tracking(self, request_id: str, endpoint: str, method: str,
                           status_code: int, response_size: int = 0,
                           client_ip: str = "", user_agent: str = "",
                           query_params: Dict[str, Any] = None,
                           cache_hit: bool = False, error_type: str = None):
        """End request tracking and record metrics"""
        
        start_time = self.active_requests.pop(request_id, datetime.now())
        end_time = datetime.now()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Create metric record
        metric = RequestMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            timestamp=end_time,
            user_agent=user_agent,
            ip_address=client_ip,
            query_params=query_params or {},
            response_size_bytes=response_size,
            cache_hit=cache_hit,
            error_type=error_type
        )
        
        # Add to analyzer
        self.analyzer.add_request_metric(metric)
        
        # Update global state
        global_state.track_request(success=(status_code < 400))
        
        # Log slow requests
        if response_time_ms > self.analyzer.slow_request_threshold_ms:
            log_debug("Slow request detected", {
                "endpoint": endpoint,
                "response_time_ms": response_time_ms,
                "status_code": status_code
            })
        
        return metric
    
    def get_performance_dashboard(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get comprehensive performance dashboard"""
        summary = self.analyzer.get_performance_summary(time_window_minutes)
        
        # Add current system status
        system_status = {
            "active_requests": len(self.active_requests),
            "uptime_seconds": (datetime.now() - global_state.startup_time).total_seconds(),
            "total_requests_lifetime": global_state.request_count,
            "circuit_breaker_status": global_state.circuit_breaker
        }
        
        return {
            **summary,
            "system_status": system_status,
            "rate_limiting": {
                "default_limit": f"{self.default_rate_limiter.requests_per_minute}/min",
                "endpoint_limits": {
                    endpoint: f"{limiter.requests_per_minute}/min" 
                    for endpoint, limiter in self.endpoint_rate_limits.items()
                }
            }
        }
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for monitoring dashboard"""
        recent_metrics = []
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        with self.analyzer.lock:
            recent_metrics = [m for m in self.analyzer.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"status": "no_recent_activity"}
        
        # Calculate real-time stats
        response_times = [m.response_time_ms for m in recent_metrics]
        current_load = len(recent_metrics) / 5.0  # requests per minute
        
        return {
            "current_load_rpm": current_load,
            "avg_response_time_ms": statistics.mean(response_times),
            "active_requests": len(self.active_requests),
            "recent_errors": len([m for m in recent_metrics if m.status_code >= 400]),
            "cache_hit_rate": len([m for m in recent_metrics if m.cache_hit]) / len(recent_metrics),
            "timestamp": datetime.now().isoformat()
        }

# Middleware helper functions
def create_request_middleware(monitor: PerformanceMonitor):
    """Create FastAPI middleware for request monitoring"""
    
    async def monitor_request(request, call_next):
        # Generate request ID
        request_id = f"{int(time.time() * 1000)}_{id(request)}"
        
        # Extract client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        endpoint = str(request.url.path)
        method = request.method
        
        # Check rate limiting
        allowed, limit_info = monitor.check_rate_limit(client_ip, endpoint)
        if not allowed:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": limit_info.get("retry_after", 60)
                },
                headers={
                    "X-RateLimit-Remaining": str(limit_info.get("tokens_remaining", 0)),
                    "X-RateLimit-Reset": str(int(limit_info.get("reset_time", time.time())))
                }
            )
        
        # Start tracking
        monitor.start_request_tracking(request_id, endpoint, method, client_ip, user_agent)
        
        # Process request
        start_time = time.time()
        try:
            response = await call_next(request)
            
            # End tracking
            monitor.end_request_tracking(
                request_id=request_id,
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                response_size=0,  # Would need to calculate from response
                client_ip=client_ip,
                user_agent=user_agent,
                cache_hit=getattr(response, 'cache_hit', False)
            )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # End tracking with error
            monitor.end_request_tracking(
                request_id=request_id,
                endpoint=endpoint,
                method=method,
                status_code=500,
                client_ip=client_ip,
                user_agent=user_agent,
                error_type=type(e).__name__
            )
            raise
    
    return monitor_request

# Global monitor instance
performance_monitor = PerformanceMonitor()