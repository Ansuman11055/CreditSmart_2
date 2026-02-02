"""UX-Safe response wrapper for frontend-safe error handling.

Phase 3B-2: API Contract Hardening & UX-Safe Failure Handling

This module provides a GUARANTEED response contract that ALWAYS returns
the same structure, even during failures. This prevents frontend UI breaks.

GUARANTEE:
Every /predict response will have these fields (ALL required):
  - status: "success" | "error"
  - request_id: string (UUID)
  - model_version: string (or "unknown" on error)
  - prediction: number | null
  - confidence: number | null (0.0-1.0)
  - error: string | null

NEVER null/missing fields. NEVER stack traces. ALWAYS valid JSON.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from app.schemas.response import CreditRiskResponse


class UXSafePredictionResponse(BaseModel):
    """Frontend-safe prediction response with guaranteed contract.
    
    This wrapper ensures the frontend ALWAYS receives a predictable structure,
    even when the backend encounters errors. All fields are ALWAYS present.
    
    Contract Guarantees:
    ═══════════════════════════════════════════════════════════════════════
    1. ALWAYS returns these 6 fields (never null for fields themselves)
    2. status indicates success/error (never missing)
    3. request_id for tracking (always UUID string)
    4. prediction/confidence are null on error (explicit null, not missing)
    5. error is null on success, string on error (never missing field)
    6. model_version is "unknown" if model not loaded
    
    Response Modes:
    ═══════════════════════════════════════════════════════════════════════
    SUCCESS:
      {
        "status": "success",
        "request_id": "abc-123",
        "model_version": "ml_v1.0.0",
        "prediction": 0.15,
        "confidence": 0.92,
        "error": null,
        "data": { ...full CreditRiskResponse... }
      }
    
    ERROR:
      {
        "status": "error",
        "request_id": "abc-123",
        "model_version": "unknown",
        "prediction": null,
        "confidence": null,
        "error": "Model not loaded. Please try again later.",
        "data": null
      }
    
    Frontend Usage:
    ═══════════════════════════════════════════════════════════════════════
    if (response.status === "success") {
      // Use response.prediction, response.data.risk_level, etc.
      displayResult(response.data);
    } else {
      // Show error message to user
      showError(response.error);
    }
    
    No need to check for missing fields - ALL fields are ALWAYS present.
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # GUARANTEED FIELDS (ALWAYS PRESENT)
    # ═══════════════════════════════════════════════════════════════════════
    
    status: Literal["success", "error"] = Field(
        ...,
        description="Response status. 'success' if prediction succeeded, 'error' if failed."
    )
    
    request_id: str = Field(
        ...,
        description="Unique request identifier (UUID) for tracking and debugging."
    )
    
    model_version: str = Field(
        ...,
        description="Model version used for prediction. 'unknown' if model not loaded."
    )
    
    prediction: Optional[float] = Field(
        ...,  # Field is required, but value can be None
        description="Risk score [0.0-1.0]. null if error occurred.",
        ge=0.0,
        le=1.0
    )
    
    confidence: Optional[float] = Field(
        ...,  # Field is required, but value can be None
        description="Model confidence [0.0-1.0]. null if error occurred.",
        ge=0.0,
        le=1.0
    )
    
    error: Optional[str] = Field(
        ...,  # Field is required, but value can be None
        description="Error message. null if prediction succeeded."
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # OPTIONAL DETAILED DATA (ONLY ON SUCCESS)
    # ═══════════════════════════════════════════════════════════════════════
    
    data: Optional[CreditRiskResponse] = Field(
        default=None,
        description="Full prediction details. Only present on success (status='success')."
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # FACTORY METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    @classmethod
    def success(
        cls,
        request_id: str,
        prediction_response: CreditRiskResponse
    ) -> "UXSafePredictionResponse":
        """Create success response with full prediction data.
        
        Args:
            request_id: Unique request identifier
            prediction_response: Full prediction details from ML model
            
        Returns:
            UXSafePredictionResponse with status='success'
        """
        return cls(
            status="success",
            request_id=request_id,
            model_version=prediction_response.model_version,
            prediction=prediction_response.risk_score,
            confidence=_calculate_confidence_score(prediction_response.risk_score),
            error=None,
            data=prediction_response
        )
    
    @classmethod
    def create_error(
        cls,
        request_id: str,
        error_message: str,
        model_version: str = "unknown"
    ) -> "UXSafePredictionResponse":
        """Create error response with null predictions.
        
        Args:
            request_id: Unique request identifier
            error_message: Human-readable error description
            model_version: Model version if available, else "unknown"
            
        Returns:
            UXSafePredictionResponse with status='error'
        """
        return cls(
            status="error",
            request_id=request_id,
            model_version=model_version,
            prediction=None,
            confidence=None,
            error=error_message,
            data=None
        )


def _calculate_confidence_score(risk_score: float) -> float:
    """Calculate numeric confidence score from risk probability.
    
    High confidence when probability is extreme (near 0 or 1).
    Low confidence when probability is uncertain (near 0.5).
    
    Args:
        risk_score: Probability of default [0.0-1.0]
        
    Returns:
        Confidence score [0.0-1.0] where:
          1.0 = very confident (extreme probability)
          0.0 = not confident (uncertain, near 0.5)
    
    Formula:
        confidence = 2 * |risk_score - 0.5|
        - risk_score=0.0 → confidence=1.0 (very confident: no risk)
        - risk_score=0.5 → confidence=0.0 (uncertain: 50/50)
        - risk_score=1.0 → confidence=1.0 (very confident: certain default)
    """
    return round(2.0 * abs(risk_score - 0.5), 4)


# Schema version constants for API versioning
REQUEST_SCHEMA_VERSION = "v1"
RESPONSE_SCHEMA_VERSION = "v1"
