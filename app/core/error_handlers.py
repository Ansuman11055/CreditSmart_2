"""Centralized error handling for production-grade FastAPI application.

═══════════════════════════════════════════════════════════════════════
PRODUCTION ERROR HANDLING
═══════════════════════════════════════════════════════════════════════

This module provides centralized, consistent error handling across the API with:
- Structured JSON error responses
- Request ID correlation for tracing
- Timestamp tracking
- Stack traces logged but NOT returned to clients
- Consistent error codes and messages

DESIGN PRINCIPLES:
1. All errors return same structure (error_code, message, request_id, timestamp)
2. 4xx errors for client issues (validation, bad input)
3. 5xx errors for server issues (model failures, internal errors)
4. Stack traces logged with exc_info=True but never exposed to clients
5. Request ID enables correlation between logs and client errors

ERROR RESPONSE FORMAT:
{
  "error_code": "VALIDATION_ERROR",
  "message": "Validation failed for field 'creditScore': Input should be less than or equal to 850",
  "request_id": "abc123-def456-ghi789",
  "timestamp": "2026-02-01T12:34:56.789Z",
  "details": {
    "errors": [...]
  }
}

USAGE:
  from app.core.error_handlers import register_error_handlers
  
  app = FastAPI()
  register_error_handlers(app)

═══════════════════════════════════════════════════════════════════════
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

from app.schemas.errors import APIErrorResponse, ErrorCodes, create_error_response

logger = structlog.get_logger(__name__)


def generate_request_id() -> str:
    """Generate unique request ID for error correlation.
    
    Returns:
        UUID string for request tracking
    """
    return str(uuid.uuid4())


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO format.
    
    Returns:
        ISO 8601 timestamp string
    """
    return datetime.now(timezone.utc).isoformat()


def create_error_response_with_metadata(
    error_code: str,
    message: str,
    request: Request,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create error response with request_id and timestamp.
    
    Args:
        error_code: Machine-readable error identifier
        message: Human-readable error description
        request: FastAPI Request object
        details: Optional additional context
        
    Returns:
        Dict with error_code, message, request_id, timestamp, details
    """
    # Try to get request_id from request state (set by middleware)
    request_id = getattr(request.state, "request_id", None) or generate_request_id()
    
    error_dict = {
        "error_code": error_code,
        "message": message,
        "request_id": request_id,
        "timestamp": get_timestamp(),
    }
    
    if details:
        error_dict["details"] = details
    
    return error_dict


# ═══════════════════════════════════════════════════════════════════════
# VALIDATION ERROR HANDLER (HTTP 422)
# ═══════════════════════════════════════════════════════════════════════

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with standardized format.
    
    Returns HTTP 422 with structured error details including request_id.
    Stack traces are logged but NOT returned to client.
    
    Args:
        request: FastAPI Request object
        exc: RequestValidationError from Pydantic
        
    Returns:
        JSONResponse with structured error
    """
    errors = exc.errors()
    request_id = getattr(request.state, "request_id", None) or generate_request_id()
    
    # Extract first error for main message
    first_error = errors[0] if errors else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", [])[1:])  # Skip 'body'
    error_msg = first_error.get("msg", "Validation failed")
    
    # Build details with all validation errors
    details = {
        "errors": [
            {
                "field": ".".join(str(loc) for loc in err.get("loc", [])[1:]),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in errors
        ]
    }
    
    # Log with request_id for correlation
    logger.warning(
        "validation_error",
        request_id=request_id,
        path=request.url.path,
        error_count=len(errors),
        first_field=field,
        # Do NOT log full error details (may contain sensitive input)
    )
    
    error_response = create_error_response_with_metadata(
        error_code=ErrorCodes.VALIDATION_ERROR,
        message=f"Validation failed for field '{field}': {error_msg}" if field else "Request validation failed",
        request=request,
        details=details
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


# ═══════════════════════════════════════════════════════════════════════
# VALUE ERROR HANDLER (HTTP 422)
# ═══════════════════════════════════════════════════════════════════════

async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError with standardized format.
    
    Returns HTTP 422 for domain validation errors.
    Stack traces are logged but NOT returned to client.
    
    Args:
        request: FastAPI Request object
        exc: ValueError exception
        
    Returns:
        JSONResponse with structured error
    """
    request_id = getattr(request.state, "request_id", None) or generate_request_id()
    
    logger.warning(
        "value_error",
        request_id=request_id,
        path=request.url.path,
        error=str(exc),
    )
    
    error_response = create_error_response_with_metadata(
        error_code=ErrorCodes.INVALID_INPUT,
        message=str(exc),
        request=request,
        details={"exception_type": "ValueError"}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


# ═══════════════════════════════════════════════════════════════════════
# RUNTIME ERROR HANDLER (HTTP 500/503)
# ═══════════════════════════════════════════════════════════════════════

async def runtime_error_handler(request: Request, exc: RuntimeError):
    """Handle RuntimeError with standardized format.
    
    Returns HTTP 500 for internal errors (model failures, etc).
    Stack traces are logged with exc_info=True but NOT returned to client.
    
    Args:
        request: FastAPI Request object
        exc: RuntimeError exception
        
    Returns:
        JSONResponse with structured error
    """
    error_message = str(exc)
    request_id = getattr(request.state, "request_id", None) or generate_request_id()
    
    # Determine specific error code based on message
    if "not loaded" in error_message.lower() or "not initialized" in error_message.lower():
        error_code = ErrorCodes.MODEL_NOT_LOADED
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif "prediction" in error_message.lower() or "inference" in error_message.lower():
        error_code = ErrorCodes.INFERENCE_FAILED
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        error_code = ErrorCodes.INTERNAL_ERROR
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # Log with full exception info (stack trace) but don't return to client
    logger.error(
        "runtime_error",
        request_id=request_id,
        path=request.url.path,
        error=error_message,
        error_code=error_code,
        exc_info=True,  # Include stack trace in logs
    )
    
    error_response = create_error_response_with_metadata(
        error_code=error_code,
        message=error_message,
        request=request,
        details={"exception_type": "RuntimeError"}
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


# ═══════════════════════════════════════════════════════════════════════
# GENERIC EXCEPTION HANDLER (HTTP 500) - CATCH-ALL
# ═══════════════════════════════════════════════════════════════════════

async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected exceptions.
    
    Returns HTTP 500 with generic error message.
    Stack traces are logged with exc_info=True but NOT returned to client.
    
    This is the last line of defense for any unhandled exceptions.
    
    Args:
        request: FastAPI Request object
        exc: Any unhandled exception
        
    Returns:
        JSONResponse with structured error
    """
    request_id = getattr(request.state, "request_id", None) or generate_request_id()
    
    # Log with full exception info (stack trace) for debugging
    logger.error(
        "unexpected_error",
        request_id=request_id,
        path=request.url.path,
        error=str(exc),
        exception_type=type(exc).__name__,
        exc_info=True,  # Include stack trace in logs (NOT in response)
    )
    
    # Return generic message (don't leak internal details)
    error_response = create_error_response_with_metadata(
        error_code=ErrorCodes.INTERNAL_ERROR,
        message="An unexpected error occurred. Please try again or contact support.",
        request=request,
        details={
            "exception_type": type(exc).__name__,
            # Do NOT include stack trace or internal details
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


# ═══════════════════════════════════════════════════════════════════════
# REQUEST ID MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════

@staticmethod
async def request_id_middleware(request: Request, call_next):
    """Middleware to add request_id to all requests for correlation.
    
    Generates a unique request_id and stores it in request.state for use
    by error handlers and logging.
    
    Args:
        request: FastAPI Request object
        call_next: Next middleware or endpoint
        
    Returns:
        Response with X-Request-ID header
    """
    # Generate or extract request ID
    request_id = request.headers.get("X-Request-ID") or generate_request_id()
    request.state.request_id = request_id
    
    # Log request with request_id
    logger.info(
        "request_received",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    
    # Process request
    response = await call_next(request)
    
    # Add request_id to response headers for client correlation
    response.headers["X-Request-ID"] = request_id
    
    return response


# ═══════════════════════════════════════════════════════════════════════
# REGISTRATION FUNCTION
# ═══════════════════════════════════════════════════════════════════════

def register_error_handlers(app: FastAPI) -> None:
    """Register all centralized error handlers with FastAPI app.
    
    This function should be called once during application startup to
    register all exception handlers and middleware.
    
    Args:
        app: FastAPI application instance
        
    Usage:
        from app.core.error_handlers import register_error_handlers
        
        app = FastAPI()
        register_error_handlers(app)
    """
    # Register exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(RuntimeError, runtime_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # Register request ID middleware
    app.middleware("http")(request_id_middleware)
    
    logger.info(
        "error_handlers_registered",
        handlers=["validation", "value_error", "runtime_error", "generic"],
        middleware=["request_id"]
    )
