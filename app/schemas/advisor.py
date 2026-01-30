"""Advisor response schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class FinancialAdvice(BaseModel):
    """Single piece of financial advice with priority and impact."""
    
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


class AdvisorResponse(BaseModel):
    """Response schema for financial advisor recommendations."""
    
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
        min_items=1,
        max_items=10
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
