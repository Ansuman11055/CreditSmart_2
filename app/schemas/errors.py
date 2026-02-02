"""Standardized error response schemas for API contract stability.

All API errors return this consistent format for predictable frontend handling.
"""

from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class APIErrorResponse(BaseModel):
    """Standardized error response for all API endpoints.
    
    This schema ensures consistent error handling across the entire API.
    Frontend can reliably parse and display errors using this format.
    
    Fields:
        error_code: Machine-readable error identifier (e.g., "MODEL_NOT_LOADED")
        message: Human-readable error description
        details: Optional additional context (dict or string)
    
    Example:
        {
          "error_code": "VALIDATION_ERROR",
          "message": "Invalid input: credit_score must be between 300 and 850",
          "details": {
            "field": "credit_score",
            "value": 950,
            "constraint": "range_300_850"
          }
        }
    """
    
    error_code: str = Field(
        ...,
        description="Machine-readable error code (UPPER_SNAKE_CASE)",
        examples=["MODEL_NOT_LOADED", "VALIDATION_ERROR", "INFERENCE_FAILED"]
    )
    
    message: str = Field(
        ...,
        description="Human-readable error message for display",
        examples=[
            "Model not loaded. Service is starting up.",
            "Invalid input: credit_score out of range.",
            "Prediction failed due to internal error."
        ]
    )
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional additional context for debugging",
        examples=[
            {"field": "credit_score", "value": 950, "min": 300, "max": 850},
            {"model_version": "ml_v1.0.0", "loaded": False},
            None
        ]
    )


# Standard error codes for consistent error handling
class ErrorCodes:
    """Enumeration of standard API error codes.
    
    These codes provide machine-readable error identification for frontend.
    """
    
    # 4xx Client Errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    EXTRA_FIELD = "EXTRA_FIELD"
    TYPE_ERROR = "TYPE_ERROR"
    RANGE_ERROR = "RANGE_ERROR"
    
    # 5xx Server Errors
    MODEL_NOT_LOADED = "MODEL_NOT_LOADED"
    INFERENCE_FAILED = "INFERENCE_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    
    # Feature validation
    FEATURE_COUNT_MISMATCH = "FEATURE_COUNT_MISMATCH"
    FEATURE_TYPE_ERROR = "FEATURE_TYPE_ERROR"


def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> APIErrorResponse:
    """Factory function to create standardized error responses.
    
    Args:
        error_code: Machine-readable error identifier
        message: Human-readable error description
        details: Optional additional context
        
    Returns:
        APIErrorResponse with consistent format
        
    Example:
        >>> error = create_error_response(
        ...     error_code="MODEL_NOT_LOADED",
        ...     message="Model not available",
        ...     details={"model_version": "ml_v1.0.0"}
        ... )
    """
    return APIErrorResponse(
        error_code=error_code,
        message=message,
        details=details
    )
