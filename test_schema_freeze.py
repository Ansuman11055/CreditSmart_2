"""Test frozen schema v1 contract."""

from app.schemas.request import CreditRiskRequest
from pydantic import ValidationError
import pytest


def test_schema_version_present():
    """Test that schema_version field exists and defaults to v1."""
    req = CreditRiskRequest(
        annual_income=60000,
        monthly_debt=2000,
        credit_score=720,
        loan_amount=20000,
        loan_term_months=48,
        employment_length_years=5,
        home_ownership='MORTGAGE',
        purpose='debt_consolidation',
        number_of_open_accounts=3,
        delinquencies_2y=0,
        inquiries_6m=1
    )
    assert req.schema_version == "v1", "Schema version should default to v1"


def test_extra_fields_rejected():
    """Test that extra fields are rejected with extra='forbid'."""
    with pytest.raises(ValidationError) as exc_info:
        CreditRiskRequest(
            annual_income=60000,
            monthly_debt=2000,
            credit_score=720,
            loan_amount=20000,
            loan_term_months=48,
            employment_length_years=5,
            home_ownership='MORTGAGE',
            purpose='debt_consolidation',
            number_of_open_accounts=3,
            delinquencies_2y=0,
            inquiries_6m=1,
            extra_field='should_fail'
        )
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert 'extra_field' in str(errors[0])
    print("✓ Extra fields correctly rejected")


def test_all_required_fields_present():
    """Test that all 11 required fields must be present."""
    # Should succeed with all fields
    req = CreditRiskRequest(
        annual_income=60000,
        monthly_debt=2000,
        credit_score=720,
        loan_amount=20000,
        loan_term_months=48,
        employment_length_years=5,
        home_ownership='MORTGAGE',
        purpose='debt_consolidation',
        number_of_open_accounts=3,
        delinquencies_2y=0,
        inquiries_6m=1
    )
    assert req is not None
    
    # Should fail without credit_score
    with pytest.raises(ValidationError):
        CreditRiskRequest(
            annual_income=60000,
            monthly_debt=2000,
            loan_amount=20000,
            loan_term_months=48,
            employment_length_years=5,
            home_ownership='MORTGAGE',
            purpose='debt_consolidation',
            number_of_open_accounts=3,
            delinquencies_2y=0,
            inquiries_6m=1
        )


def test_dti_auto_computed():
    """Test that debt_to_income_ratio is auto-computed if not provided."""
    req = CreditRiskRequest(
        annual_income=60000,
        monthly_debt=2000,
        credit_score=720,
        loan_amount=20000,
        loan_term_months=48,
        employment_length_years=5,
        home_ownership='MORTGAGE',
        purpose='debt_consolidation',
        number_of_open_accounts=3,
        delinquencies_2y=0,
        inquiries_6m=1
    )
    
    # monthly_income = 60000 / 12 = 5000
    # dti = (2000 / 5000) * 100 = 40.0
    assert req.compute_dti() == 40.0


def test_categorical_normalization():
    """Test that categorical fields are normalized."""
    req = CreditRiskRequest(
        annual_income=60000,
        monthly_debt=2000,
        credit_score=720,
        loan_amount=20000,
        loan_term_months=48,
        employment_length_years=5,
        home_ownership='mortgage',  # lowercase input
        purpose='DEBT_CONSOLIDATION',  # uppercase input
        number_of_open_accounts=3,
        delinquencies_2y=0,
        inquiries_6m=1
    )
    
    # home_ownership should be normalized to uppercase
    assert req.home_ownership == "MORTGAGE"
    
    # purpose should be normalized to lowercase
    assert req.purpose == "debt_consolidation"


def test_invalid_categorical_values():
    """Test that invalid categorical values are rejected."""
    # Invalid home_ownership
    with pytest.raises(ValidationError) as exc_info:
        CreditRiskRequest(
            annual_income=60000,
            monthly_debt=2000,
            credit_score=720,
            loan_amount=20000,
            loan_term_months=48,
            employment_length_years=5,
            home_ownership='INVALID',
            purpose='debt_consolidation',
            number_of_open_accounts=3,
            delinquencies_2y=0,
            inquiries_6m=1
        )
    assert 'home_ownership' in str(exc_info.value)
    
    # Invalid purpose
    with pytest.raises(ValidationError) as exc_info:
        CreditRiskRequest(
            annual_income=60000,
            monthly_debt=2000,
            credit_score=720,
            loan_amount=20000,
            loan_term_months=48,
            employment_length_years=5,
            home_ownership='MORTGAGE',
            purpose='invalid_purpose',
            number_of_open_accounts=3,
            delinquencies_2y=0,
            inquiries_6m=1
        )
    assert 'purpose' in str(exc_info.value)


def test_numeric_range_validation():
    """Test that numeric fields enforce range constraints."""
    # Credit score too low
    with pytest.raises(ValidationError):
        CreditRiskRequest(
            annual_income=60000,
            monthly_debt=2000,
            credit_score=250,  # Below 300
            loan_amount=20000,
            loan_term_months=48,
            employment_length_years=5,
            home_ownership='MORTGAGE',
            purpose='debt_consolidation',
            number_of_open_accounts=3,
            delinquencies_2y=0,
            inquiries_6m=1
        )
    
    # Loan amount must be positive
    with pytest.raises(ValidationError):
        CreditRiskRequest(
            annual_income=60000,
            monthly_debt=2000,
            credit_score=720,
            loan_amount=0,  # Must be > 0
            loan_term_months=48,
            employment_length_years=5,
            home_ownership='MORTGAGE',
            purpose='debt_consolidation',
            number_of_open_accounts=3,
            delinquencies_2y=0,
            inquiries_6m=1
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
