"""Prediction endpoint for credit risk assessment."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
import structlog

from app.schemas.request import CreditRiskRequest
from app.schemas.response import CreditRiskResponse
from app.ml.model import get_model

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/predict", response_model=CreditRiskResponse, tags=["prediction"])
async def predict_credit_risk(request: CreditRiskRequest) -> CreditRiskResponse:
    """Predict credit risk for loan applicant.
    
    This endpoint accepts applicant financial data and returns a risk assessment
    including numeric risk score, categorical risk level, recommended action,
    and human-readable explanation.
    
    Args:
        request: Credit risk request with applicant features
        
    Returns:
        CreditRiskResponse with risk assessment and explanation
        
    Raises:
        HTTPException: 500 if model inference fails
        HTTPException: 422 if request validation fails (automatic)
    """
    try:
        # Log incoming request (excluding sensitive data)
        logger.info(
            "prediction_request",
            credit_score=request.credit_score,
            loan_amount=request.loan_amount,
            loan_term=request.loan_term_months,
        )
        
        # Get singleton model instance
        model = get_model()
        
        # Generate prediction using inference engine
        # This internally calls the explainer for human-readable text
        response = model.predict(request)
        
        # Log prediction outcome
        logger.info(
            "prediction_complete",
            risk_score=response.risk_score,
            risk_level=response.risk_level.value,
            recommended_action=response.recommended_action,
        )
        
        return response
        
    except ValueError as e:
        # Handle domain validation errors (e.g., invalid enum values)
        logger.error("prediction_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )
        
    except RuntimeError as e:
        # Handle model loading/initialization errors
        logger.error("prediction_model_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model is not available. Please try again later.",
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error("prediction_unexpected_error", error=str(e), exc_info=True)
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


@router.get("/model/info", tags=["prediction"])
async def get_model_info():
    """Get information about the current prediction model.
    
    Returns model metadata including type, version, and supported features.
    Useful for monitoring and debugging.
    
    Returns:
        Dictionary with model information
    """
    try:
        model = get_model()
        info = model.get_model_info()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "model": info,
            }
        )
        
    except Exception as e:
        logger.error("model_info_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model information.",
        )
