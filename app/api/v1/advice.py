"""Credit Advice API Endpoint - API v1.

═══════════════════════════════════════════════════════════════════════
ENDPOINT: POST /api/v1/advice
═══════════════════════════════════════════════════════════════════════

API Version: v1 (stable)
Status: Production
Contract: Frozen (same input as /predict)

Phase 4C: AI Credit Advisor

This endpoint provides the COMPLETE user-facing credit advisory experience:
1. ML Prediction (probability of default)
2. SHAP Explanations (feature importance)
3. Policy Decision (APPROVE/REVIEW/REJECT)
4. Natural Language Advice (what it means, why, what to do)

This is the primary endpoint for user-facing applications where
human-centered communication is essential.

Response Schema:
{
  "decision": {
    "decision": "APPROVE | REVIEW | REJECT",
    "risk_tier": "LOW | MEDIUM | HIGH",
    "confidence": "HIGH | MEDIUM | LOW",
    "decision_reason": string,
    "recommended_action": string
  },
  "advisor": {
    "summary": string,
    "key_risk_factors": [string],
    "recommended_actions": [string],
    "user_tone": "POSITIVE | NEUTRAL | CAUTIONARY",
    "next_steps": string
  },
  "prediction": {...},
  "explanations": {...},
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
from app.services.credit_advisor import get_credit_advisor, CreditAdvice
from app.api.v1.explain import PredictionSummary, ExplanationDetails

router = APIRouter()
logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class AdvisoryResponse(BaseModel):
    """Complete advisory response with decision + natural language advice.
    
    This is the most user-friendly response format, combining:
    - ML prediction
    - SHAP explanations
    - Policy decision
    - Natural language advisor
    
    Designed for direct consumption by user-facing frontends.
    """
    
    decision: CreditDecision = Field(
        description="Policy-based credit decision"
    )
    
    advisor: CreditAdvice = Field(
        description="Natural language advice and guidance"
    )
    
    prediction: PredictionSummary = Field(
        description="ML prediction summary"
    )
    
    explanations: ExplanationDetails = Field(
        description="SHAP-based feature explanations"
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

@router.post("/advice", response_model=AdvisoryResponse, tags=["advisory"])
async def get_credit_advice(request: CreditRiskRequest) -> AdvisoryResponse:
    """Get complete credit advice with decision and natural language guidance.
    
    Phase 4C: AI Credit Advisor
    
    This endpoint orchestrates the full advisory pipeline:
    1. **ML Prediction**: Run model inference for probability of default
    2. **Explainability**: Compute SHAP values for feature importance
    3. **Policy Decision**: Apply business rules to make final decision
    4. **Natural Language Advisor**: Generate user-friendly advice
    
    The four-layer architecture ensures:
    - ML provides accurate risk assessment
    - Explanations justify the assessment
    - Policy controls the decision
    - Advisor communicates in plain English
    
    Input Schema:
    -------------
    Same as /api/v1/predict endpoint (11 required fields)
    
    Output Schema:
    --------------
    Unified response with four sections:
    - **prediction**: Raw ML output (probability, risk_label)
    - **explanations**: Top 5 risk/protective factors with SHAP values
    - **decision**: Final credit decision (APPROVE/REVIEW/REJECT)
    - **advisor**: Natural language advice and action items
    
    Usage Example:
    --------------
    ```
    POST /api/v1/advice
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
      "decision": {
        "decision": "APPROVE",
        "risk_tier": "LOW",
        "confidence": "HIGH",
        "decision_reason": "Low predicted default risk..."
      },
      "advisor": {
        "summary": "Your credit profile shows strong stability...",
        "key_risk_factors": ["High usage of available credit"],
        "recommended_actions": [
          "Reducing outstanding balances can significantly improve...",
          "Maintaining current positive financial habits..."
        ],
        "user_tone": "POSITIVE",
        "next_steps": "You may proceed with the next stage..."
      }
    }
    ```
    
    Advisory Philosophy:
    -------------------
    - Professional, calm, non-judgmental tone
    - No ML jargon (SHAP, probability, features)
    - Action-oriented guidance
    - Emphasizes improvement path
    - Never shames the user
    
    Args:
        request: Credit risk request (same schema as /predict)
        
    Returns:
        AdvisoryResponse with complete advisory pipeline output
        
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
        "advisory_pipeline_start",
        request_id=request_id,
        timestamp=timestamp,
        credit_score=request.credit_score,
        loan_amount=request.loan_amount
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
            logger.error("advisory_model_not_loaded", request_id=request_id)
            raise RuntimeError("Model not loaded. Cannot generate advice.")
        
        # Run prediction
        prediction_response = model.predict(request)
        prediction_probability = prediction_response.risk_score
        model_version = prediction_response.model_version
        
        stage_times["prediction_ms"] = round((time.time() - stage_start) * 1000, 2)
        
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
        
        # ═══════════════════════════════════════════════════════════════
        # STAGE 4: NATURAL LANGUAGE ADVISOR
        # ═══════════════════════════════════════════════════════════════
        stage_start = time.time()
        
        advisor = get_credit_advisor()
        
        # Generate natural language advice
        credit_advice = advisor.generate_advice(
            decision=credit_decision.decision,
            risk_tier=credit_decision.risk_tier,
            explanation_summary=explanation_summary,
            confidence=credit_decision.confidence,
            override_applied=credit_decision.override_applied
        )
        
        stage_times["advisor_ms"] = round((time.time() - stage_start) * 1000, 2)
        
        # ═══════════════════════════════════════════════════════════════
        # FINAL: BUILD UNIFIED ADVISORY RESPONSE
        # ═══════════════════════════════════════════════════════════════
        total_time_ms = round((time.time() - start_time) * 1000, 2)
        
        logger.info(
            "advisory_pipeline_complete",
            request_id=request_id,
            decision=credit_decision.decision,
            user_tone=credit_advice.user_tone,
            total_time_ms=total_time_ms,
            prediction_ms=stage_times["prediction_ms"],
            explanation_ms=stage_times["explanation_ms"],
            decision_ms=stage_times["decision_ms"],
            advisor_ms=stage_times["advisor_ms"]
        )
        
        return AdvisoryResponse(
            decision=credit_decision,
            advisor=credit_advice,
            prediction=PredictionSummary(**explanation["prediction"]),
            explanations=ExplanationDetails(**explanation["explanations"]),
            request_id=request_id,
            model_version=model_version,
            timestamp=timestamp,
            total_processing_time_ms=total_time_ms,
            pipeline_breakdown=stage_times
        )
        
    except RuntimeError as e:
        logger.error(
            "advisory_pipeline_runtime_error",
            request_id=request_id,
            error=str(e),
            total_time_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise
        
    except Exception as e:
        logger.error(
            "advisory_pipeline_unexpected_error",
            request_id=request_id,
            error=str(e),
            exception_type=type(e).__name__,
            total_time_ms=round((time.time() - start_time) * 1000, 2),
            exc_info=True
        )
        raise
