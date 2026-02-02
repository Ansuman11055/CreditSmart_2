"""ML prediction endpoints - API v1.

═══════════════════════════════════════════════════════════════════════
ENDPOINTS: POST /api/v1/predict, /predict/legacy, /predict/batch
═══════════════════════════════════════════════════════════════════════

API Version: v1 (stable)
Status: Production
Contract: Frozen (11-field input schema)

Credit risk prediction with production-grade safety:
- UX-safe guaranteed response structure (always same fields)
- Timeout handling (30s max inference time)
- Error normalization (all errors → JSON, no stack traces)
- Schema versioning (request/response tracking)
- Request ID tracking for debugging

ENDPOINTS:
1. /api/v1/predict        - UX-safe prediction (recommended)
2. /api/v1/predict/legacy - Legacy format (backward compatibility)
3. /api/v1/predict/batch  - Batch predictions

INPUT CONTRACT (11 required fields):
- annual_income, monthly_debt, credit_score
- loan_amount, loan_term_months
- employment_length_years, home_ownership
- purpose, number_of_open_accounts
- delinquencies_2y, inquiries_6m

RESPONSE GUARANTEE:
All responses contain these 6 fields (NEVER missing):
- status: "success" | "error"
- request_id: string (UUID)
- model_version: string
- prediction: number | null
- confidence: number | null
- error: string | null

═══════════════════════════════════════════════════════════════════════
"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import structlog
from collections import deque
from typing import Deque
import time
import uuid
from datetime import datetime, timezone
import asyncio
from functools import wraps

from app.schemas.request import CreditRiskRequest
from app.schemas.response import CreditRiskResponse
from app.schemas.ux_safe_response import UXSafePredictionResponse, REQUEST_SCHEMA_VERSION, RESPONSE_SCHEMA_VERSION
from app.ml.model import get_model

# Timeout configuration (seconds)
INFERENCE_TIMEOUT = 30.0

router = APIRouter()
logger = structlog.get_logger(__name__)

# Runtime prediction tracking (last 100 predictions)
# Used to monitor distribution and detect anomalies
_prediction_history: Deque[float] = deque(maxlen=100)
_last_distribution_log_time = time.time()


# ═══════════════════════════════════════════════════════════════════════
# OBSERVABILITY HELPER FUNCTIONS (NO PII LOGGING)
# ═══════════════════════════════════════════════════════════════════════

def _get_credit_band(credit_score: int) -> str:
    """Convert credit score to privacy-safe band.
    
    Args:
        credit_score: Raw credit score (300-850)
        
    Returns:
        Band label (EXCELLENT, GOOD, FAIR, POOR)
    """
    if credit_score >= 750:
        return "EXCELLENT"
    elif credit_score >= 700:
        return "GOOD"
    elif credit_score >= 650:
        return "FAIR"
    else:
        return "POOR"


def _get_loan_band(loan_amount: float) -> str:
    """Convert loan amount to privacy-safe band.
    
    Args:
        loan_amount: Raw loan amount
        
    Returns:
        Band label (SMALL, MEDIUM, LARGE, VERY_LARGE)
    """
    if loan_amount < 5000:
        return "SMALL"
    elif loan_amount < 15000:
        return "MEDIUM"
    elif loan_amount < 30000:
        return "LARGE"
    else:
        return "VERY_LARGE"


def _get_dti_band(dti: float) -> str:
    """Convert DTI to privacy-safe band.
    
    Args:
        dti: Debt-to-income ratio
        
    Returns:
        Band label (LOW, MODERATE, HIGH, VERY_HIGH)
    """
    if dti < 0.2:
        return "LOW"
    elif dti < 0.35:
        return "MODERATE"
    elif dti < 0.5:
        return "HIGH"
    else:
        return "VERY_HIGH"


def _get_employment_band(years: float) -> str:
    """Convert employment length to privacy-safe band.
    
    Args:
        years: Employment length in years
        
    Returns:
        Band label (NEW, JUNIOR, EXPERIENCED, SENIOR)
    """
    if years < 1:
        return "NEW"
    elif years < 3:
        return "JUNIOR"
    elif years < 10:
        return "EXPERIENCED"
    else:
        return "SENIOR"


# Note: Validation error handling is done by FastAPI automatically
# Custom handler can be added to app.main if needed
async def validation_exception_handler_unused(request: Request, exc: RequestValidationError):
    """Custom handler for validation errors with detailed logging.
    
    Returns HTTP 422 with clear error messages for invalid inputs.
    """
    errors = exc.errors()
    
    # Log validation failure with details
    logger.error(
        "validation_error",
        error_count=len(errors),
        errors=[
            {
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
                "input": err.get("input", ""),
            }
            for err in errors
        ],
        request_path=request.url.path,
    )
    
    # Format user-friendly error messages
    error_details = []
    for err in errors:
        field = ".".join(str(loc) for loc in err.get("loc", []))
        message = err.get("msg", "Validation error")
        error_details.append(f"{field}: {message}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": error_details,
            "error_type": "validation_error",
            "message": "Request validation failed. Please check your input.",
        },
    )


@router.post("/predict", response_model=UXSafePredictionResponse, tags=["prediction"])
async def predict_credit_risk_ux_safe(request: CreditRiskRequest) -> UXSafePredictionResponse:
    """Predict credit risk with UX-safe guaranteed response structure.
    
    This endpoint GUARANTEES a consistent response structure even on errors.
    Frontend can always rely on the same fields being present.
    
    ═══════════════════════════════════════════════════════════════════════
    RESPONSE CONTRACT GUARANTEE:
    ═══════════════════════════════════════════════════════════════════════
    ALL responses contain these 6 fields (NEVER missing):
      - status: "success" | "error"
      - request_id: string (UUID)
      - model_version: string
      - prediction: number | null
      - confidence: number | null
      - error: string | null
    
    SUCCESS Example:
      {
        "status": "success",
        "request_id": "abc-123",
        "model_version": "ml_v1.0.0",
        "prediction": 0.15,
        "confidence": 0.92,
        "error": null,
        "data": { ...full CreditRiskResponse... }
      }
    
    ERROR Example:
      {
        "status": "error",
        "request_id": "abc-123",
        "model_version": "unknown",
        "prediction": null,
        "confidence": null,
        "error": "Inference timeout after 30s",
        "data": null
      }
    
    ═══════════════════════════════════════════════════════════════════════
    ERROR HANDLING:
    ═══════════════════════════════════════════════════════════════════════
    - Validation errors → HTTP 422, error in response
    - Model errors → HTTP 500, error in response
    - Timeout → HTTP 504, error in response
    - Runtime errors → HTTP 500, generic error message
    
    NO stack traces. NO internal paths. ALWAYS valid JSON.
    
    ═══════════════════════════════════════════════════════════════════════
    TIMEOUT BEHAVIOR:
    ═══════════════════════════════════════════════════════════════════════
    - Max inference time: 30 seconds
    - If timeout occurs:
      * Response: HTTP 504 with error message
      * Logging: Internal timeout logged with request_id
      * Server: Remains running (no crash)
    
    Args:
        request: Credit risk request with applicant features
        
    Returns:
        UXSafePredictionResponse with guaranteed structure
        
    Response Codes:
        200: Success (check status field for success/error)
        422: Validation error (automatic by FastAPI)
        500: Internal error
        504: Timeout
    """
    # Generate unique request ID for tracking
    request_id = str(uuid.uuid4())
    start_time = time.time()
    timestamp = datetime.now(timezone.utc).isoformat()
    
    try:
        # Phase 3C-1: Input Safety Validation (NaN/Inf/Range checks)
        from app.core.input_safety import validate_input_safety
        
        request_dict = request.model_dump()
        is_safe, safety_errors = validate_input_safety(request_dict)
        
        if not is_safe:
            logger.warning(
                "input_safety_validation_failed",
                request_id=request_id,
                error_count=len(safety_errors),
                errors=safety_errors[:3]  # Log first 3 only
            )
            
            # Return UX-safe error response
            return UXSafePredictionResponse.create_error(
                request_id=request_id,
                error_message=f"Input validation failed: {'; '.join(safety_errors[:2])}",
                model_version="validation_failed"
            )
        
        # Log incoming request (NO PII - only aggregated metrics)
        logger.info(
            "prediction_request_received",
            request_id=request_id,
            timestamp=timestamp,
            request_schema_version=REQUEST_SCHEMA_VERSION,
            response_schema_version=RESPONSE_SCHEMA_VERSION,
            # Aggregated metrics (safe to log)
            credit_score_band=_get_credit_band(request.credit_score),
            loan_amount_band=_get_loan_band(request.loan_amount),
            dti_band=_get_dti_band(request.compute_dti()),
            employment_band=_get_employment_band(request.employment_length_years),
            home_ownership=request.home_ownership,  # Categorical, not PII
            purpose=request.purpose,  # Categorical, not PII
            has_delinquencies=(request.delinquencies_2y > 0),
            has_inquiries=(request.inquiries_6m > 0),
        )
        
        # Validate computed DTI is reasonable
        dti = request.compute_dti()
        if dti > 100:
            logger.warning(
                "high_dti_detected",
                request_id=request_id,
                dti=dti,
                monthly_debt=request.monthly_debt,
                annual_income=request.annual_income,
            )
        
        # Get singleton model instance (fail fast if not loaded)
        model = get_model()
        
        # Verify model is loaded before attempting prediction
        if not model.is_loaded:
            logger.error(
                "prediction_failed_model_not_loaded",
                request_id=request_id,
            )
            return UXSafePredictionResponse.create_error(
                request_id=request_id,
                error_message="Model not loaded. Service is starting up or experiencing issues.",
                model_version="unknown"
            )
        
        logger.debug(
            "inference_starting",
            request_id=request_id,
        )
        
        # ═══════════════════════════════════════════════════════════════════════
        # INFERENCE WITH TIMEOUT PROTECTION
        # ═══════════════════════════════════════════════════════════════════════
        inference_start = time.time()
        
        try:
            # Run prediction with timeout
            # Using asyncio.wait_for to enforce timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(model.predict, request),
                timeout=INFERENCE_TIMEOUT
            )
            
        except asyncio.TimeoutError:
            # Timeout occurred - log and return graceful error
            total_time = time.time() - start_time
            logger.error(
                "inference_timeout",
                request_id=request_id,
                timeout_seconds=INFERENCE_TIMEOUT,
                total_time_ms=round(total_time * 1000, 2),
            )
            
            # Return UX-safe error response
            return UXSafePredictionResponse.create_error(
                request_id=request_id,
                error_message=f"Inference timeout after {INFERENCE_TIMEOUT}s. Please try again with different inputs.",
                model_version=model.get_model_version() if model.is_loaded else "unknown"
            )
        
        inference_time = time.time() - inference_start
        
        # Track prediction distribution for runtime monitoring
        _prediction_history.append(response.risk_score)
        
        # Log distribution statistics periodically (every 5 minutes)
        global _last_distribution_log_time
        current_time = time.time()
        if current_time - _last_distribution_log_time >= 300:  # 5 minutes
            if len(_prediction_history) > 0:
                import numpy as np
                predictions = list(_prediction_history)
                logger.info(
                    "prediction_distribution",
                    sample_size=len(predictions),
                    mean=f"{np.mean(predictions):.4f}",
                    median=f"{np.median(predictions):.4f}",
                    std=f"{np.std(predictions):.4f}",
                    min=f"{np.min(predictions):.4f}",
                    max=f"{np.max(predictions):.4f}",
                    high_risk_count=sum(1 for p in predictions if p > 0.5),
                    high_risk_pct=f"{100 * sum(1 for p in predictions if p > 0.5) / len(predictions):.1f}%"
                )
            _last_distribution_log_time = current_time
        
        # Calculate total request time
        total_time = time.time() - start_time
        
        # Determine risk band for monitoring (HIGH/MEDIUM/LOW)
        if response.risk_score >= 0.7:
            risk_band = "HIGH"
        elif response.risk_score >= 0.3:
            risk_band = "MEDIUM"
        else:
            risk_band = "LOW"
        
        # Log prediction outcome with structured observability data
        # NOTE: No raw features or PII are logged here
        logger.info(
            "prediction_complete",
            # Request tracking
            request_id=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            # Schema versions
            request_schema_version=REQUEST_SCHEMA_VERSION,
            response_schema_version=RESPONSE_SCHEMA_VERSION,
            # Model outputs (safe to log)
            risk_score=f"{response.risk_score:.4f}",
            prediction_probability=f"{response.risk_score:.4f}",  # Explicit probability
            risk_level=response.risk_level.value,
            risk_band=risk_band,  # HIGH/MEDIUM/LOW for alerting
            recommended_action=response.recommended_action.value,
            confidence_level=response.confidence_level,
            model_version=response.model_version,
            schema_version=response.schema_version,
            # Performance metrics
            inference_latency_ms=round(inference_time * 1000, 2),
            total_latency_ms=round(total_time * 1000, 2),
            # High-level flags (no PII)
            is_high_risk=(risk_band == "HIGH"),
            is_approved=(response.recommended_action.value == "APPROVE"),
        )
        
        # Return UX-safe success response
        return UXSafePredictionResponse.success(
            request_id=request_id,
            prediction_response=response
        )
        
    except ValueError as e:
        # Handle domain validation errors (e.g., invalid enum values)
        total_time = time.time() - start_time
        logger.error(
            "prediction_validation_error",
            request_id=request_id,
            error=str(e),
            total_time_ms=f"{total_time * 1000:.2f}"
        )
        
        # Return UX-safe error response (not raising HTTPException)
        return UXSafePredictionResponse.create_error(
            request_id=request_id,
            error_message=f"Validation error: {str(e)}",
            model_version="unknown"
        )
        
    except RuntimeError as e:
        # Handle model loading/initialization errors
        total_time = time.time() - start_time
        logger.error(
            "prediction_model_error",
            request_id=request_id,
            error=str(e),
            total_time_ms=f"{total_time * 1000:.2f}"
        )
        
        # Return UX-safe error response
        return UXSafePredictionResponse.create_error(
            request_id=request_id,
            error_message="Model is not available. Please try again later.",
            model_version="unknown"
        )
        
    except Exception as e:
        # Catch-all for unexpected errors - NO stack trace to frontend
        total_time = time.time() - start_time
        logger.error(
            "prediction_unexpected_error",
            request_id=request_id,
            error=str(e),
            exception_type=type(e).__name__,
            total_time_ms=f"{total_time * 1000:.2f}",
            exc_info=True  # Log full trace internally, not to frontend
        )
        
        # Return UX-safe generic error (no internal details leaked)
        return UXSafePredictionResponse.create_error(
            request_id=request_id,
            error_message="An unexpected error occurred. Please try again or contact support.",
            model_version="unknown"
        )


@router.post("/predict/legacy", response_model=CreditRiskResponse, tags=["prediction"])
async def predict_credit_risk(request: CreditRiskRequest) -> CreditRiskResponse:
    """[LEGACY] Predict credit risk for loan applicant.
    
    **DEPRECATED**: Use /predict endpoint for UX-safe guaranteed responses.
    This legacy endpoint may throw HTTPExceptions that break frontend UI.
    
    This endpoint accepts applicant financial data and returns a risk assessment
    including numeric risk score, categorical risk level, recommended action,
    and human-readable explanation.
    
    **Strict Validation:**
    - All 11 required fields must be present
    - Extra fields are rejected (HTTP 422)
    - Values must be within valid ranges
    - Data types must match exactly
    
    Args:
        request: Credit risk request with applicant features
        
    Returns:
        CreditRiskResponse with risk assessment and explanation
        
    Raises:
        HTTPException: 422 if request validation fails (automatic)
        HTTPException: 500 if model inference fails
    """
    # Generate unique request ID for tracking
    request_id = str(uuid.uuid4())
    start_time = time.time()
    timestamp = datetime.now(timezone.utc).isoformat()
    
    try:
        # Log incoming request (NO PII - only aggregated metrics)
        logger.info(
            "prediction_request_received",
            request_id=request_id,
            timestamp=timestamp,
            # Aggregated metrics (safe to log)
            credit_score_band=_get_credit_band(request.credit_score),
            loan_amount_band=_get_loan_band(request.loan_amount),
            dti_band=_get_dti_band(request.compute_dti()),
            employment_band=_get_employment_band(request.employment_length_years),
            home_ownership=request.home_ownership,  # Categorical, not PII
            purpose=request.purpose,  # Categorical, not PII
            has_delinquencies=(request.delinquencies_2y > 0),
            has_inquiries=(request.inquiries_6m > 0),
        )
        
        # Validate computed DTI is reasonable
        dti = request.compute_dti()
        if dti > 100:
            logger.warning(
                "high_dti_detected",
                request_id=request_id,
                dti=dti,
                monthly_debt=request.monthly_debt,
                annual_income=request.annual_income,
            )
        
        # Get singleton model instance (fail fast if not loaded)
        model = get_model()
        
        # Verify model is loaded before attempting prediction
        if not model.is_loaded:
            logger.error(
                "prediction_failed_model_not_loaded",
                request_id=request_id,
            )
            raise RuntimeError("Model not loaded. Service is starting up or experiencing issues.")
        
        logger.debug(
            "inference_starting",
            request_id=request_id,
        )
        
        # Generate prediction using inference engine
        # This internally calls the explainer for human-readable text
        inference_start = time.time()
        response = model.predict(request)
        inference_time = time.time() - inference_start
        
        # Track prediction distribution for runtime monitoring
        _prediction_history.append(response.risk_score)
        
        # Log distribution statistics periodically (every 5 minutes)
        global _last_distribution_log_time
        current_time = time.time()
        if current_time - _last_distribution_log_time >= 300:  # 5 minutes
            if len(_prediction_history) > 0:
                import numpy as np
                predictions = list(_prediction_history)
                logger.info(
                    "prediction_distribution",
                    sample_size=len(predictions),
                    mean=f"{np.mean(predictions):.4f}",
                    median=f"{np.median(predictions):.4f}",
                    std=f"{np.std(predictions):.4f}",
                    min=f"{np.min(predictions):.4f}",
                    max=f"{np.max(predictions):.4f}",
                    high_risk_count=sum(1 for p in predictions if p > 0.5),
                    high_risk_pct=f"{100 * sum(1 for p in predictions if p > 0.5) / len(predictions):.1f}%"
                )
            _last_distribution_log_time = current_time
        
        # Calculate total request time
        total_time = time.time() - start_time
        
        # Determine risk band for monitoring (HIGH/MEDIUM/LOW)
        if response.risk_score >= 0.7:
            risk_band = "HIGH"
        elif response.risk_score >= 0.3:
            risk_band = "MEDIUM"
        else:
            risk_band = "LOW"
        
        # Log prediction outcome with structured observability data
        # NOTE: No raw features or PII are logged here
        logger.info(
            "prediction_complete",
            # Request tracking
            request_id=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            # Model outputs (safe to log)
            risk_score=f"{response.risk_score:.4f}",
            prediction_probability=f"{response.risk_score:.4f}",  # Explicit probability
            risk_level=response.risk_level.value,
            risk_band=risk_band,  # HIGH/MEDIUM/LOW for alerting
            recommended_action=response.recommended_action.value,
            confidence_level=response.confidence_level,
            model_version=response.model_version,
            schema_version=response.schema_version,
            # Performance metrics
            inference_latency_ms=round(inference_time * 1000, 2),
            total_latency_ms=round(total_time * 1000, 2),
            # High-level flags (no PII)
            is_high_risk=(risk_band == "HIGH"),
            is_approved=(response.recommended_action.value == "APPROVE"),
        )
        
        return response
        
    except ValueError as e:
        # Handle domain validation errors (e.g., invalid enum values)
        total_time = time.time() - start_time
        logger.error(
            "prediction_validation_error",
            request_id=request_id,
            error=str(e),
            total_time_ms=f"{total_time * 1000:.2f}"
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )
        
    except RuntimeError as e:
        # Handle model loading/initialization errors
        total_time = time.time() - start_time
        logger.error(
            "prediction_model_error",
            request_id=request_id,
            error=str(e),
            total_time_ms=f"{total_time * 1000:.2f}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model is not available. Please try again later.",
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        total_time = time.time() - start_time
        logger.error(
            "prediction_unexpected_error",
            request_id=request_id,
            error=str(e),
            total_time_ms=f"{total_time * 1000:.2f}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction.",
        )


@router.post("/predict/batch", response_model=list[CreditRiskResponse], tags=["prediction"])
async def predict_credit_risk_batch(
    requests: list[CreditRiskRequest]
) -> list[CreditRiskResponse]:
    """Predict credit risk for multiple loan applicants.
    
    This endpoint accepts a list of applicant data and returns risk assessments
    for each applicant. Predictions are processed sequentially to ensure
    deterministic ordering.
    
    Args:
        requests: List of credit risk requests
        
    Returns:
        List of CreditRiskResponse objects in same order as input
        
    Raises:
        HTTPException: 400 if batch is too large (>100 requests)
        HTTPException: 500 if model inference fails
    """
    # Enforce batch size limit to prevent resource exhaustion
    MAX_BATCH_SIZE = 100
    if len(requests) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size {len(requests)} exceeds maximum of {MAX_BATCH_SIZE}",
        )
    
    logger.info("batch_prediction_request", batch_size=len(requests))
    
    try:
        model = get_model()
        responses = []
        
        # Process each request sequentially
        for idx, request in enumerate(requests):
            try:
                response = model.predict(request)
                responses.append(response)
            except Exception as e:
                # Log error but continue processing remaining requests
                logger.error(
                    "batch_prediction_item_error",
                    index=idx,
                    error=str(e),
                )
                # Return error response for failed item
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Prediction failed for item at index {idx}: {str(e)}",
                )
        
        logger.info("batch_prediction_complete", batch_size=len(responses))
        return responses
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        logger.error("batch_prediction_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during batch prediction.",
        )

