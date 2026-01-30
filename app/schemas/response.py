"""Response schemas for credit risk prediction API."""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    """Credit risk level classification.
    
    These levels represent the assessed risk of loan default:
    - LOW: Minimal risk, excellent credit profile
    - MEDIUM: Moderate risk, acceptable credit profile  
    - HIGH: Elevated risk, requires additional scrutiny
    - VERY_HIGH: Severe risk, high probability of default
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class CreditRiskResponse(BaseModel):
    """Response schema for credit risk prediction.
    
    Returns the model's risk assessment including numeric score,
    categorical risk level, and optional explanation.
    """

    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability of default. 0 = no risk, 1 = certain default.",
        examples=[0.05, 0.25, 0.65, 0.90]
    )

    risk_level: RiskLevel = Field(
        ...,
        description="Categorical risk level derived from risk_score.",
        examples=["LOW", "MEDIUM", "HIGH"]
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Model confidence in the prediction (0-1). Lower indicates uncertainty.",
        examples=[0.85, 0.92, 0.78]
    )

    recommended_action: str = Field(
        ...,
        description="Recommended action: 'APPROVE', 'REVIEW', or 'REJECT'.",
        examples=["APPROVE", "REVIEW", "REJECT"]
    )

    explanation: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of the risk assessment.",
        examples=[
            "Low risk due to excellent credit score and stable income.",
            "High debt-to-income ratio and recent delinquencies increase risk.",
        ]
    )

    key_factors: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Key contributing factors to the risk score (for interpretability).",
        examples=[
            {
                "credit_score": {"value": 720, "impact": "positive"},
                "debt_to_income": {"value": 35.2, "impact": "neutral"},
                "delinquencies": {"value": 2, "impact": "negative"}
            }
        ]
    )

    model_version: Optional[str] = Field(
        default=None,
        description="Version of the ML model used for prediction.",
        examples=["v1.0.0", "v1.2.3"]
    )

    @field_validator("recommended_action")
    @classmethod
    def validate_recommended_action(cls, v: str) -> str:
        """Validate recommended action against allowed values."""
        allowed = {"APPROVE", "REVIEW", "REJECT"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(
                f"recommended_action must be one of {allowed}, got '{v}'"
            )
        return v_upper

    @classmethod
    def from_risk_score(
        cls,
        risk_score: float,
        confidence: float = 1.0,
        explanation: Optional[str] = None,
        key_factors: Optional[Dict[str, Any]] = None,
        model_version: Optional[str] = None,
    ) -> "CreditRiskResponse":
        """Create response from risk score with automatic level/action assignment.
        
        Args:
            risk_score: Probability of default (0-1)
            confidence: Model confidence (0-1)
            explanation: Optional explanation text
            key_factors: Optional dict of contributing factors
            model_version: Optional model version string
            
        Returns:
            Complete CreditRiskResponse with derived fields
        """
        # Derive risk level from score
        if risk_score < 0.25:
            risk_level = RiskLevel.LOW
            recommended_action = "APPROVE"
        elif risk_score < 0.50:
            risk_level = RiskLevel.MEDIUM
            recommended_action = "REVIEW"
        elif risk_score < 0.75:
            risk_level = RiskLevel.HIGH
            recommended_action = "REJECT"
        else:
            risk_level = RiskLevel.VERY_HIGH
            recommended_action = "REJECT"

        return cls(
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=confidence,
            recommended_action=recommended_action,
            explanation=explanation,
            key_factors=key_factors,
            model_version=model_version,
        )

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "risk_score": 0.15,
                "risk_level": "LOW",
                "confidence": 0.92,
                "recommended_action": "APPROVE",
                "explanation": "Strong credit profile with stable income and no recent delinquencies.",
                "key_factors": {
                    "credit_score": {"value": 780, "impact": "positive"},
                    "employment_length": {"value": 8, "impact": "positive"},
                    "debt_to_income": {"value": 18.5, "impact": "positive"}
                },
                "model_version": "v1.0.0"
            }
        }
