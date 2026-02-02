"""Input safety validation for production inference.

Phase 3C-1: Production Readiness & System Hardening

This module provides additional runtime safety checks beyond Pydantic validation:
- NaN/Inf detection (pandas/numpy)
- Type coercion safety
- Range validation with clear error messages
- Data quality checks before inference
"""

import math
import structlog
from typing import Any, Dict, List, Tuple

logger = structlog.get_logger(__name__)


class InputSafetyError(Exception):
    """Raised when input data fails safety checks."""
    pass


def check_for_nan_inf(value: Any, field_name: str) -> None:
    """Check if a numeric value is NaN or Inf.
    
    Args:
        value: Value to check
        field_name: Field name for error messages
        
    Raises:
        InputSafetyError: If value is NaN or Inf
    """
    if isinstance(value, (int, float)):
        if math.isnan(value):
            raise InputSafetyError(
                f"Field '{field_name}' contains NaN (Not a Number). "
                f"Please provide a valid numeric value."
            )
        if math.isinf(value):
            raise InputSafetyError(
                f"Field '{field_name}' contains Infinity. "
                f"Please provide a finite numeric value."
            )


def validate_numeric_ranges(data: Dict[str, Any]) -> List[str]:
    """Validate numeric fields are within reasonable business ranges.
    
    This provides a second layer of validation beyond Pydantic to catch
    edge cases and provide better error messages.
    
    Args:
        data: Dictionary of field values
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Annual income checks
    if "annual_income" in data:
        income = data["annual_income"]
        if income is not None:
            if income < 0:
                errors.append("annual_income cannot be negative")
            elif income > 10_000_000:
                errors.append("annual_income exceeds maximum (10M)")
            elif income < 1000 and income > 0:
                errors.append("annual_income too low (minimum 1000)")
    
    # Monthly debt checks
    if "monthly_debt" in data:
        debt = data["monthly_debt"]
        if debt is not None:
            if debt < 0:
                errors.append("monthly_debt cannot be negative")
            elif debt > 100_000:
                errors.append("monthly_debt exceeds maximum (100K)")
    
    # Credit score checks (additional beyond Pydantic)
    if "credit_score" in data:
        score = data["credit_score"]
        if score is not None:
            if score < 300:
                errors.append("credit_score below minimum (300)")
            elif score > 850:
                errors.append("credit_score above maximum (850)")
    
    # Loan amount checks
    if "loan_amount" in data:
        amount = data["loan_amount"]
        if amount is not None:
            if amount <= 0:
                errors.append("loan_amount must be positive")
            elif amount > 1_000_000:
                errors.append("loan_amount exceeds maximum (1M)")
    
    # Loan term checks
    if "loan_term_months" in data:
        term = data["loan_term_months"]
        if term is not None:
            if term < 6:
                errors.append("loan_term_months below minimum (6)")
            elif term > 360:
                errors.append("loan_term_months exceeds maximum (360 = 30 years)")
    
    # Employment length checks
    if "employment_length_years" in data:
        years = data["employment_length_years"]
        if years is not None:
            if years < 0:
                errors.append("employment_length_years cannot be negative")
            elif years > 60:
                errors.append("employment_length_years exceeds maximum (60)")
    
    # Open accounts checks
    if "number_of_open_accounts" in data:
        accounts = data["number_of_open_accounts"]
        if accounts is not None:
            if accounts < 0:
                errors.append("number_of_open_accounts cannot be negative")
            elif accounts > 100:
                errors.append("number_of_open_accounts exceeds maximum (100)")
    
    # Delinquencies checks
    if "delinquencies_2y" in data:
        delinq = data["delinquencies_2y"]
        if delinq is not None:
            if delinq < 0:
                errors.append("delinquencies_2y cannot be negative")
            elif delinq > 50:
                errors.append("delinquencies_2y exceeds maximum (50)")
    
    # Inquiries checks
    if "inquiries_6m" in data:
        inq = data["inquiries_6m"]
        if inq is not None:
            if inq < 0:
                errors.append("inquiries_6m cannot be negative")
            elif inq > 50:
                errors.append("inquiries_6m exceeds maximum (50)")
    
    # DTI ratio checks (if provided)
    if "debt_to_income_ratio" in data and data["debt_to_income_ratio"] is not None:
        dti = data["debt_to_income_ratio"]
        if dti < 0:
            errors.append("debt_to_income_ratio cannot be negative")
        elif dti > 10:
            errors.append("debt_to_income_ratio exceeds maximum (10 = 1000%)")
    
    return errors


def validate_input_safety(request_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Perform comprehensive input safety validation.
    
    This function checks for:
    - NaN/Inf values in numeric fields
    - Reasonable business ranges
    - Data quality issues
    
    Args:
        request_data: Dictionary of request fields
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Define numeric fields to check for NaN/Inf
    numeric_fields = [
        "annual_income",
        "monthly_debt",
        "credit_score",
        "loan_amount",
        "loan_term_months",
        "employment_length_years",
        "number_of_open_accounts",
        "delinquencies_2y",
        "inquiries_6m",
        "debt_to_income_ratio"
    ]
    
    # Check for NaN/Inf in all numeric fields
    for field in numeric_fields:
        if field in request_data and request_data[field] is not None:
            try:
                check_for_nan_inf(request_data[field], field)
            except InputSafetyError as e:
                errors.append(str(e))
    
    # Validate numeric ranges
    range_errors = validate_numeric_ranges(request_data)
    errors.extend(range_errors)
    
    # Check for logical consistency
    if "annual_income" in request_data and "monthly_debt" in request_data:
        income = request_data.get("annual_income")
        debt = request_data.get("monthly_debt")
        
        if income is not None and debt is not None:
            # Check if monthly debt exceeds annual income (clearly wrong)
            if debt * 12 > income * 10:  # Monthly debt > 10x annual income
                errors.append(
                    "monthly_debt is unreasonably high compared to annual_income "
                    "(exceeds 10x annual income)"
                )
    
    # Check loan amount vs income ratio
    if "loan_amount" in request_data and "annual_income" in request_data:
        loan = request_data.get("loan_amount")
        income = request_data.get("annual_income")
        
        if loan is not None and income is not None and income > 0:
            loan_to_income = loan / income
            if loan_to_income > 100:  # Loan > 100x annual income
                errors.append(
                    "loan_amount is unreasonably high compared to annual_income "
                    "(exceeds 100x annual income)"
                )
    
    is_valid = len(errors) == 0
    
    if not is_valid:
        logger.warning(
            "input_safety_validation_failed",
            error_count=len(errors),
            errors=errors[:3]  # Log first 3 errors only
        )
    
    return is_valid, errors


def sanitize_error_message(error_msg: str) -> str:
    """Sanitize error message for frontend display.
    
    Removes:
    - File paths
    - Internal variable names
    - Stack trace references
    
    Args:
        error_msg: Raw error message
        
    Returns:
        Sanitized error message safe for frontend
    """
    # Remove file paths (Windows and Unix)
    import re
    
    # Remove Windows paths (e.g., C:\...\file.py)
    sanitized = re.sub(r'[A-Za-z]:\\[^\s]+\.py', '[file]', error_msg)
    
    # Remove Unix paths (e.g., /app/ml/model.py)
    sanitized = re.sub(r'/[\w/]+\.py', '[file]', sanitized)
    
    # Remove line numbers (e.g., "line 123")
    sanitized = re.sub(r'line \d+', 'line [N]', sanitized)
    
    # Remove Python traceback markers
    sanitized = sanitized.replace('Traceback (most recent call last):', '')
    sanitized = sanitized.replace('File "', '')
    
    # Remove internal variable references (e.g., "variable 'x' ")
    sanitized = re.sub(r"variable '[^']+' ", '', sanitized)
    
    # Collapse multiple spaces
    sanitized = ' '.join(sanitized.split())
    
    return sanitized.strip()


def create_safe_error_response(
    error_code: str,
    user_message: str,
    internal_details: str = None
) -> Dict[str, Any]:
    """Create a production-safe error response.
    
    Args:
        error_code: Error code (e.g., "INPUT_VALIDATION_ERROR")
        user_message: User-friendly message
        internal_details: Internal details (logged but not returned)
        
    Returns:
        Safe error response dictionary
    """
    if internal_details:
        logger.error(
            "error_response_created",
            error_code=error_code,
            user_message=user_message,
            internal_details=internal_details
        )
    
    return {
        "error": True,
        "code": error_code,
        "message": sanitize_error_message(user_message)
    }
