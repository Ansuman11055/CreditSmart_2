"""Explainability API endpoint - API v1.

═══════════════════════════════════════════════════════════════════════
ENDPOINT: POST /api/v1/explain
═══════════════════════════════════════════════════════════════════════

API Version: v1 (stable)
Status: Production
Contract: Frozen (same input as /predict)

Phase 4A: Trust & Explainability Layer

This endpoint provides SHAP-based explanations for credit risk predictions,
converting raw ML outputs into interpretable, human-readable insights.

Features:
- Same input schema as /predict endpoint
- SHAP-based feature importance
- Top risk-increasing factors
- Top risk-decreasing (protective) factors
- Model confidence assessment
- Clean, frontend-ready JSON

Response Schema:
{
  "prediction": {
    "probability": float (0.0-1.0),
    "risk_label": "LOW | MEDIUM | HIGH"
  },
  "explanations": {
    "top_risk_factors": [
      {
        "feature": string (human-readable),
        "impact": float (SHAP value),
        "impact_percentage": float (0-100),
        "direction": "increase"
      }
    ],
    "top_protective_factors": [
      {
        "feature": string (human-readable),
        "impact": float (negative SHAP value),
        "impact_percentage": float (0-100),
        "direction": "decrease"
      }
    ]
  },
  "model_confidence": "HIGH | MEDIUM | LOW",
  "request_id": string (UUID),
  "model_version": string
}

═══════════════════════════════════════════════════════════════════════
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import structlog
import uuid
import time
from datetime import datetime, timezone

from app.schemas.request import CreditRiskRequest
from app.ml.model import get_model
from app.ml.explainability import get_explainability_engine

router = APIRouter()
logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class FeatureContribution(BaseModel):
    """Single feature contribution to prediction."""
    
    feature: str = Field(
        description="Human-readable feature name"
    )
    
    impact: float = Field(
        description="SHAP value (positive = risk increase, negative = risk decrease)"
    )
    
    impact_percentage: float = Field(
        description="Relative contribution as percentage (0-100)",
        ge=0,
        le=100
    )
    
    direction: Literal["increase", "decrease"] = Field(
        description="Whether feature increases or decreases risk"
    )


class PredictionSummary(BaseModel):
    """Prediction summary for explainability."""
    
    probability: float = Field(
        description="Predicted probability of default (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    risk_label: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Categorical risk level"
    )


class ExplanationDetails(BaseModel):
    """Detailed SHAP-based explanations."""
    
    top_risk_factors: List[FeatureContribution] = Field(
        description="Features that increase predicted risk (positive SHAP values)"
    )
    
    top_protective_factors: List[FeatureContribution] = Field(
        description="Features that decrease predicted risk (negative SHAP values)"
    )


class ExplainResponse(BaseModel):
    """Complete explanation response."""
    
    prediction: PredictionSummary = Field(
        description="Prediction summary"
    )
    
    explanations: ExplanationDetails = Field(
        description="SHAP-based feature contributions"
    )
    
    model_confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Model's confidence in prediction based on SHAP value distribution"
    )
    
    request_id: str = Field(
        description="Unique request identifier for tracking"
    )
    
    model_version: str = Field(
        description="Model version used for prediction"
    )
    
    timestamp: str = Field(
        description="ISO 8601 timestamp (UTC)"
    )
    
    inference_time_ms: float = Field(
        description="Total computation time in milliseconds"
    )
    
    base_value: Optional[float] = Field(
        default=None,
        description="SHAP base value (expected model output)"
    )
    
    note: Optional[str] = Field(
        default=None,
        description="Additional notes (e.g., fallback to heuristics)"
    )


# ═══════════════════════════════════════════════════════════════════════
# ENDPOINT IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════

@router.post("/explain", response_model=ExplainResponse, tags=["explainability"])
async def explain_prediction(request: CreditRiskRequest) -> ExplainResponse:
    """Generate SHAP-based explanation for credit risk prediction.
    
    Phase 4A: Trust & Explainability Layer
    
    This endpoint provides interpretable explanations by:
    1. Running ML prediction
    2. Computing SHAP values
    3. Identifying top risk contributors
    4. Identifying top protective factors
    5. Converting to human-readable format
    
    Input Schema:
    -------------
    Same as /api/v1/predict endpoint (11 required fields)
    
    Output Schema:
    --------------
    - prediction: Probability and risk label
    - explanations: Top 5 risk/protective factors with SHAP values
    - model_confidence: Confidence assessment
    - metadata: request_id, model_version, timing
    
    Usage Example:
    --------------
    ```
    POST /api/v1/explain
    {
      "annual_income": 75000,
      "monthly_debt": 1200,
      "credit_score": 720,
      "loan_amount": 25000,
      "loan_term_months": 60,
      "employment_length_years": 5,
      "home_ownership": "MORTGAGE",
      "purpose": "debt_consolidation",
      "number_of_open_accounts": 8,
      "delinquencies_2y": 0,
      "inquiries_6m": 1
    }
    ```
    
    Response Example:
    -----------------
    ```
    {
      "prediction": {
        "probability": 0.23,
        "risk_label": "LOW"
      },
      "explanations": {
        "top_risk_factors": [
          {
            "feature": "Monthly Debt",
            "impact": 0.08,
            "impact_percentage": 15.3,
            "direction": "increase"
          }
        ],
        "top_protective_factors": [
          {
            "feature": "Credit Score",
            "impact": -0.12,
            "impact_percentage": 22.8,
            "direction": "decrease"
          }
        ]
      },
      "model_confidence": "HIGH"
    }
    ```
    
    Args:
        request: Credit risk request (same schema as /predict)
        
    Returns:
        ExplainResponse with prediction and SHAP explanations
        
    Response Codes:
        200: Success
        422: Validation error
        500: Internal error
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    start_time = time.time()
    timestamp = datetime.now(timezone.utc).isoformat()
    
    logger.info(
        "explain_request_received",
        request_id=request_id,
        timestamp=timestamp,
        credit_score_band=_get_credit_band(request.credit_score),
        loan_amount_band=_get_loan_band(request.loan_amount)
    )
    
    try:
        # Get model and run prediction
        model = get_model()
        
        if not model.is_loaded:
            logger.error("explain_model_not_loaded", request_id=request_id)
            raise RuntimeError("Model not loaded. Cannot generate explanation.")
        
        # Run prediction to get probability
        prediction_response = model.predict(request)
        prediction_probability = prediction_response.risk_score
        model_version = prediction_response.model_version
        
        # Get explainability engine
        explainer = get_explainability_engine()
        
        # Generate SHAP-based explanation
        explanation = explainer.explain_prediction(
            request=request,
            prediction_probability=prediction_probability,
            top_n=5
        )
        
        # Calculate total time
        total_time_ms = round((time.time() - start_time) * 1000, 2)
        
        # Log completion
        logger.info(
            "explain_complete",
            request_id=request_id,
            risk_label=explanation["prediction"]["risk_label"],
            model_confidence=explanation["model_confidence"],
            risk_factors_count=len(explanation["explanations"]["top_risk_factors"]),
            protective_factors_count=len(explanation["explanations"]["top_protective_factors"]),
            inference_time_ms=total_time_ms
        )
        
        # Build response
        return ExplainResponse(
            prediction=PredictionSummary(**explanation["prediction"]),
            explanations=ExplanationDetails(**explanation["explanations"]),
            model_confidence=explanation["model_confidence"],
            request_id=request_id,
            model_version=model_version,
            timestamp=timestamp,
            inference_time_ms=total_time_ms,
            base_value=explanation.get("base_value"),
            note=explanation.get("note")
        )
        
    except RuntimeError as e:
        logger.error(
            "explain_runtime_error",
            request_id=request_id,
            error=str(e),
            total_time_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise
        
    except Exception as e:
        logger.error(
            "explain_unexpected_error",
            request_id=request_id,
            error=str(e),
            exception_type=type(e).__name__,
            total_time_ms=round((time.time() - start_time) * 1000, 2),
            exc_info=True
        )
        raise


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def _get_credit_band(credit_score: int) -> str:
    """Convert credit score to privacy-safe band."""
    if credit_score >= 750:
        return "EXCELLENT"
    elif credit_score >= 700:
        return "GOOD"
    elif credit_score >= 650:
        return "FAIR"
    else:
        return "POOR"


def _get_loan_band(loan_amount: float) -> str:
    """Convert loan amount to privacy-safe band."""
    if loan_amount < 5000:
        return "SMALL"
    elif loan_amount < 15000:
        return "MEDIUM"
    elif loan_amount < 30000:
        return "LARGE"
    else:
        return "VERY_LARGE"


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4D: GET ENDPOINT FOR CACHED EXPLANATIONS
# ═══════════════════════════════════════════════════════════════════════

@router.get(
    "/explain/{prediction_id}",
    response_model=ExplainResponse,
    tags=["explainability"],
    summary="Get cached explanation for a prediction",
    description="""
    Retrieve a previously cached explanation by prediction request ID.
    
    **Phase 4D Explainability** - This endpoint fetches explanations that
    were generated and cached during the original /predict call.
    
    **No recomputation** - Explanations are pre-computed and cached for performance.
    
    **Cache TTL** - Explanations expire after 1 hour (same as predictions).
    """
)
async def get_cached_explanation(prediction_id: str) -> ExplainResponse:
    """Get cached explanation for a prediction (Phase 4D Explainability).
    
    Args:
        prediction_id: Request ID from original /predict call
        
    Returns:
        ExplainResponse with SHAP-based explanations
        
    Raises:
        HTTPException: 404 if not found, 500 on error
    """
    from fastapi import HTTPException
    from app.core.prediction_cache import get_prediction_cache
    
    start_time = time.time()
    
    logger.info(
        "cached_explanation_request",
        prediction_id=prediction_id
    )
    
    try:
        # Get cache instance
        cache = get_prediction_cache()
        
        # Retrieve explanation from cache
        explanation_data = cache.get_explanation(prediction_id)
        
        if explanation_data is None:
            logger.warning(
                "cached_explanation_not_found",
                prediction_id=prediction_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No explanation found for prediction ID: {prediction_id}. "
                       "Explanation may have expired or was never generated."
            )
        
        # Build response from cached data
        total_time_ms = round((time.time() - start_time) * 1000, 2)
        
        # Convert cached data to response format
        response = ExplainResponse(
            prediction=PredictionSummary(
                probability=explanation_data.get("risk_score", 0.0),
                risk_label=explanation_data.get("risk_band", "unknown").upper()
            ),
            explanations=ExplanationDetails(
                top_risk_factors=[
                    FeatureContribution(
                        feature=f["human_name"],
                        impact=f["shap_value"],
                        impact_percentage=abs(f["shap_value"]) * 100,  # Simple percentage
                        direction="increase"
                    )
                    for f in explanation_data.get("top_negative_features", [])
                ],
                top_protective_factors=[
                    FeatureContribution(
                        feature=f["human_name"],
                        impact=f["shap_value"],
                        impact_percentage=abs(f["shap_value"]) * 100,
                        direction="decrease"
                    )
                    for f in explanation_data.get("top_positive_features", [])
                ]
            ),
            model_confidence="MEDIUM",  # Default for cached
            request_id=prediction_id,
            model_version=explanation_data.get("model_version", "unknown"),
            timestamp=datetime.now(timezone.utc).isoformat(),
            inference_time_ms=0.0,  # Cached, no inference
            base_value=None,
            note="Cached explanation retrieved from Phase 4D explainability service"
        )
        
        logger.info(
            "cached_explanation_retrieved",
            prediction_id=prediction_id,
            risk_band=explanation_data.get("risk_band"),
            total_time_ms=total_time_ms
        )
        
        return response
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            "cached_explanation_error",
            prediction_id=prediction_id,
            error=str(e),
            exception_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve explanation. Please try again."
        )

