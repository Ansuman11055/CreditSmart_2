"""Credit Decision API Endpoint - API v1.

═══════════════════════════════════════════════════════════════════════
ENDPOINT: POST /api/v1/decision
═══════════════════════════════════════════════════════════════════════

API Version: v1 (stable)
Status: Production
Contract: Frozen (same input as /predict)

Phase 4B: Decision Policy Engine

This endpoint provides end-to-end credit decision flow:
1. ML Prediction (probability of default)
2. SHAP Explanations (feature importance)
3. Policy Decision (APPROVE/REVIEW/REJECT)

This is the COMPLETE decision pipeline suitable for production fintech systems.

Response Schema:
{
  "prediction": {
    "probability": float,
    "risk_label": "LOW | MEDIUM | HIGH"
  },
  "explanations": {
    "top_risk_factors": [...],
    "top_protective_factors": [...]
  },
  "decision": {
    "decision": "APPROVE | REVIEW | REJECT",
    "risk_tier": "LOW | MEDIUM | HIGH",
    "confidence": "HIGH | MEDIUM | LOW",
    "decision_reason": string,
    "recommended_action": string
  },
  "request_id": string,
  "model_version": string,
  "timestamp": string
}

═══════════════════════════════════════════════════════════════════════
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import structlog
import uuid
import time
from datetime import datetime, timezone

from app.schemas.request import CreditRiskRequest
from app.ml.model import get_model
from app.ml.explainability import get_explainability_engine
from app.services.decision_engine import get_decision_engine, CreditDecision
from app.api.v1.explain import PredictionSummary, ExplanationDetails

router = APIRouter()
logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class UnifiedDecisionResponse(BaseModel):
    """Complete unified decision response with ML + explainability + policy.
    
    This is the primary response schema for production credit decisioning.
    It combines all three layers:
    - ML prediction
    - SHAP explanations
    - Policy decision
    """
    
    prediction: PredictionSummary = Field(
        description="ML prediction summary"
    )
    
    explanations: ExplanationDetails = Field(
        description="SHAP-based feature explanations"
    )
    
    decision: CreditDecision = Field(
        description="Final policy-based credit decision"
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
    
    total_processing_time_ms: float = Field(
        description="Total end-to-end processing time"
    )
    
    pipeline_breakdown: Dict[str, float] = Field(
        description="Time breakdown by pipeline stage (ms)"
    )


# ═══════════════════════════════════════════════════════════════════════
# ENDPOINT IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════

@router.post("/decision", response_model=UnifiedDecisionResponse, tags=["decision"])
async def make_credit_decision(request: CreditRiskRequest) -> UnifiedDecisionResponse:
    """Make complete credit decision with prediction, explanation, and policy.
    
    Phase 4B: End-to-End Decision Pipeline
    
    This endpoint orchestrates the full decision flow:
    1. **ML Prediction**: Run model inference for probability of default
    2. **Explainability**: Compute SHAP values for feature importance
    3. **Policy Decision**: Apply business rules to make final decision
    
    The three-layer architecture ensures:
    - ML informs the decision
    - Explanations justify the decision
    - Policy controls the decision
    
    Input Schema:
    -------------
    Same as /api/v1/predict endpoint (11 required fields)
    
    Output Schema:
    --------------
    Unified response with three sections:
    - **prediction**: Raw ML output (probability, risk_label)
    - **explanations**: Top 5 risk/protective factors with SHAP values
    - **decision**: Final credit decision (APPROVE/REVIEW/REJECT)
    
    Usage Example:
    --------------
    ```
    POST /api/v1/decision
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
        "top_risk_factors": [...],
        "top_protective_factors": [...]
      },
      "decision": {
        "decision": "APPROVE",
        "risk_tier": "LOW",
        "confidence": "HIGH",
        "decision_reason": "Low predicted default risk with stable financial profile.",
        "recommended_action": "Proceed with standard loan processing and documentation."
      }
    }
    ```
    
    Decision Logic:
    ---------------
    - **Risk Tiers**: LOW (<0.30), MEDIUM (0.30-0.60), HIGH (≥0.60)
    - **Base Mapping**: LOW → APPROVE, MEDIUM → REVIEW, HIGH → REJECT
    - **Overrides**: Low confidence always requires REVIEW
    - **Safety**: Never auto-reject without high confidence + explanations
    
    Args:
        request: Credit risk request (same schema as /predict)
        
    Returns:
        UnifiedDecisionResponse with complete decision pipeline output
        
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
        "decision_pipeline_start",
        request_id=request_id,
        timestamp=timestamp,
        credit_score=request.credit_score,
        loan_amount=request.loan_amount,
        purpose=request.purpose
    )
    
    # Track timing for each stage
    stage_times: Dict[str, float] = {}
    
    try:
        # ═══════════════════════════════════════════════════════════════
        # STAGE 1: ML PREDICTION
        # ═══════════════════════════════════════════════════════════════
        stage_start = time.time()
        
        model = get_model()
        if not model.is_loaded:
            logger.error("decision_model_not_loaded", request_id=request_id)
            raise RuntimeError("Model not loaded. Cannot make decision.")
        
        # Run prediction
        prediction_response = model.predict(request)
        prediction_probability = prediction_response.risk_score
        model_version = prediction_response.model_version
        
        stage_times["prediction_ms"] = round((time.time() - stage_start) * 1000, 2)
        
        logger.info(
            "decision_prediction_complete",
            request_id=request_id,
            probability=prediction_probability,
            stage_time_ms=stage_times["prediction_ms"]
        )
        
        # ═══════════════════════════════════════════════════════════════
        # STAGE 2: SHAP EXPLANATIONS
        # ═══════════════════════════════════════════════════════════════
        stage_start = time.time()
        
        explainer = get_explainability_engine()
        explanation = explainer.explain_prediction(
            request=request,
            prediction_probability=prediction_probability,
            top_n=5
        )
        
        stage_times["explanation_ms"] = round((time.time() - stage_start) * 1000, 2)
        
        logger.info(
            "decision_explanation_complete",
            request_id=request_id,
            model_confidence=explanation["model_confidence"],
            stage_time_ms=stage_times["explanation_ms"]
        )
        
        # ═══════════════════════════════════════════════════════════════
        # STAGE 3: POLICY DECISION
        # ═══════════════════════════════════════════════════════════════
        stage_start = time.time()
        
        decision_engine = get_decision_engine()
        
        # Prepare explanation summary for decision engine
        explanation_summary = {
            "top_risk_factors": explanation["explanations"]["top_risk_factors"],
            "top_protective_factors": explanation["explanations"]["top_protective_factors"]
        }
        
        # Make policy decision
        credit_decision = decision_engine.make_decision(
            probability_of_default=prediction_probability,
            model_confidence=explanation["model_confidence"],
            explanation_summary=explanation_summary
        )
        
        stage_times["decision_ms"] = round((time.time() - stage_start) * 1000, 2)
        
        logger.info(
            "decision_policy_complete",
            request_id=request_id,
            decision=credit_decision.decision,
            risk_tier=credit_decision.risk_tier,
            override_applied=credit_decision.override_applied,
            stage_time_ms=stage_times["decision_ms"]
        )
        
        # ═══════════════════════════════════════════════════════════════
        # FINAL: BUILD UNIFIED RESPONSE
        # ═══════════════════════════════════════════════════════════════
        total_time_ms = round((time.time() - start_time) * 1000, 2)
        
        logger.info(
            "decision_pipeline_complete",
            request_id=request_id,
            decision=credit_decision.decision,
            total_time_ms=total_time_ms,
            prediction_ms=stage_times["prediction_ms"],
            explanation_ms=stage_times["explanation_ms"],
            decision_ms=stage_times["decision_ms"]
        )
        
        return UnifiedDecisionResponse(
            prediction=PredictionSummary(**explanation["prediction"]),
            explanations=ExplanationDetails(**explanation["explanations"]),
            decision=credit_decision,
            request_id=request_id,
            model_version=model_version,
            timestamp=timestamp,
            total_processing_time_ms=total_time_ms,
            pipeline_breakdown=stage_times
        )
        
    except RuntimeError as e:
        logger.error(
            "decision_pipeline_runtime_error",
            request_id=request_id,
            error=str(e),
            total_time_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise
        
    except Exception as e:
        logger.error(
            "decision_pipeline_unexpected_error",
            request_id=request_id,
            error=str(e),
            exception_type=type(e).__name__,
            total_time_ms=round((time.time() - start_time) * 1000, 2),
            exc_info=True
        )
        raise


# ═══════════════════════════════════════════════════════════════════════
# HELPER ENDPOINT: DECISION POLICIES INFO
# ═══════════════════════════════════════════════════════════════════════

class PolicyInfoResponse(BaseModel):
    """Decision policy configuration information."""
    
    risk_tiers: Dict[str, str] = Field(
        description="Risk tier thresholds"
    )
    
    decision_mapping: Dict[str, str] = Field(
        description="Risk tier to decision mapping"
    )
    
    overrides: list[str] = Field(
        description="Mandatory override rules"
    )


@router.get("/decision/policies", response_model=PolicyInfoResponse, tags=["decision"])
async def get_decision_policies() -> PolicyInfoResponse:
    """Get current decision policy configuration.
    
    This endpoint returns the active policy rules and thresholds
    for transparency and auditability.
    
    Returns:
        PolicyInfoResponse with current configuration
    """
    from app.services.decision_engine import PolicyThresholds
    
    thresholds = PolicyThresholds()
    
    return PolicyInfoResponse(
        risk_tiers={
            "LOW": f"PD < {thresholds.LOW_RISK_THRESHOLD}",
            "MEDIUM": f"{thresholds.LOW_RISK_THRESHOLD} ≤ PD < {thresholds.MEDIUM_RISK_THRESHOLD}",
            "HIGH": f"PD ≥ {thresholds.MEDIUM_RISK_THRESHOLD}"
        },
        decision_mapping={
            "LOW + HIGH/MEDIUM confidence": "APPROVE",
            "MEDIUM risk": "REVIEW",
            "HIGH risk": "REJECT"
        },
        overrides=[
            "LOW confidence always requires REVIEW",
            "Missing explanations require REVIEW",
            "Never auto-reject without HIGH confidence + explanations",
            f"≥{thresholds.STRONG_NEGATIVE_FACTORS_THRESHOLD} strong risk factors escalate risk tier"
        ]
    )
