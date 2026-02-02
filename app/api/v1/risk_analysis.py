"""Risk Analysis endpoint - Frontend-compatible adapter.

═══════════════════════════════════════════════════════════════════════
FRONTEND API CONTRACT (FROZEN - Phase 3A-1)
═══════════════════════════════════════════════════════════════════════

This endpoint implements a frozen API contract with the frontend.
Discovered via Frontend → Backend Contract Discovery (Phase 3A-1).

CONTRACT DETAILS:
- Source: types.ts (Frontend TypeScript definitions)
- Discovered: February 1, 2026
- Status: FROZEN (coordinate with frontend for any changes)
- Documentation: PHASE_3A1_CONTRACT_DISCOVERY.md

INPUT CONTRACT: FinancialProfile (5 fields)
  - annualIncome: number (user's annual income in USD)
  - monthlyDebt: number (total monthly debt payments in USD)
  - creditScore: number (FICO credit score, 300-850)
  - loanAmount: number (requested loan amount in USD)
  - employmentYears: number (years at current employment)

OUTPUT CONTRACT: RiskAnalysis (5 fields)
  - score: number (0-1000, higher = less risky)
  - riskLevel: 'Low' | 'Medium' | 'High' | 'Critical'
  - summary: string (professional risk assessment)
  - factors: string[] (key risk factors identified)
  - recommendation: string (actionable recommendation)

CONSTRAINTS:
- Response time: Must be < 10 seconds (frontend timeout)
- CORS: Must allow localhost:5173 (Vite dev server)
- Headers: Content-Type: application/json
- Base URL: /api/v1/risk-analysis

⚠️ BREAKING CHANGE WARNING:
DO NOT modify field names, types, or structure without frontend coordination.
This contract matches TypeScript types exactly (camelCase naming).

═══════════════════════════════════════════════════════════════════════

IMPLEMENTATION NOTES:
- Frontend provides 5 fields, backend ML model requires 11 fields
- This adapter fills missing 6 fields with sensible defaults
- Transforms ML probability output → frontend risk analysis format
- Internal mapping: probability_of_default → score, risk_tier → riskLevel
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import structlog
from typing import Literal, List

from app.schemas.request import CreditRiskRequest
from app.ml.model import get_model

router = APIRouter()
logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# FRONTEND-COMPATIBLE REQUEST/RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class FinancialProfile(BaseModel):
    """Frontend's simplified financial profile (5 fields).
    
    ═══════════════════════════════════════════════════════════════════════
    FROZEN FRONTEND CONTRACT (Phase 3A-1)
    ═══════════════════════════════════════════════════════════════════════
    
    This schema EXACTLY matches the TypeScript interface from types.ts:
    ```typescript
    export interface FinancialProfile {
      annualIncome: number;
      monthlyDebt: number;
      creditScore: number;
      loanAmount: number;
      employmentYears: number;
    }
    ```
    
    CONTRACT REQUIREMENTS:
    - Field names: MUST use camelCase (TypeScript convention)
    - Field types: MUST be JSON-serializable (number → float/int)
    - Field order: Not critical (JSON objects are unordered)
    - Required: ALL 5 fields are required (no optionals)
    - Validation: Ranges validated by Pydantic
    
    ⚠️ DO NOT MODIFY WITHOUT FRONTEND COORDINATION
    Any changes to field names, types, or required status will break frontend.
    
    Discovery Source: PHASE_3A1_CONTRACT_DISCOVERY.md
    ═══════════════════════════════════════════════════════════════════════
    """
    annualIncome: float = Field(
        ...,
        description="Applicant's annual income in USD",
        ge=1,  # Must have some income
        le=10_000_000,
        examples=[85000]
    )
    monthlyDebt: float = Field(
        ...,
        description="Total monthly debt payments in USD",
        ge=0,
        le=100_000,
        examples=[1200]
    )
    creditScore: int = Field(
        ...,
        description="FICO credit score (300-850)",
        ge=300,
        le=850,
        examples=[720]
    )
    loanAmount: float = Field(
        ...,
        description="Requested loan amount in USD",
        ge=1000,
        le=1_000_000,
        examples=[25000]
    )
    employmentYears: float = Field(
        ...,
        description="Years at current employment",
        ge=0,
        le=50,
        examples=[5]
    )


class RiskAnalysis(BaseModel):
    """Frontend's expected risk analysis response (5 fields).
    
    ═══════════════════════════════════════════════════════════════════════
    FROZEN FRONTEND CONTRACT (Phase 3A-1)
    ═══════════════════════════════════════════════════════════════════════
    
    This schema EXACTLY matches the TypeScript interface from types.ts:
    ```typescript
    export interface RiskAnalysis {
      score: number;
      riskLevel: 'Low' | 'Medium' | 'High' | 'Critical';
      summary: string;
      factors: string[];
      recommendation: string;
    }
    ```
    
    CONTRACT REQUIREMENTS:
    - Field names: MUST use camelCase (TypeScript convention)
    - score: 0-1000 integer (higher = less risky)
    - riskLevel: EXACTLY one of: 'Low', 'Medium', 'High', 'Critical'
    - summary: Human-readable professional assessment (2-3 sentences)
    - factors: Array of key risk factor strings (3-5 items typical)
    - recommendation: Actionable advice for loan officer
    
    ⚠️ DO NOT MODIFY WITHOUT FRONTEND COORDINATION
    Any changes to field names, types, or enum values will break frontend.
    
    Discovery Source: PHASE_3A1_CONTRACT_DISCOVERY.md
    ═══════════════════════════════════════════════════════════════════════
    """
    score: int = Field(
        ...,
        description="Proprietary risk score (0-1000, higher is better)",
        ge=0,
        le=1000,
        examples=[785]
    )
    riskLevel: Literal['Low', 'Medium', 'High', 'Critical'] = Field(
        ...,
        description="Risk tier classification",
        examples=["Low"]
    )
    summary: str = Field(
        ...,
        description="Professional summary of risk profile",
        examples=["Based on the provided financial profile, the applicant demonstrates strong repayment capacity."]
    )
    factors: List[str] = Field(
        ...,
        description="Key factors affecting risk assessment",
        examples=[["High credit score (700+)", "Low debt-to-income ratio", "Stable employment history"]]
    )
    recommendation: str = Field(
        ...,
        description="Recommendation for loan officer",
        examples=["Approve loan with competitive interest rate."]
    )


# ═══════════════════════════════════════════════════════════════════════
# TRANSFORMATION LOGIC
# ═══════════════════════════════════════════════════════════════════════

def transform_frontend_to_backend(profile: FinancialProfile) -> CreditRiskRequest:
    """Transform frontend's 5-field input to backend's 11-field requirement.
    
    Missing fields are filled with sensible defaults based on common use cases.
    
    Args:
        profile: Frontend FinancialProfile (5 fields)
        
    Returns:
        CreditRiskRequest with all 11 required fields
    """
    return CreditRiskRequest(
        schema_version="v1",
        # Direct mappings (5 fields from frontend):
        annual_income=profile.annualIncome,
        monthly_debt=profile.monthlyDebt,
        credit_score=profile.creditScore,
        loan_amount=profile.loanAmount,
        employment_length_years=profile.employmentYears,
        
        # Sensible defaults for missing fields (6 additional):
        loan_term_months=60,  # 5-year loan (most common)
        home_ownership="MORTGAGE",  # Most common for established applicants
        purpose="debt_consolidation",  # Most common loan purpose
        number_of_open_accounts=8,  # Average number of accounts
        delinquencies_2y=0,  # Assume clean record (optimistic default)
        inquiries_6m=1,  # Minimal recent inquiries
    )


def transform_backend_to_frontend(backend_response: dict) -> RiskAnalysis:
    """Transform backend's comprehensive response to frontend's simple format.
    
    Args:
        backend_response: UXSafePredictionResponse with full ML output
        
    Returns:
        RiskAnalysis in frontend-compatible format
    """
    # Extract prediction and data
    prediction = backend_response.get("prediction")
    data = backend_response.get("data", {})
    
    # Transform probability (0-1) to score (0-1000)
    # Lower probability → higher score (inverted for UX)
    score = int((1 - prediction) * 1000) if prediction is not None else 500
    
    # Map risk tier to risk level
    risk_tier = data.get("risk_tier", "TIER_3")
    risk_level_map = {
        "TIER_1": "Low",      # Lowest risk
        "TIER_2": "Low",
        "TIER_3": "Medium",   # Moderate risk
        "TIER_4": "High",
        "TIER_5": "Critical"  # Highest risk
    }
    risk_level = risk_level_map.get(risk_tier, "Medium")
    
    # Generate summary based on risk level
    dti = data.get("debt_to_income_ratio", 0.0)
    credit_score = data.get("credit_score", 700)
    
    if risk_level == "Low":
        summary = (
            "Based on the provided financial profile, the applicant demonstrates strong repayment capacity. "
            "The debt-to-income ratio is healthy, and the credit score indicates a history of responsible credit usage."
        )
    elif risk_level == "Medium":
        summary = (
            "The applicant shows moderate credit risk with acceptable financial indicators. "
            "Debt-to-income ratio is within acceptable range, though some areas could be improved."
        )
    elif risk_level == "High":
        summary = (
            "The applicant presents elevated credit risk with several concerning factors. "
            "High debt-to-income ratio and/or lower credit score suggest potential repayment challenges."
        )
    else:  # Critical
        summary = (
            "The applicant demonstrates significant credit risk with multiple red flags. "
            "Financial profile suggests high probability of default without substantial improvements."
        )
    
    # Extract key factors from backend
    backend_factors = data.get("key_factors", [])
    
    # Generate user-friendly factors
    factors = []
    if credit_score >= 750:
        factors.append("Excellent credit score (750+)")
    elif credit_score >= 700:
        factors.append("Good credit score (700+)")
    elif credit_score >= 650:
        factors.append("Fair credit score (650+)")
    else:
        factors.append("Below average credit score")
    
    if dti < 0.2:
        factors.append("Very low debt-to-income ratio")
    elif dti < 0.35:
        factors.append("Healthy debt-to-income ratio")
    elif dti < 0.5:
        factors.append("Elevated debt-to-income ratio")
    else:
        factors.append("High debt-to-income ratio")
    
    employment_years = data.get("employment_length_years", 5)
    if employment_years >= 10:
        factors.append("Strong employment stability (10+ years)")
    elif employment_years >= 3:
        factors.append("Stable employment history")
    else:
        factors.append("Limited employment history")
    
    # Add backend factors if available
    if isinstance(backend_factors, list) and len(backend_factors) > 0:
        for factor in backend_factors[:3]:  # Top 3 from ML model
            if isinstance(factor, dict):
                feature = factor.get("feature", "")
                if feature and feature not in str(factors):
                    factors.append(f"{feature.replace('_', ' ').title()} consideration")
    
    # Generate recommendation
    if risk_level == "Low":
        recommendation = "Approve loan with competitive interest rate. Strong candidate for favorable terms."
    elif risk_level == "Medium":
        recommendation = "Approve with standard terms. Monitor closely and consider standard interest rate."
    elif risk_level == "High":
        recommendation = "Exercise caution. Consider approval with higher interest rate or require additional collateral."
    else:  # Critical
        recommendation = "Recommend decline or require substantial additional guarantees before approval."
    
    return RiskAnalysis(
        score=score,
        riskLevel=risk_level,
        summary=summary,
        factors=factors,
        recommendation=recommendation
    )


# ═══════════════════════════════════════════════════════════════════════
# ADAPTER ENDPOINT
# ═══════════════════════════════════════════════════════════════════════

@router.post("/risk-analysis", response_model=RiskAnalysis, tags=["frontend-adapter"])
async def analyze_risk(profile: FinancialProfile) -> RiskAnalysis:
    """Frontend-compatible risk analysis endpoint.
    
    This adapter endpoint bridges frontend and backend:
    - Accepts frontend's simple 5-field FinancialProfile
    - Fills missing 6 fields with sensible defaults
    - Calls internal /predict endpoint
    - Transforms ML output to frontend-compatible format
    - Returns RiskAnalysis in exact format frontend expects
    
    ═══════════════════════════════════════════════════════════════════════
    FRONTEND INTEGRATION:
    ═══════════════════════════════════════════════════════════════════════
    Update `lib/api.ts`:
    ```typescript
    getRiskScore: async (input: FinancialProfile) => {
      return apiClient.post('/risk-analysis', input);
    }
    ```
    
    ═══════════════════════════════════════════════════════════════════════
    RESPONSE CONTRACT:
    ═══════════════════════════════════════════════════════════════════════
    ```json
    {
      "score": 785,
      "riskLevel": "Low",
      "summary": "Based on the provided financial profile...",
      "factors": ["High credit score (700+)", "Low debt-to-income ratio", ...],
      "recommendation": "Approve loan with competitive interest rate."
    }
    ```
    
    Args:
        profile: Frontend's FinancialProfile (5 fields)
        
    Returns:
        RiskAnalysis in frontend-compatible format
        
    Response Codes:
        200: Success with risk analysis
        422: Validation error (invalid inputs)
        500: Internal error
    """
    # Get model info for logging
    model_manager = get_model()
    model_version = model_manager.model_version if hasattr(model_manager, 'model_version') else 'unknown'
    
    # Log request (NO PII - use safe ranges only)
    def _get_income_band(income: float) -> str:
        """Convert income to privacy-safe band."""
        if income < 30000: return "LOW"
        elif income < 60000: return "MODERATE"
        elif income < 100000: return "HIGH"
        else: return "VERY_HIGH"
    
    def _get_credit_band(score: int) -> str:
        """Convert credit score to privacy-safe band."""
        if score >= 750: return "EXCELLENT"
        elif score >= 700: return "GOOD"
        elif score >= 650: return "FAIR"
        else: return "POOR"
    
    def _get_loan_band(amount: float) -> str:
        """Convert loan amount to privacy-safe band."""
        if amount < 10000: return "SMALL"
        elif amount < 25000: return "MEDIUM"
        elif amount < 50000: return "LARGE"
        else: return "VERY_LARGE"
    
    logger.info(
        "risk_analysis_request",
        income_band=_get_income_band(profile.annualIncome),
        credit_band=_get_credit_band(profile.creditScore),
        loan_band=_get_loan_band(profile.loanAmount),
        model_version=model_version
    )
    
    try:
        # Step 1: Transform frontend input to backend format
        backend_request = transform_frontend_to_backend(profile)
        
        logger.debug(
            "transformed_to_backend_format",
            backend_fields=11,
            frontend_fields=5,
            filled_defaults=6
        )
        
        # Step 2: Run prediction using ML model
        # (model_manager already retrieved above for logging)
        
        # Run prediction (model expects CreditRiskRequest object)
        result = model_manager.predict(backend_request)
        
        # Convert CreditRiskResponse to dict
        result_dict = result.model_dump()
        
        # Build response dict similar to UXSafePredictionResponse
        backend_response_dict = {
            "status": "success",
            "prediction": result_dict.get("probability_of_default"),
            "data": result_dict
        }
        
        # Step 3: Transform backend response to frontend format
        frontend_response = transform_backend_to_frontend(backend_response_dict)
        
        logger.info(
            "risk_analysis_success",
            score=frontend_response.score,
            risk_level=frontend_response.riskLevel
        )
        
        return frontend_response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        logger.error(
            "risk_analysis_unexpected_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during risk analysis."
        )
