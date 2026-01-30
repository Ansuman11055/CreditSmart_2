"""Request schemas for credit risk prediction API."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CreditRiskRequest(BaseModel):
    """Request schema for credit risk prediction.
    
    This schema validates input features for credit risk assessment.
    All numeric fields include range validation to ensure data quality.
    """

    annual_income: float = Field(
        ...,
        ge=0,
        le=10_000_000,
        description="Annual income in USD. Must be non-negative and reasonable.",
        examples=[50000, 75000, 120000]
    )

    monthly_debt: float = Field(
        ...,
        ge=0,
        le=100_000,
        description="Total monthly debt payments in USD. Includes loans, credit cards, etc.",
        examples=[500, 1200, 2500]
    )

    credit_score: int = Field(
        ...,
        ge=300,
        le=850,
        description="FICO credit score. Valid range is 300-850.",
        examples=[650, 720, 800]
    )

    loan_amount: float = Field(
        ...,
        gt=0,
        le=1_000_000,
        description="Requested loan amount in USD. Must be positive.",
        examples=[10000, 25000, 50000]
    )

    loan_term_months: int = Field(
        ...,
        ge=6,
        le=360,
        description="Loan term in months. Typically 12-360 months (1-30 years).",
        examples=[12, 36, 60, 120]
    )

    employment_length_years: float = Field(
        ...,
        ge=0,
        le=50,
        description="Years of employment at current job. 0 for unemployed/new job.",
        examples=[0, 2.5, 5, 10]
    )

    home_ownership: str = Field(
        ...,
        description="Home ownership status: 'RENT', 'OWN', 'MORTGAGE', or 'OTHER'.",
        examples=["RENT", "MORTGAGE", "OWN"]
    )

    purpose: str = Field(
        ...,
        description="Loan purpose: 'debt_consolidation', 'home_improvement', 'business', etc.",
        examples=["debt_consolidation", "home_improvement", "major_purchase"]
    )

    number_of_open_accounts: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Number of open credit accounts (cards, loans, etc.).",
        examples=[2, 5, 10]
    )

    delinquencies_2y: int = Field(
        default=0,
        ge=0,
        le=50,
        description="Number of 30+ day delinquencies in the past 2 years.",
        examples=[0, 1, 3]
    )

    inquiries_6m: int = Field(
        default=0,
        ge=0,
        le=20,
        description="Number of credit inquiries in the last 6 months.",
        examples=[0, 1, 2]
    )

    debt_to_income_ratio: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Debt-to-income ratio as percentage. Auto-calculated if not provided.",
        examples=[15.5, 30.0, 45.8]
    )

    @field_validator("home_ownership")
    @classmethod
    def validate_home_ownership(cls, v: str) -> str:
        """Validate home ownership status against allowed values."""
        allowed = {"RENT", "OWN", "MORTGAGE", "OTHER"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(
                f"home_ownership must be one of {allowed}, got '{v}'"
            )
        return v_upper

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        """Validate loan purpose against common categories."""
        allowed = {
            "debt_consolidation",
            "home_improvement",
            "major_purchase",
            "medical",
            "business",
            "car",
            "vacation",
            "wedding",
            "moving",
            "other",
        }
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(
                f"purpose must be one of {allowed}, got '{v}'"
            )
        return v_lower

    def compute_dti(self) -> float:
        """Compute debt-to-income ratio if not provided.
        
        Returns:
            Debt-to-income ratio as a percentage.
        """
        if self.debt_to_income_ratio is not None:
            return self.debt_to_income_ratio
        
        monthly_income = self.annual_income / 12
        if monthly_income == 0:
            return 0.0
        
        return round((self.monthly_debt / monthly_income) * 100, 2)

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
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
                "inquiries_6m": 1,
            }
        }
