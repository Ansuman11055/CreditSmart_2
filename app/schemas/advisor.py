"""Advisor response schemas.

VALIDATION ROBUSTNESS:
- All float fields protected against NaN/Inf
- Categorical fields validated against strict enums
- String fields checked for empty values
- Risk scores bounded to [0.0, 1.0]
- No silent coercion or assumptions
"""

import math
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class FinancialAdvice(BaseModel):
    """Single piece of financial advice with priority and impact.
    
    All fields are required and validated for robustness.
    """
    
    category: str = Field(
        ...,
        description="Advice category: 'credit_score', 'debt_management', 'income', 'payment_history'",
        examples=["credit_score", "debt_management"]
    )
    
    priority: str = Field(
        ...,
        description="Priority level: 'HIGH', 'MEDIUM', or 'LOW'",
        examples=["HIGH", "MEDIUM", "LOW"]
    )
    
    suggestion: str = Field(
        ...,
        description="Actionable improvement suggestion",
        examples=["Pay down credit card balances to below 30% utilization"]
    )
    
    expected_impact: str = Field(
        ...,
        description="Expected impact on risk score",
        examples=["Could reduce risk score by 15-20 points"]
    )
    
    timeframe: str = Field(
        ...,
        description="Expected timeframe to see results",
        examples=["3-6 months", "Immediate", "1-2 years"]
    )
    
    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate advice category against allowed values.
        
        ROBUSTNESS: Prevents typos and ensures consistent categorization.
        ML IMPACT: Categories used for grouping/filtering recommendations.
        
        Args:
            v: Category value
            
        Returns:
            Validated lowercase category
            
        Raises:
            ValueError: If category not in allowed set or empty
        """
        # Defensive: Reject empty strings
        if not v or not v.strip():
            raise ValueError(
                "category cannot be empty. "
                "Must be one of: credit_score, debt_management, income, payment_history"
            )
        
        allowed = {"credit_score", "debt_management", "income", "payment_history"}
        v_lower = v.strip().lower()
        
        if v_lower not in allowed:
            raise ValueError(
                f"category must be one of {allowed}, got '{v}'"
            )
        
        return v_lower
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority level against allowed values.
        
        ROBUSTNESS: Ensures consistent priority levels for sorting.
        BUSINESS RULE: HIGH > MEDIUM > LOW priority ordering.
        
        Args:
            v: Priority value
            
        Returns:
            Validated uppercase priority
            
        Raises:
            ValueError: If priority not in allowed set or empty
        """
        # Defensive: Reject empty strings
        if not v or not v.strip():
            raise ValueError(
                "priority cannot be empty. "
                "Must be one of: HIGH, MEDIUM, LOW"
            )
        
        allowed = {"HIGH", "MEDIUM", "LOW"}
        v_upper = v.strip().upper()
        
        if v_upper not in allowed:
            raise ValueError(
                f"priority must be one of {allowed}, got '{v}'"
            )
        
        return v_upper
    
    @field_validator("suggestion", "expected_impact", "timeframe")
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Validate string fields are not empty.
        
        ROBUSTNESS: Empty advice is useless to users.
        
        Args:
            v: String value
            
        Returns:
            Validated trimmed string
            
        Raises:
            ValueError: If string is empty or whitespace-only
        """
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace-only")
        
        return v.strip()


class AdvisorResponse(BaseModel):
    """Response schema for financial advisor recommendations.
    
    All risk scores validated for NaN/Inf safety.
    """
    
    overall_assessment: str = Field(
        ...,
        description="High-level summary of financial health",
        examples=["Good financial position with minor improvement opportunities"]
    )
    
    current_risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Current risk score (0-1 scale)",
        examples=[0.25, 0.65]
    )
    
    potential_risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Potential risk score if advice is followed",
        examples=[0.15, 0.45]
    )
    
    recommendations: List[FinancialAdvice] = Field(
        ...,
        description="Ordered list of recommendations (highest priority first)",
        min_length=1,  # Updated from deprecated min_items
        max_length=10   # Updated from deprecated max_items
    )
    
    strengths: List[str] = Field(
        default_factory=list,
        description="Current financial strengths to maintain",
        examples=[["Clean payment history", "Stable employment"]]
    )
    
    next_steps: Optional[str] = Field(
        default=None,
        description="Immediate next steps to take",
        examples=["Focus on paying down high-interest debt and avoid new credit inquiries"]
    )
    
    @field_validator("current_risk_score", "potential_risk_score")
    @classmethod
    def validate_risk_scores(cls, v: float) -> float:
        """Validate risk scores are safe numeric values.
        
        ROBUSTNESS: NaN/Inf would break frontend display and comparisons.
        BUSINESS RULE: Risk scores must be in [0.0, 1.0] range.
        
        Args:
            v: Risk score value
            
        Returns:
            Validated risk score
            
        Raises:
            ValueError: If score is NaN, Inf, or out of bounds
        """
        # Critical: Reject NaN/Inf
        if math.isnan(v) or math.isinf(v):
            raise ValueError(
                f"risk_score cannot be NaN or Infinity, got {v}"
            )
        
        # Pydantic ge/le already checks bounds, but explicit check for clarity
        if not 0.0 <= v <= 1.0:
            raise ValueError(
                f"risk_score must be between 0.0 and 1.0, got {v}"
            )
        
        return v
    
    @field_validator("overall_assessment")
    @classmethod
    def validate_assessment_not_empty(cls, v: str) -> str:
        """Validate assessment is not empty.
        
        ROBUSTNESS: Empty assessments provide no value to users.
        
        Args:
            v: Assessment text
            
        Returns:
            Validated trimmed text
            
        Raises:
            ValueError: If text is empty or whitespace-only
        """
        if not v or not v.strip():
            raise ValueError("overall_assessment cannot be empty")
        
        return v.strip()
    
    @field_validator("recommendations")
    @classmethod
    def validate_recommendations_not_empty(cls, v: List[FinancialAdvice]) -> List[FinancialAdvice]:
        """Validate recommendations list is not empty.
        
        ROBUSTNESS: Advisor must provide at least one recommendation.
        BUSINESS RULE: Empty recommendations = failed analysis.
        
        Args:
            v: List of recommendations
            
        Returns:
            Validated list
            
        Raises:
            ValueError: If list is empty
        """
        if not v or len(v) == 0:
            raise ValueError(
                "recommendations cannot be empty. "
                "At least 1 recommendation required."
            )
        
        return v
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "overall_assessment": "Moderate risk profile with clear improvement path",
                "current_risk_score": 0.45,
                "potential_risk_score": 0.25,
                "recommendations": [
                    {
                        "category": "debt_management",
                        "priority": "HIGH",
                        "suggestion": "Reduce debt-to-income ratio from 45% to below 36%",
                        "expected_impact": "Could reduce risk score by 20-25 points",
                        "timeframe": "6-12 months"
                    },
                    {
                        "category": "credit_score",
                        "priority": "MEDIUM",
                        "suggestion": "Work on improving credit score through on-time payments",
                        "expected_impact": "Could reduce risk score by 10-15 points",
                        "timeframe": "3-6 months"
                    }
                ],
                "strengths": [
                    "Stable employment for 5+ years",
                    "No recent delinquencies"
                ],
                "next_steps": "Prioritize debt reduction and maintain clean payment history"
            }
        }
