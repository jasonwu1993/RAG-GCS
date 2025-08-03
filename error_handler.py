# Comprehensive Error Handling System
# Detailed error codes, user-friendly messages, and error analytics

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import traceback
import json
from dataclasses import dataclass, asdict

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from core import log_debug, track_function_entry, global_state

class ErrorCategory(Enum):
    """Error categories for classification"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication" 
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    RATE_LIMIT = "rate_limit"
    EXTERNAL_SERVICE = "external_service"
    PROCESSING = "processing"
    STORAGE = "storage"
    SEARCH = "search"
    SYSTEM = "system"
    CONFIGURATION = "configuration"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorDetails:
    """Detailed error information"""
    code: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    details: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    documentation_url: Optional[str] = None

class ErrorCodes:
    """Centralized error code definitions"""
    
    # Validation Errors (1000-1999)
    INVALID_QUERY = ErrorDetails(
        code="VAL_1001",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        message="Query parameter is empty or invalid",
        user_message="Please provide a valid search query",
        suggestions=["Enter a search term with at least 2 characters", "Check for special characters that might cause issues"]
    )
    
    INVALID_FILE_FORMAT = ErrorDetails(
        code="VAL_1002", 
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        message="Unsupported file format provided",
        user_message="File format not supported for processing",
        suggestions=["Use supported formats: PDF, DOCX, TXT, MD, CSV, JSON, XLSX"]
    )
    
    FILE_TOO_LARGE = ErrorDetails(
        code="VAL_1003",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        message="File size exceeds maximum allowed limit",
        user_message="File is too large to process",
        suggestions=["Reduce file size to under 50MB", "Split large files into smaller documents"]
    )
    
    INVALID_FILTERS = ErrorDetails(
        code="VAL_1004",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        message="Invalid search filters provided",
        user_message="Search filters contain invalid values",
        suggestions=["Check filter format", "Use available facet values from /search/facets endpoint"]
    )
    
    # Authentication Errors (2000-2999)
    MISSING_API_KEY = ErrorDetails(
        code="AUTH_2001",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        message="API key not provided",
        user_message="Authentication required",
        suggestions=["Include API key in Authorization header", "Contact administrator for API access"]
    )
    
    INVALID_API_KEY = ErrorDetails(
        code="AUTH_2002",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        message="Invalid or expired API key",
        user_message="Authentication failed",
        suggestions=["Check API key format", "Request new API key if expired"]
    )
    
    # Rate Limiting Errors (3000-3999)
    RATE_LIMIT_EXCEEDED = ErrorDetails(
        code="RATE_3001",
        category=ErrorCategory.RATE_LIMIT,
        severity=ErrorSeverity.MEDIUM,
        message="Request rate limit exceeded",
        user_message="Too many requests. Please slow down.",
        suggestions=["Wait before making another request", "Consider upgrading to higher rate limits"]
    )
    
    # External Service Errors (4000-4999)
    OPENAI_SERVICE_ERROR = ErrorDetails(
        code="EXT_4001",
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.HIGH,
        message="OpenAI service unavailable or error",
        user_message="AI service temporarily unavailable",
        suggestions=["Try again in a few minutes", "Contact support if problem persists"]
    )
    
    VERTEX_AI_ERROR = ErrorDetails(
        code="EXT_4002",
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.HIGH,
        message="Vertex AI search service error",
        user_message="Search service temporarily unavailable",
        suggestions=["Try again later", "Use basic search if available"]
    )
    
    GOOGLE_DRIVE_ERROR = ErrorDetails(
        code="EXT_4003",
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.MEDIUM,
        message="Google Drive sync service error",
        user_message="Document sync temporarily unavailable",
        suggestions=["Check Google Drive permissions", "Try manual sync later"]
    )
    
    GOOGLE_STORAGE_ERROR = ErrorDetails(
        code="EXT_4004",
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.HIGH,
        message="Google Cloud Storage error",
        user_message="Storage service unavailable",
        suggestions=["Try again later", "Contact support if problem persists"]
    )
    
    # Processing Errors (5000-5999)
    TEXT_EXTRACTION_FAILED = ErrorDetails(
        code="PROC_5001",
        category=ErrorCategory.PROCESSING,
        severity=ErrorSeverity.MEDIUM,
        message="Failed to extract text from document",
        user_message="Could not process document content",
        suggestions=["Check if document is password protected", "Try a different file format", "Ensure document is not corrupted"]
    )
    
    EMBEDDING_GENERATION_FAILED = ErrorDetails(
        code="PROC_5002",
        category=ErrorCategory.PROCESSING,
        severity=ErrorSeverity.HIGH,
        message="Failed to generate text embeddings",
        user_message="Document indexing failed",
        suggestions=["Try processing again", "Contact support if error persists"]
    )
    
    CHUNK_CREATION_FAILED = ErrorDetails(
        code="PROC_5003",
        category=ErrorCategory.PROCESSING,
        severity=ErrorSeverity.MEDIUM,
        message="Failed to create text chunks from document",
        user_message="Document processing failed",
        suggestions=["Check document format", "Ensure document contains readable text"]
    )
    
    BATCH_PROCESSING_FAILED = ErrorDetails(
        code="PROC_5004",
        category=ErrorCategory.PROCESSING,
        severity=ErrorSeverity.MEDIUM,
        message="Batch processing operation failed",
        user_message="Multiple document processing failed",
        suggestions=["Check individual file errors", "Try processing files separately"]
    )
    
    # Search Errors (6000-6999)
    SEARCH_INDEX_UNAVAILABLE = ErrorDetails(
        code="SEARCH_6001",
        category=ErrorCategory.SEARCH,
        severity=ErrorSeverity.HIGH,
        message="Search index not available",
        user_message="Search functionality temporarily unavailable",
        suggestions=["Try again later", "Contact support if problem persists"]
    )
    
    SEARCH_TIMEOUT = ErrorDetails(
        code="SEARCH_6002",
        category=ErrorCategory.SEARCH,
        severity=ErrorSeverity.MEDIUM,
        message="Search operation timed out",
        user_message="Search took too long to complete",
        suggestions=["Try a more specific query", "Use filters to narrow results"]
    )
    
    NO_SEARCH_RESULTS = ErrorDetails(
        code="SEARCH_6003",
        category=ErrorCategory.SEARCH,
        severity=ErrorSeverity.LOW,
        message="No results found for search query",
        user_message="No documents found matching your search",
        suggestions=["Try different keywords", "Check spelling", "Use broader search terms"]
    )
    
    # System Errors (7000-7999)
    INTERNAL_SERVER_ERROR = ErrorDetails(
        code="SYS_7001",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.CRITICAL,
        message="Internal server error occurred",
        user_message="An unexpected error occurred",
        suggestions=["Try again later", "Contact support with error details"]
    )
    
    SERVICE_UNAVAILABLE = ErrorDetails(
        code="SYS_7002",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.HIGH,
        message="Service temporarily unavailable",
        user_message="Service is currently under maintenance",
        suggestions=["Try again in a few minutes", "Check status page for updates"]
    )
    
    CONFIGURATION_ERROR = ErrorDetails(
        code="SYS_7003",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.CRITICAL,
        message="System configuration error",
        user_message="System configuration issue detected",
        suggestions=["Contact system administrator", "Check service configuration"]
    )

class ErrorAnalytics:
    """Track and analyze errors for insights"""
    
    def __init__(self):
        self.error_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        self.error_counts: Dict[str, int] = {}
        
    def record_error(self, error_code: str, error_details: ErrorDetails, 
                    request_info: Dict[str, Any] = None):
        """Record error occurrence for analytics"""
        
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_code": error_code,
            "category": error_details.category.value,
            "severity": error_details.severity.value,
            "message": error_details.message,
            "request_info": request_info or {}
        }
        
        self.error_history.append(error_record)
        
        # Update counts
        self.error_counts[error_code] = self.error_counts.get(error_code, 0) + 1
        
        # Cleanup old history
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        # Log error
        log_debug("Error recorded", {
            "error_code": error_code,
            "category": error_details.category.value,
            "severity": error_details.severity.value
        })
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for specified time period"""
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        
        recent_errors = [
            error for error in self.error_history
            if datetime.fromisoformat(error["timestamp"]).timestamp() > cutoff_time
        ]
        
        if not recent_errors:
            return {"status": "no_errors", "time_period_hours": hours}
        
        # Calculate statistics
        error_by_category = {}
        error_by_severity = {}
        error_by_code = {}
        
        for error in recent_errors:
            category = error["category"]
            severity = error["severity"]
            code = error["error_code"]
            
            error_by_category[category] = error_by_category.get(category, 0) + 1
            error_by_severity[severity] = error_by_severity.get(severity, 0) + 1
            error_by_code[code] = error_by_code.get(code, 0) + 1
        
        # Top errors
        top_errors = sorted(error_by_code.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "time_period_hours": hours,
            "total_errors": len(recent_errors),
            "errors_by_category": error_by_category,
            "errors_by_severity": error_by_severity,
            "top_error_codes": dict(top_errors),
            "error_rate_per_hour": len(recent_errors) / hours
        }

class EnhancedErrorHandler:
    """Main error handling service"""
    
    def __init__(self):
        self.analytics = ErrorAnalytics()
        self.error_codes = ErrorCodes()
        
        log_debug("Enhanced error handler initialized")
    
    def create_error_response(self, error_details: ErrorDetails, 
                            request: Optional[Request] = None,
                            additional_context: Dict[str, Any] = None) -> JSONResponse:
        """Create standardized error response"""
        
        # Record error for analytics
        request_info = {}
        if request:
            request_info = {
                "endpoint": str(request.url.path),
                "method": request.method,
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        
        self.analytics.record_error(error_details.code, error_details, request_info)
        
        # Build response
        response_data = {
            "error": {
                "code": error_details.code,
                "category": error_details.category.value,
                "severity": error_details.severity.value,
                "message": error_details.user_message,
                "details": error_details.details or {},
                "suggestions": error_details.suggestions or [],
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Add additional context
        if additional_context:
            response_data["error"]["context"] = additional_context
        
        # Add documentation URL if available
        if error_details.documentation_url:
            response_data["error"]["documentation"] = error_details.documentation_url
        
        # Determine HTTP status code based on category
        status_code = self._get_http_status_code(error_details.category)
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    def _get_http_status_code(self, category: ErrorCategory) -> int:
        """Map error category to HTTP status code"""
        mapping = {
            ErrorCategory.VALIDATION: 400,
            ErrorCategory.AUTHENTICATION: 401,
            ErrorCategory.AUTHORIZATION: 403,
            ErrorCategory.NOT_FOUND: 404,
            ErrorCategory.RATE_LIMIT: 429,
            ErrorCategory.EXTERNAL_SERVICE: 502,
            ErrorCategory.PROCESSING: 422,
            ErrorCategory.STORAGE: 503,
            ErrorCategory.SEARCH: 503,
            ErrorCategory.SYSTEM: 500,
            ErrorCategory.CONFIGURATION: 500
        }
        return mapping.get(category, 500)
    
    def handle_validation_error(self, message: str, details: Dict[str, Any] = None) -> JSONResponse:
        """Handle validation errors"""
        error_details = self.error_codes.INVALID_QUERY
        if details:
            error_details.details = details
        return self.create_error_response(error_details)
    
    def handle_rate_limit_error(self, retry_after: int = 60) -> JSONResponse:
        """Handle rate limiting errors"""
        error_details = self.error_codes.RATE_LIMIT_EXCEEDED
        error_details.details = {"retry_after_seconds": retry_after}
        
        response = self.create_error_response(error_details)
        response.headers["Retry-After"] = str(retry_after)
        return response
    
    def handle_external_service_error(self, service: str, original_error: str = None) -> JSONResponse:
        """Handle external service errors"""
        service_errors = {
            "openai": self.error_codes.OPENAI_SERVICE_ERROR,
            "vertex_ai": self.error_codes.VERTEX_AI_ERROR,
            "google_drive": self.error_codes.GOOGLE_DRIVE_ERROR,
            "google_storage": self.error_codes.GOOGLE_STORAGE_ERROR
        }
        
        error_details = service_errors.get(service, self.error_codes.INTERNAL_SERVER_ERROR)
        if original_error:
            error_details.details = {"original_error": original_error}
        
        return self.create_error_response(error_details)
    
    def handle_processing_error(self, operation: str, original_error: str = None) -> JSONResponse:
        """Handle processing errors"""
        processing_errors = {
            "text_extraction": self.error_codes.TEXT_EXTRACTION_FAILED,
            "embedding_generation": self.error_codes.EMBEDDING_GENERATION_FAILED,
            "chunk_creation": self.error_codes.CHUNK_CREATION_FAILED,
            "batch_processing": self.error_codes.BATCH_PROCESSING_FAILED
        }
        
        error_details = processing_errors.get(operation, self.error_codes.INTERNAL_SERVER_ERROR)
        if original_error:
            error_details.details = {"original_error": original_error}
        
        return self.create_error_response(error_details)
    
    def handle_search_error(self, error_type: str, query: str = None) -> JSONResponse:
        """Handle search-related errors"""
        search_errors = {
            "index_unavailable": self.error_codes.SEARCH_INDEX_UNAVAILABLE,
            "timeout": self.error_codes.SEARCH_TIMEOUT,
            "no_results": self.error_codes.NO_SEARCH_RESULTS
        }
        
        error_details = search_errors.get(error_type, self.error_codes.INTERNAL_SERVER_ERROR)
        if query:
            error_details.details = {"query": query}
        
        return self.create_error_response(error_details)
    
    def handle_unexpected_error(self, exception: Exception, request: Request = None) -> JSONResponse:
        """Handle unexpected errors with full context"""
        error_details = self.error_codes.INTERNAL_SERVER_ERROR
        error_details.details = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": traceback.format_exc()
        }
        
        # Log full error details
        log_debug("Unexpected error occurred", {
            "exception": str(exception),
            "type": type(exception).__name__,
            "endpoint": str(request.url.path) if request else "unknown"
        })
        
        return self.create_error_response(error_details, request)
    
    def get_error_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error analytics and insights"""
        return self.analytics.get_error_statistics(hours)

# Global error handler instance
error_handler = EnhancedErrorHandler()

# Exception handler middleware
async def create_exception_handler():
    """Create FastAPI exception handler"""
    
    async def exception_handler(request: Request, exc: Exception):
        """Global exception handler for FastAPI"""
        
        if isinstance(exc, HTTPException):
            # Handle known HTTP exceptions
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "code": f"HTTP_{exc.status_code}",
                        "message": exc.detail,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
        else:
            # Handle unexpected exceptions
            return error_handler.handle_unexpected_error(exc, request)
    
    return exception_handler