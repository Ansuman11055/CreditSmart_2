"""Financial advisor endpoint."""

from fastapi import APIRouter, HTTPException, status
import structlog

from app.schemas.request import CreditRiskRequest
from app.schemas.advisor import AdvisorResponse
from app.services.advisor import get_advisor
from app.ml.model import get_model

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/advisor", response_model=AdvisorResponse, tags=["advisor"])
async def get_financial_advice(request: CreditRiskRequest) -> AdvisorResponse:
    """Generate personalized financial improvement recommendations.
    
    This endpoint analyzes the applicant's financial profile and provides
    actionable advice for improving creditworthiness. Recommendations are
    prioritized by impact and include expected timeframes.
    
    The advice is currently generated using deterministic rule-based logic.
    Future versions will integrate LLM-powered personalization.
    
    Args:
        request: Credit risk request with applicant features
        
    Returns:
        AdvisorResponse with prioritized recommendations and improvement plan
        
    Raises:
        HTTPException: 500 if advice generation fails
        HTTPException: 422 if request validation fails (automatic)
    """
    try:
        # Log request
        logger.info(
            "advisor_request",
            credit_score=request.credit_score,
            dti=request.compute_dti(),
        )
        
        # First, get current risk assessment
        model = get_model()
        risk_response = model.predict(request)
        
        # Generate personalized financial advice
        advisor = get_advisor()
        advice_response = advisor.generate_advice(
            request=request,
            current_risk_score=risk_response.risk_score,
        )
        
        # Log outcome
        logger.info(
            "advisor_complete",
            current_score=advice_response.current_risk_score,
            potential_score=advice_response.potential_risk_score,
            recommendation_count=len(advice_response.recommendations),
        )
        
        return advice_response
        
    except ValueError as e:
        # Handle domain validation errors
        logger.error("advisor_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )
        
    except RuntimeError as e:
        # Handle service errors
        logger.error("advisor_service_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Advisor service is not available. Please try again later.",
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error("advisor_unexpected_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating advice.",
        )
