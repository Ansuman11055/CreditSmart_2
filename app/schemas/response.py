"""Response schemas for credit risk prediction API.

PRODUCTION CONTRACT - FROZEN AS OF 2026-01-31
This schema is a versioned API contract. Breaking changes require a new schema version.

VALIDATION ROBUSTNESS:
- All float fields protected against NaN/Inf values
- Enum fields validated against strict allowed values
- Risk scores bounded to [0.0, 1.0]
- No silent coercion or frontend assumptions
"""

import math
from enum import Enum
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class RiskLevel(str, Enum):
    """Credit risk level classification.
    
    These levels represent the assessed risk of loan default:
    - LOW: Minimal risk, excellent credit profile (risk_score < 0.25)
    - MEDIUM: Moderate risk, acceptable credit profile (risk_score 0.25-0.50)
    - HIGH: Elevated risk, requires additional scrutiny (risk_score 0.50-0.75)
    - VERY_HIGH: Severe risk, high probability of default (risk_score >= 0.75)
    
    Business Interpretation:
    - LOW → Automatic approval recommended
    - MEDIUM → Manual review recommended
    - HIGH/VERY_HIGH → Rejection recommended
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class RecommendedAction(str, Enum):
    """Recommended action for loan application.
    
    Decision guidance based on risk assessment:
    - APPROVE: Low risk, proceed with loan approval
    - REVIEW: Moderate risk, requires human review
    - REJECT: High risk, decline loan application
    """
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


class CreditRiskResponse(BaseModel):
    """Production-grade response schema for credit risk prediction (Schema Version: v1).
    
    This schema represents a frozen API contract for credit risk assessment responses.
    All fields are explicitly defined with strict type validation.
    
    ═══════════════════════════════════════════════════════════════════════
    PRODUCTION CONTRACT GUARANTEES:
    ═══════════════════════════════════════════════════════════════════════
    - Extra fields are FORBIDDEN (strict contract enforcement)
    - All required fields always present
    - Numeric precision fixed for frontend safety
    - Enums validated against allowed values
    - Schema version field ensures forward compatibility
    
    ═══════════════════════════════════════════════════════════════════════
    FIELD DEFINITIONS (9 fields: 7 required + 2 optional):
    ═══════════════════════════════════════════════════════════════════════
    REQUIRED (7 fields):
      1. schema_version         - API version identifier (v1)
      2. risk_score             - Probability of default [0.0-1.0]
      3. risk_level             - Categorical risk (LOW/MEDIUM/HIGH/VERY_HIGH)
      4. recommended_action     - Decision guidance (APPROVE/REVIEW/REJECT)
      5. model_version          - Model identifier for traceability
      6. prediction_probability - Raw model probability (alias for risk_score)
      7. confidence_level       - Model confidence description
    
    OPTIONAL (2 fields):
      8. explanation           - Human-readable risk explanation
      9. key_factors           - Contributing factors (for interpretability)
    
    ═══════════════════════════════════════════════════════════════════════
    FRONTEND CONSUMPTION GUIDE:
    ═══════════════════════════════════════════════════════════════════════
    - Use risk_level for visual indicators (badges, colors)
    - Use recommended_action for decision buttons
    - Display risk_score as percentage: (risk_score * 100).toFixed(1) + "%"
    - Show explanation to users for transparency
    - Use model_version for audit trails
    - confidence_level provides user-friendly confidence indicator
    
    ═══════════════════════════════════════════════════════════════════════
    SCHEMA VERSIONING:
    ═══════════════════════════════════════════════════════════════════════
    Current Version: v1 (frozen 2026-01-31)
    - Breaking changes require new version (v2, v3, etc.)
    - Backward compatibility maintained within version
    - Frontend can check schema_version for compatibility
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # SCHEMA VERSION (REQUIRED FOR API CONTRACT)
    # ═══════════════════════════════════════════════════════════════════════
    
    schema_version: Literal["v1"] = Field(
        default="v1",
        description="API schema version. Current: v1 (2026-01-31). Used for compatibility checks.",
        examples=["v1"]
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # PYDANTIC CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════
    
    model_config = ConfigDict(
        extra='forbid',  # Reject extra fields (strict contract enforcement)
        validate_assignment=True,  # Validate on field assignment
        frozen=False,  # Allow internal mutations if needed
        json_schema_extra={
            "example": {
                "schema_version": "v1",
                "risk_score": 0.15,
                "risk_level": "LOW",
                "recommended_action": "APPROVE",
                "model_version": "ml_v1.0.0",
                "prediction_probability": 0.15,
                "confidence_level": "HIGH",
                "explanation": "Strong credit profile with stable income and no recent delinquencies.",
                "key_factors": {
                    "credit_score": {"value": 780, "impact": "positive"},
                    "employment_length": {"value": 8, "impact": "positive"},
                    "debt_to_income": {"value": 18.5, "impact": "positive"}
                }
            }
        }
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # RISK ASSESSMENT FIELDS (REQUIRED)
    # ═══════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════
    # RISK ASSESSMENT FIELDS (REQUIRED)
    # ═══════════════════════════════════════════════════════════════════════

    risk_score: float = Field(
        ...,  # Required
        ge=0.0,
        le=1.0,
        description=(
            "REQUIRED. Probability of loan default as decimal [0.0, 1.0]. "
            "Business logic: 0.0 = no risk (certain repayment), 1.0 = certain default. "
            "Frontend display: Multiply by 100 for percentage (e.g., 0.15 → 15%). "
            "Precision: Rounded to 4 decimal places for consistency. "
            "Range: [0.0, 1.0]"
        ),
        examples=[0.05, 0.25, 0.65, 0.90]
    )

    risk_level: RiskLevel = Field(
        ...,  # Required
        description=(
            "REQUIRED. Categorical risk classification derived from risk_score. "
            "Business logic: "
            "  LOW (< 0.25): Excellent credit, automatic approval "
            "  MEDIUM (0.25-0.50): Acceptable credit, manual review "
            "  HIGH (0.50-0.75): Elevated risk, rejection recommended "
            "  VERY_HIGH (≥ 0.75): Severe risk, automatic rejection "
            "Frontend display: Use for color-coded badges (green/yellow/orange/red). "
            "Validation: Must match RiskLevel enum."
        ),
        examples=["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
    )

    recommended_action: RecommendedAction = Field(
        ...,  # Required
        description=(
            "REQUIRED. Recommended decision for loan application. "
            "Business logic: "
            "  APPROVE: Low risk, proceed with loan "
            "  REVIEW: Moderate risk, requires human assessment "
            "  REJECT: High risk, decline application "
            "Frontend display: Use for action buttons and decision guidance. "
            "Validation: Must match RecommendedAction enum."
        ),
        examples=["APPROVE", "REVIEW", "REJECT"]
    )

    model_version: str = Field(
        ...,  # Required
        description=(
            "REQUIRED. ML model version identifier for traceability and auditing. "
            "Business logic: Format 'ml_v{major}.{minor}.{patch}' (e.g., 'ml_v1.0.0'). "
            "Used for: Model rollbacks, A/B testing, audit trails, debugging. "
            "Frontend display: Show in footer or metadata for transparency. "
            "Should never be null for production predictions."
        ),
        examples=["ml_v1.0.0", "ml_v1.2.3", "xgboost_v2.1.0"]
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # CONFIDENCE & PROBABILITY FIELDS (REQUIRED)
    # ═══════════════════════════════════════════════════════════════════════

    prediction_probability: float = Field(
        ...,  # Required
        ge=0.0,
        le=1.0,
        description=(
            "REQUIRED. Raw model probability output (same as risk_score for backward compatibility). "
            "Business logic: Direct ML model output before any thresholding. "
            "Technical note: Alias for risk_score to maintain API compatibility. "
            "Frontend display: Can use interchangeably with risk_score. "
            "Precision: Rounded to 4 decimal places. "
            "Range: [0.0, 1.0]"
        ),
        examples=[0.1523, 0.6789, 0.9012]
    )

    confidence_level: str = Field(
        ...,  # Required
        description=(
            "REQUIRED. Human-readable confidence indicator. "
            "Business logic: "
            "  HIGH: Model very confident (probability near 0 or 1) "
            "  MEDIUM: Moderate confidence (probability 0.2-0.8) "
            "  LOW: Uncertain prediction (probability near 0.5) "
            "Frontend display: Show to users alongside prediction for transparency. "
            "Interpretation: LOW confidence suggests manual review regardless of prediction."
        ),
        examples=["HIGH", "MEDIUM", "LOW"]
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # EXPLANATORY FIELDS (OPTIONAL)
    # ═══════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════
    # EXPLANATORY FIELDS (OPTIONAL)
    # ═══════════════════════════════════════════════════════════════════════

    explanation: Optional[str] = Field(
        default=None,
        description=(
            "OPTIONAL. Human-readable explanation of risk assessment. "
            "Business logic: Plain-language summary of prediction reasoning. "
            "Content: Key factors, concerns, and decision rationale. "
            "Frontend display: Show in details panel or tooltip for transparency. "
            "Regulatory: Important for fair lending compliance (explainability). "
            "Null handling: If null, frontend should show generic message."
        ),
        examples=[
            "Low risk due to excellent credit score and stable income.",
            "High debt-to-income ratio and recent delinquencies increase risk.",
            "Strong credit profile with long employment history.",
        ]
    )

    key_factors: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "OPTIONAL. Key contributing factors to risk assessment (interpretability). "
            "Business logic: Dictionary of features with values and impact. "
            "Structure: {feature_name: {value: X, impact: 'positive'|'negative'|'neutral'}} "
            "Frontend display: Use for feature importance visualization. "
            "ML interpretability: Enables SHAP/LIME-style explanations. "
            "Null handling: If null, explanation text is sufficient."
        ),
        examples=[
            {
                "credit_score": {"value": 720, "impact": "positive"},
                "debt_to_income": {"value": 35.2, "impact": "neutral"},
                "delinquencies": {"value": 2, "impact": "negative"}
            }
        ]
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # FIELD VALIDATORS (BUSINESS LOGIC ENFORCEMENT)
    # ═══════════════════════════════════════════════════════════════════════

    @field_validator("recommended_action", mode='before')
    @classmethod
    def validate_recommended_action(cls, v: Any) -> str:
        """Validate and normalize recommended action.
        
        Accepts both string and enum, normalizes to uppercase.
        
        Args:
            v: Raw action value (string or enum)
            
        Returns:
            Validated RecommendedAction enum
            
        Raises:
            ValueError: If value not in allowed set
        """
        if isinstance(v, RecommendedAction):
            return v
        
        if isinstance(v, str):
            v_upper = v.upper()
            try:
                return RecommendedAction(v_upper)
            except ValueError:
                allowed = {e.value for e in RecommendedAction}
                raise ValueError(
                    f"recommended_action must be one of {allowed}, got '{v}'"
                )
        
        raise ValueError(f"recommended_action must be string or RecommendedAction, got {type(v)}")

    @field_validator("risk_level", mode='before')
    @classmethod
    def validate_risk_level(cls, v: Any) -> RiskLevel:
        """Validate risk level enum.
        
        Ensures risk_level is a valid RiskLevel enum value.
        
        Args:
            v: Raw risk level value
            
        Returns:
            Validated RiskLevel enum
            
        Raises:
            ValueError: If value not in RiskLevel enum
        """
        if isinstance(v, RiskLevel):
            return v
        
        if isinstance(v, str):
            v_upper = v.upper()
            try:
                return RiskLevel(v_upper)
            except ValueError:
                allowed = {e.value for e in RiskLevel}
                raise ValueError(
                    f"risk_level must be one of {allowed}, got '{v}'"
                )
        
        raise ValueError(f"risk_level must be string or RiskLevel, got {type(v)}")

    @field_validator("risk_score", "prediction_probability")
    @classmethod
    def validate_probability_precision(cls, v: float) -> float:
        """Validate probability values are safe, bounded, and consistently formatted.
        
        ROBUSTNESS: This validation exists because:
        1. NaN/Inf would break frontend charts, comparisons, and conditional logic
        2. Probabilities outside [0.0, 1.0] are mathematically invalid
        3. Excessive precision (e.g., 0.123456789) is noise, not signal
        4. ML models occasionally output edge cases (1e-10, 0.999999999)
        
        BUSINESS RULE: Risk score is primary decision metric
        ML IMPACT: Probabilities are model output, must be valid for all use cases
        
        Args:
            v: Probability value from model
            
        Returns:
            Validated and rounded probability (4 decimal places)
            
        Raises:
            ValueError: If probability is NaN, Inf, or outside [0.0, 1.0]
        """
        # Critical: Reject NaN/Inf (would break all downstream logic)
        if math.isnan(v) or math.isinf(v):
            raise ValueError(
                f"Probability cannot be NaN or Infinity, got {v}. "
                "This indicates a model inference error."
            )
        
        # Defensive: Probabilities must be in [0.0, 1.0]
        if not 0.0 <= v <= 1.0:
            raise ValueError(
                f"Probability must be between 0.0 and 1.0, got {v}. "
                "This indicates a model output error."
            )
        
        # Consistency: Round to 4 decimal places for frontend display
        # (e.g., 0.1523 = 15.23% risk)
        return round(v, 4)

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: str) -> str:
        """Validate confidence level string.
        
        ROBUSTNESS: This validation exists because:
        1. Empty confidence breaks frontend display logic
        2. Invalid values (typos) must be caught early
        3. Standardized values enable consistent UI rendering
        
        BUSINESS RULE: Confidence helps users interpret prediction reliability
        
        Args:
            v: Raw confidence level
            
        Returns:
            Validated uppercase confidence level
            
        Raises:
            ValueError: If not HIGH, MEDIUM, or LOW, or if empty
        """
        # Defensive: Reject empty strings
        if not v or not v.strip():
            raise ValueError(
                "confidence_level cannot be empty. "
                "Must be one of: HIGH, MEDIUM, LOW"
            )
        
        allowed = {"HIGH", "MEDIUM", "LOW"}
        v_upper = v.strip().upper()
        
        if v_upper not in allowed:
            raise ValueError(
                f"confidence_level must be one of {allowed}, got '{v}'"
            )
        
        return v_upper
    
    # ═══════════════════════════════════════════════════════════════════════
    # FACTORY METHODS (CONVENIENCE CONSTRUCTORS)
    # ═══════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════
    # FACTORY METHODS (CONVENIENCE CONSTRUCTORS)
    # ═══════════════════════════════════════════════════════════════════════

    @classmethod
    def from_risk_score(
        cls,
        risk_score: float,
        model_version: str,
        explanation: Optional[str] = None,
        key_factors: Optional[Dict[str, Any]] = None,
    ) -> "CreditRiskResponse":
        """Create response from risk score with automatic level/action assignment.
        
        This factory method derives risk_level, recommended_action, and confidence_level
        from the risk_score using production thresholds.
        
        Business Logic:
        - risk_score < 0.25  → LOW risk, APPROVE
        - risk_score < 0.50  → MEDIUM risk, REVIEW
        - risk_score < 0.75  → HIGH risk, REJECT
        - risk_score ≥ 0.75  → VERY_HIGH risk, REJECT
        
        Confidence Logic:
        - Probability < 0.2 or > 0.8 → HIGH confidence
        - Probability 0.2-0.8 → MEDIUM confidence
        - Probability 0.4-0.6 → LOW confidence (uncertain)
        
        Args:
            risk_score: Probability of default (0-1)
            model_version: Model identifier (required for traceability)
            explanation: Optional explanation text
            key_factors: Optional dict of contributing factors
            
        Returns:
            Complete CreditRiskResponse with all derived fields
            
        Example:
            >>> response = CreditRiskResponse.from_risk_score(
            ...     risk_score=0.15,
            ...     model_version="ml_v1.0.0",
            ...     explanation="Low risk applicant"
            ... )
            >>> response.risk_level
            <RiskLevel.LOW: 'LOW'>
            >>> response.recommended_action
            <RecommendedAction.APPROVE: 'APPROVE'>
        """
        # Derive risk level from score
        if risk_score < 0.25:
            risk_level = RiskLevel.LOW
            recommended_action = RecommendedAction.APPROVE
        elif risk_score < 0.50:
            risk_level = RiskLevel.MEDIUM
            recommended_action = RecommendedAction.REVIEW
        elif risk_score < 0.75:
            risk_level = RiskLevel.HIGH
            recommended_action = RecommendedAction.REJECT
        else:
            risk_level = RiskLevel.VERY_HIGH
            recommended_action = RecommendedAction.REJECT
        
        # Derive confidence level
        # High confidence when probability is extreme (near 0 or 1)
        # Low confidence when probability is uncertain (near 0.5)
        if risk_score < 0.2 or risk_score > 0.8:
            confidence_level = "HIGH"
        elif 0.4 <= risk_score <= 0.6:
            confidence_level = "LOW"
        else:
            confidence_level = "MEDIUM"

        return cls(
            schema_version="v1",
            risk_score=round(risk_score, 4),
            risk_level=risk_level,
            recommended_action=recommended_action,
            model_version=model_version,
            prediction_probability=round(risk_score, 4),
            confidence_level=confidence_level,
            explanation=explanation,
            key_factors=key_factors,
        )


# ═══════════════════════════════════════════════════════════════════════
# LEGACY COMPATIBILITY (DEPRECATED - DO NOT USE IN NEW CODE)
# ═══════════════════════════════════════════════════════════════════════

# Note: The old Config class style is deprecated in Pydantic v2
# Retained only for reference - model_config (ConfigDict) should be used
