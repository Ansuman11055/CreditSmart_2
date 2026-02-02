"""Request schemas for credit risk prediction API.

PRODUCTION CONTRACT - FROZEN AS OF 2026-01-31
This schema is a versioned API contract. Breaking changes require a new schema version.

VALIDATION ROBUSTNESS:
- All numeric fields protected against NaN/Inf values
- Categorical fields validated against strict enums (no silent coercion)
- Empty payloads rejected (all 11 fields required)
- Clear error messages for invalid inputs
- No frontend assumptions (backend-first validation)
"""

import math
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class CreditRiskRequest(BaseModel):
    """Production-grade request schema for credit risk prediction (Schema Version: v1).
    
    This schema represents a frozen API contract for credit risk assessment.
    All fields are explicitly defined with strict type and range validation.
    
    ═══════════════════════════════════════════════════════════════════════
    PRODUCTION CONTRACT GUARANTEES:
    ═══════════════════════════════════════════════════════════════════════
    - Extra fields are FORBIDDEN (HTTP 422 error)
    - All 11 required fields must be present
    - Data types must match exactly (no implicit coercion)
    - Numeric values must be within business-logical ranges
    - Categorical values must match allowed enums
    - Schema version field ensures forward compatibility
    
    ═══════════════════════════════════════════════════════════════════════
    FIELD REQUIREMENTS (11 required + 1 optional):
    ═══════════════════════════════════════════════════════════════════════
    REQUIRED (11 fields):
      1. annual_income          - Applicant's annual income (USD)
      2. monthly_debt           - Total monthly debt payments (USD)
      3. credit_score           - FICO credit score (300-850)
      4. loan_amount            - Requested loan amount (USD)
      5. loan_term_months       - Loan duration in months
      6. employment_length_years - Years at current job
      7. home_ownership         - Housing status (RENT/OWN/MORTGAGE/OTHER)
      8. purpose                - Loan purpose category
      9. number_of_open_accounts - Count of open credit accounts
     10. delinquencies_2y       - Past delinquencies (2 years)
     11. inquiries_6m           - Recent credit inquiries (6 months)
    
    OPTIONAL (1 field):
      - debt_to_income_ratio    - DTI percentage (auto-computed if omitted)
    
    ═══════════════════════════════════════════════════════════════════════
    ML MODEL ALIGNMENT:
    ═══════════════════════════════════════════════════════════════════════
    This schema maps 1:1 with trained model features:
    - 11 raw input features (as defined above)
    - 1 computed feature (debt_to_income_ratio)
    - Total: 12 features fed to preprocessor → one-hot encoding → model
    
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
        str_strip_whitespace=True,  # Strip whitespace from string inputs
        validate_assignment=True,  # Validate on field assignment
        frozen=False,  # Allow mutation for DTI computation
        json_schema_extra={
            "example": {
                "schema_version": "v1",
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
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # FINANCIAL FEATURES (REQUIRED)
    # ═══════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════
    # FINANCIAL FEATURES (REQUIRED)
    # ═══════════════════════════════════════════════════════════════════════

    annual_income: float = Field(
        ...,  # Required (no default value)
        ge=0,  # Greater than or equal to 0
        le=10_000_000,  # Maximum reasonable income
        description=(
            "REQUIRED. Applicant's total annual income in USD before taxes. "
            "Business logic: Must be non-negative and below $10M. "
            "ML impact: Strong predictor of repayment capacity. "
            "Range: [0, 10,000,000]"
        ),
        examples=[50000, 75000, 120000]
    )

    monthly_debt: float = Field(
        ...,  # Required
        ge=0,
        le=100_000,
        description=(
            "REQUIRED. Total monthly debt obligations in USD (loans, credit cards, etc.). "
            "Business logic: Includes all recurring debt payments. "
            "ML impact: Used to compute debt-to-income ratio (DTI). "
            "Range: [0, 100,000]"
        ),
        examples=[500, 1200, 2500]
    )

    credit_score: int = Field(
        ...,  # Required
        ge=300,
        le=850,
        description=(
            "REQUIRED. FICO credit score representing creditworthiness. "
            "Business logic: Standard FICO range is 300-850. "
            "ML impact: Strongest single predictor in most credit models. "
            "Range: [300, 850]"
        ),
        examples=[650, 720, 800]
    )

    loan_amount: float = Field(
        ...,  # Required
        gt=0,  # Must be strictly positive
        le=1_000_000,
        description=(
            "REQUIRED. Requested loan amount in USD. "
            "Business logic: Must be positive (> 0) and below $1M limit. "
            "ML impact: Interacts with income to determine affordability. "
            "Range: (0, 1,000,000]"
        ),
        examples=[10000, 25000, 50000]
    )

    loan_term_months: int = Field(
        ...,  # Required
        ge=6,
        le=360,
        description=(
            "REQUIRED. Loan duration in months. "
            "Business logic: Typical range is 12-360 months (1-30 years). "
            "ML impact: Longer terms increase default risk. "
            "Range: [6, 360]"
        ),
        examples=[12, 36, 60, 120]
    )

    employment_length_years: float = Field(
        ...,  # Required
        ge=0,
        le=50,
        description=(
            "REQUIRED. Years employed at current job (decimal allowed for partial years). "
            "Business logic: 0 indicates unemployed or new employment. "
            "ML impact: Employment stability correlates with repayment ability. "
            "Range: [0, 50]"
        ),
        examples=[0, 2.5, 5, 10]
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORICAL FEATURES (REQUIRED)
    # ═══════════════════════════════════════════════════════════════════════

    home_ownership: str = Field(
        ...,  # Required
        description=(
            "REQUIRED. Housing ownership status. "
            "Allowed values: 'RENT', 'OWN', 'MORTGAGE', 'OTHER' (case-insensitive). "
            "Business logic: Indicates financial stability and collateral. "
            "ML impact: One-hot encoded for model input. "
            "Validation: Converted to uppercase, must match enum."
        ),
        examples=["RENT", "MORTGAGE", "OWN"]
    )

    purpose: str = Field(
        ...,  # Required
        description=(
            "REQUIRED. Loan purpose category. "
            "Allowed values: 'debt_consolidation', 'home_improvement', 'major_purchase', "
            "'medical', 'business', 'car', 'vacation', 'wedding', 'moving', 'other' (case-insensitive). "
            "Business logic: Different purposes have different risk profiles. "
            "ML impact: One-hot encoded for model input. "
            "Validation: Converted to lowercase, must match enum."
        ),
        examples=["debt_consolidation", "home_improvement", "major_purchase"]
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # CREDIT HISTORY FEATURES (REQUIRED)
    # ═══════════════════════════════════════════════════════════════════════

    number_of_open_accounts: int = Field(
        ...,  # Required (no default)
        ge=0,
        le=100,
        description=(
            "REQUIRED. Count of currently open credit accounts (cards, loans, lines of credit). "
            "Business logic: Indicates credit utilization and history depth. "
            "ML impact: Too few or too many accounts can indicate risk. "
            "Range: [0, 100]"
        ),
        examples=[2, 5, 10]
    )

    delinquencies_2y: int = Field(
        ...,  # Required (no default)
        ge=0,
        le=50,
        description=(
            "REQUIRED. Number of 30+ day payment delinquencies in past 2 years. "
            "Business logic: Direct indicator of payment history. "
            "ML impact: Strong negative predictor (delinquencies = higher risk). "
            "Range: [0, 50]"
        ),
        examples=[0, 1, 3]
    )

    inquiries_6m: int = Field(
        ...,  # Required (no default)
        ge=0,
        le=20,
        description=(
            "REQUIRED. Number of hard credit inquiries in last 6 months. "
            "Business logic: Multiple inquiries suggest credit shopping or financial stress. "
            "ML impact: High inquiry count correlates with default risk. "
            "Range: [0, 20]"
        ),
        examples=[0, 1, 2]
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # COMPUTED FEATURES (OPTIONAL - AUTO-CALCULATED)
    # ═══════════════════════════════════════════════════════════════════════

    debt_to_income_ratio: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description=(
            "OPTIONAL. Debt-to-income ratio as percentage (monthly_debt / monthly_income * 100). "
            "Business logic: Key affordability metric. DTI > 43% often disqualifies loans. "
            "ML impact: Critical feature for default prediction. "
            "Auto-computed: If not provided, calculated from annual_income and monthly_debt. "
            "Range: [0, 100]"
        ),
        examples=[15.5, 30.0, 45.8]
    )
    
    # ═══════════════════════════════════════════════════════════════════════
    # FIELD VALIDATORS (BUSINESS LOGIC ENFORCEMENT)
    # ═══════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════
    # FIELD VALIDATORS (BUSINESS LOGIC ENFORCEMENT)
    # ═══════════════════════════════════════════════════════════════════════

    @field_validator("home_ownership")
    @classmethod
    def validate_home_ownership(cls, v: str) -> str:
        """Validate and normalize home ownership status.
        
        ROBUSTNESS: This validation exists because:
        1. ML model was trained on specific one-hot encoded categories
        2. Unknown categories would create feature misalignment → incorrect predictions
        3. Empty strings or whitespace must be rejected (no silent defaults)
        4. Case insensitivity improves UX while maintaining data integrity
        
        BUSINESS RULE: Home ownership affects loan risk (MORTGAGE > OWN > RENT)
        
        Args:
            v: Raw home ownership value
            
        Returns:
            Normalized uppercase value
            
        Raises:
            ValueError: If value not in allowed set or is empty/whitespace
        """
        # Defensive: Reject empty strings (no silent coercion to defaults)
        if not v or not v.strip():
            raise ValueError(
                "home_ownership cannot be empty. "
                "Must be one of: RENT, OWN, MORTGAGE, OTHER"
            )
        
        allowed = {"RENT", "OWN", "MORTGAGE", "OTHER"}
        v_upper = v.strip().upper()
        
        if v_upper not in allowed:
            raise ValueError(
                f"home_ownership must be one of {allowed}, got '{v}'. "
                f"This field is required for accurate risk assessment."
            )
        return v_upper

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        """Validate and normalize loan purpose.
        
        ROBUSTNESS: This validation exists because:
        1. ML model learned risk patterns per purpose (business loans != vacation loans)
        2. Unknown purposes would create feature vector misalignment
        3. Empty/whitespace values must fail fast (no assumptions)
        4. Typos or variations must be caught ("consolidation" != "debt_consolidation")
        
        BUSINESS RULE: Loan purpose affects default risk significantly
        
        Args:
            v: Raw purpose value
            
        Returns:
            Normalized lowercase value
            
        Raises:
            ValueError: If value not in allowed set or is empty/whitespace
        """
        # Defensive: Reject empty strings (no silent defaults)
        if not v or not v.strip():
            raise ValueError(
                "purpose cannot be empty. "
                "Must be one of: debt_consolidation, home_improvement, major_purchase, "
                "medical, business, car, vacation, wedding, moving, other"
            )
        
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
        v_lower = v.strip().lower()
        
        if v_lower not in allowed:
            raise ValueError(
                f"purpose must be one of {allowed}, got '{v}'. "
                f"This field is critical for risk assessment accuracy."
            )
        return v_lower

    @field_validator("annual_income")
    @classmethod
    def validate_annual_income(cls, v: float) -> float:
        """Validate annual income is within reasonable bounds and safe for ML inference.
        
        ROBUSTNESS: This validation exists because:
        1. NaN/Inf would corrupt model input → unpredictable predictions
        2. Negative income is logically impossible (data quality issue)
        3. Extreme values (>10M) outside training distribution → unreliable predictions
        4. Zero income is valid (unemployed applicants) but risky
        
        BUSINESS RULE: Income is primary repayment capacity indicator
        ML IMPACT: High-importance feature in most credit risk models
        
        Args:
            v: Annual income value
            
        Returns:
            Validated income
            
        Raises:
            ValueError: If income is NaN, Inf, negative, or exceeds reasonable maximum
        """
        # Critical: Reject NaN/Inf (would break model inference)
        if math.isnan(v) or math.isinf(v):
            raise ValueError(
                f"annual_income cannot be NaN or Infinity, got {v}. "
                "Please provide a valid numeric income value."
            )
        
        # Defensive: Negative income is nonsensical
        if v < 0:
            raise ValueError(
                f"annual_income cannot be negative, got {v}. "
                "Income must be 0 or greater."
            )
        
        # Defensive: Extreme outliers outside training distribution
        if v > 10_000_000:
            raise ValueError(
                f"annual_income exceeds maximum reasonable value (10M), got {v}. "
                "Please verify the input or contact support for high-value cases."
            )
        
        return v
    
    @field_validator("credit_score")
    @classmethod
    def validate_credit_score(cls, v: int) -> int:
        """Validate credit score is within FICO range.
        
        ROBUSTNESS: This validation exists because:
        1. FICO scores are legally defined as 300-850 (industry standard)
        2. Scores outside this range indicate data quality issues or wrong scoring model
        3. Model was trained on FICO distribution → out-of-range = unreliable
        4. Integer type enforced (no 725.5 scores)
        
        BUSINESS RULE: Credit score is strongest single default predictor
        ML IMPACT: Typically highest feature importance in credit models
        
        Args:
            v: Credit score value
            
        Returns:
            Validated score
            
        Raises:
            ValueError: If score outside FICO range [300, 850]
        """
        if not 300 <= v <= 850:
            raise ValueError(
                f"credit_score must be between 300 and 850 (FICO range), got {v}. "
                "Please verify the score or use a different scoring model."
            )
        return v
    
    @field_validator("loan_amount")
    @classmethod
    def validate_loan_amount(cls, v: float) -> float:
        """Validate loan amount is positive, reasonable, and safe for ML inference.
        
        ROBUSTNESS: This validation exists because:
        1. NaN/Inf would corrupt model predictions
        2. Zero/negative amounts are logically impossible (no such thing as $0 loan)
        3. Extreme amounts (>1M) outside training distribution
        4. Loan amount interacts with income for affordability calculation
        
        BUSINESS RULE: Loan amount must be strictly positive
        ML IMPACT: Affects loan-to-income ratio (key risk factor)
        
        Args:
            v: Loan amount value
            
        Returns:
            Validated amount
            
        Raises:
            ValueError: If amount is NaN, Inf, non-positive, or exceeds maximum
        """
        # Critical: Reject NaN/Inf (would break model inference)
        if math.isnan(v) or math.isinf(v):
            raise ValueError(
                f"loan_amount cannot be NaN or Infinity, got {v}. "
                "Please provide a valid numeric loan amount."
            )
        
        # Defensive: Zero or negative loans are nonsensical
        if v <= 0:
            raise ValueError(
                f"loan_amount must be positive, got {v}. "
                "Cannot request a loan of $0 or less."
            )
        
        # Defensive: Extreme outliers outside training distribution
        if v > 1_000_000:
            raise ValueError(
                f"loan_amount exceeds maximum (1M), got {v}. "
                "Please verify the amount or contact support for large loans."
            )
        
        return v
    
    @field_validator("monthly_debt")
    @classmethod
    def validate_monthly_debt(cls, v: float) -> float:
        """Validate monthly debt is non-negative and safe for ML inference.
        
        ROBUSTNESS: This validation exists because:
        1. NaN/Inf would corrupt debt-to-income ratio calculation
        2. Negative debt is impossible (you can't owe negative money)
        3. Extreme values (>100k/month) outside training distribution
        4. Zero debt is valid (debt-free applicants)
        
        BUSINESS RULE: Monthly debt is used to calculate DTI ratio (critical metric)
        ML IMPACT: High-importance feature for affordability assessment
        
        Args:
            v: Monthly debt value
            
        Returns:
            Validated debt amount
            
        Raises:
            ValueError: If debt is NaN, Inf, negative, or exceeds maximum
        """
        # Critical: Reject NaN/Inf (would break DTI calculation)
        if math.isnan(v) or math.isinf(v):
            raise ValueError(
                f"monthly_debt cannot be NaN or Infinity, got {v}. "
                "Please provide a valid numeric debt amount."
            )
        
        # Defensive: Negative debt is nonsensical
        if v < 0:
            raise ValueError(
                f"monthly_debt cannot be negative, got {v}. "
                "Debt must be 0 or greater."
            )
        
        # Defensive: Extreme outliers (>100k/month debt)
        if v > 100_000:
            raise ValueError(
                f"monthly_debt exceeds maximum (100k), got {v}. "
                "Please verify this value."
            )
        
        return v
    
    @field_validator("employment_length_years")
    @classmethod
    def validate_employment_length(cls, v: float) -> float:
        """Validate employment length is non-negative and reasonable.
        
        ROBUSTNESS: This validation exists because:
        1. NaN/Inf would corrupt model predictions
        2. Negative employment length is impossible (can't work -5 years)
        3. Extreme values (>50 years) outside realistic employment spans
        4. Zero is valid (unemployed or just started)
        
        BUSINESS RULE: Employment stability indicates income reliability
        ML IMPACT: Longer employment generally reduces default risk
        
        Args:
            v: Employment length in years (decimals allowed)
            
        Returns:
            Validated employment length
            
        Raises:
            ValueError: If length is NaN, Inf, negative, or exceeds maximum
        """
        # Critical: Reject NaN/Inf (would break model inference)
        if math.isnan(v) or math.isinf(v):
            raise ValueError(
                f"employment_length_years cannot be NaN or Infinity, got {v}. "
                "Please provide a valid numeric employment length."
            )
        
        # Defensive: Negative employment is nonsensical
        if v < 0:
            raise ValueError(
                f"employment_length_years cannot be negative, got {v}. "
                "Employment length must be 0 or greater."
            )
        
        # Defensive: Unrealistic employment spans
        if v > 50:
            raise ValueError(
                f"employment_length_years exceeds reasonable maximum (50), got {v}. "
                "Please verify this value."
            )
        
        return v
    
    @field_validator("debt_to_income_ratio")
    @classmethod
    def validate_dti_ratio(cls, v: Optional[float]) -> Optional[float]:
        """Validate debt-to-income ratio is reasonable and safe for ML inference.
        
        ROBUSTNESS: This validation exists because:
        1. NaN/Inf would corrupt model predictions (DTI is critical feature)
        2. Negative DTI is impossible (both debt and income are non-negative)
        3. DTI > 100% is technically possible but extremely rare
        4. None is allowed (auto-computed from income/debt)
        
        BUSINESS RULE: DTI > 43% often disqualifies loans (standard threshold)
        ML IMPACT: One of the most important affordability metrics
        
        Args:
            v: DTI ratio as percentage (or None to auto-compute)
            
        Returns:
            Validated DTI ratio or None
            
        Raises:
            ValueError: If DTI is NaN, Inf, negative, or exceeds maximum
        """
        # Allow None (will be auto-computed)
        if v is None:
            return v
        
        # Critical: Reject NaN/Inf (would break model inference)
        if math.isnan(v) or math.isinf(v):
            raise ValueError(
                f"debt_to_income_ratio cannot be NaN or Infinity, got {v}. "
                "Please provide a valid numeric DTI ratio or omit for auto-computation."
            )
        
        # Defensive: Negative DTI is nonsensical
        if v < 0:
            raise ValueError(
                f"debt_to_income_ratio cannot be negative, got {v}. "
                "DTI must be 0 or greater."
            )
        
        # Defensive: Extreme DTI values (>100% is rare but possible)
        if v > 100:
            raise ValueError(
                f"debt_to_income_ratio exceeds maximum (100%), got {v}. "
                "Please verify this calculation."
            )
        
        return v
    
    # ═══════════════════════════════════════════════════════════════════════
    # COMPUTED METHODS (BUSINESS LOGIC)
    # ═══════════════════════════════════════════════════════════════════════

    def compute_dti(self) -> float:
        """Compute debt-to-income ratio if not explicitly provided.
        
        Business Logic:
        - DTI = (monthly_debt / monthly_income) * 100
        - monthly_income = annual_income / 12
        - If annual_income is 0, DTI defaults to 0 (edge case)
        
        This is a critical affordability metric used by lenders.
        Standard thresholds:
        - DTI < 36%: Good
        - DTI 36-43%: Acceptable
        - DTI > 43%: High risk (often disqualified)
        
        Returns:
            Debt-to-income ratio as percentage (0-100+)
        """
        if self.debt_to_income_ratio is not None:
            return self.debt_to_income_ratio
        
        monthly_income = self.annual_income / 12
        if monthly_income == 0:
            return 0.0
        
        return round((self.monthly_debt / monthly_income) * 100, 2)
