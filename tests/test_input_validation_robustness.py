"""
Comprehensive tests for ML input validation robustness.

Tests verify:
- NaN/Inf values are rejected for all float fields
- Empty strings are rejected for categorical fields
- Invalid enum values fail fast with clear errors
- All validations include helpful error messages
- No silent coercion or frontend assumptions

Phase: Validation Hardening
Date: 2026-02-01
"""
import math
import pytest
from pydantic import ValidationError
from app.schemas.request import CreditRiskRequest
from app.schemas.response import CreditRiskResponse, RiskLevel, RecommendedAction
from app.schemas.advisor import FinancialAdvice, AdvisorResponse


class TestCreditRiskRequestRobustness:
    """Test CreditRiskRequest validation robustness."""
    
    def get_valid_request_data(self):
        """Return valid request data for testing."""
        return {
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
    
    # ═══════════════════════════════════════════════════════════════════════
    # NaN/Inf VALIDATION TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_annual_income_rejects_nan(self):
        """Test annual_income rejects NaN values."""
        data = self.get_valid_request_data()
        data["annual_income"] = float("nan")
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        assert "NaN" in error or "nan" in error.lower()
        assert "annual_income" in error.lower()
    
    def test_annual_income_rejects_inf(self):
        """Test annual_income rejects Infinity values."""
        data = self.get_valid_request_data()
        data["annual_income"] = float("inf")
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        assert "inf" in error.lower()
        assert "annual_income" in error.lower()
    
    def test_monthly_debt_rejects_nan(self):
        """Test monthly_debt rejects NaN values."""
        data = self.get_valid_request_data()
        data["monthly_debt"] = float("nan")
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        assert "nan" in error.lower()
        assert "monthly_debt" in error.lower()
    
    def test_loan_amount_rejects_inf(self):
        """Test loan_amount rejects Infinity values."""
        data = self.get_valid_request_data()
        data["loan_amount"] = float("inf")
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        assert "inf" in error.lower()
        assert "loan_amount" in error.lower()
    
    def test_employment_length_rejects_nan(self):
        """Test employment_length_years rejects NaN values."""
        data = self.get_valid_request_data()
        data["employment_length_years"] = float("nan")
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        assert "nan" in error.lower()
        assert "employment" in error.lower()
    
    def test_dti_ratio_rejects_nan(self):
        """Test debt_to_income_ratio rejects NaN values."""
        data = self.get_valid_request_data()
        data["debt_to_income_ratio"] = float("nan")
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        assert "nan" in error.lower()
    
    # ═══════════════════════════════════════════════════════════════════════
    # EMPTY STRING VALIDATION TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_home_ownership_rejects_empty_string(self):
        """Test home_ownership rejects empty strings."""
        data = self.get_valid_request_data()
        data["home_ownership"] = ""
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        assert "empty" in error.lower()
        assert "home_ownership" in error.lower()
    
    def test_home_ownership_rejects_whitespace_only(self):
        """Test home_ownership rejects whitespace-only strings."""
        data = self.get_valid_request_data()
        data["home_ownership"] = "   "
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        assert "empty" in error.lower() or "cannot be empty" in error.lower()
    
    def test_purpose_rejects_empty_string(self):
        """Test purpose rejects empty strings."""
        data = self.get_valid_request_data()
        data["purpose"] = ""
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        assert "empty" in error.lower()
        assert "purpose" in error.lower()
    
    # ═══════════════════════════════════════════════════════════════════════
    # INVALID ENUM VALIDATION TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_home_ownership_rejects_invalid_value(self):
        """Test home_ownership rejects invalid enum values."""
        data = self.get_valid_request_data()
        data["home_ownership"] = "RENTING"  # Typo: should be RENT
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        assert "RENT" in error or "OWN" in error or "MORTGAGE" in error
        assert "home_ownership" in error.lower()
    
    def test_purpose_rejects_invalid_value(self):
        """Test purpose rejects invalid enum values."""
        data = self.get_valid_request_data()
        data["purpose"] = "consolidation"  # Typo: should be debt_consolidation
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        assert "purpose" in error.lower()
        assert "consolidation" in error.lower()
    
    # ═══════════════════════════════════════════════════════════════════════
    # BOUNDARY VALIDATION TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_credit_score_below_minimum(self):
        """Test credit_score rejects values below 300."""
        data = self.get_valid_request_data()
        data["credit_score"] = 299
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        # Accept either Pydantic ge/le or custom validator message
        assert ("300" in error or "greater than or equal" in error.lower())
        assert "credit_score" in error.lower()
    
    def test_credit_score_above_maximum(self):
        """Test credit_score rejects values above 850."""
        data = self.get_valid_request_data()
        data["credit_score"] = 851
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        # Accept either Pydantic ge/le or custom validator message
        assert ("850" in error or "less than or equal" in error.lower())
        assert "credit_score" in error.lower()
    
    def test_loan_amount_zero_rejected(self):
        """Test loan_amount rejects zero (must be positive)."""
        data = self.get_valid_request_data()
        data["loan_amount"] = 0
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        # Accept either Pydantic gt or custom validator message
        assert ("positive" in error.lower() or "greater than 0" in error.lower())
        assert "loan_amount" in error.lower()
    
    def test_loan_amount_negative_rejected(self):
        """Test loan_amount rejects negative values."""
        data = self.get_valid_request_data()
        data["loan_amount"] = -1000
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        # Accept either Pydantic gt, custom validator, or "greater than 0" message
        assert ("positive" in error.lower() or "cannot be negative" in error.lower() or "greater than 0" in error.lower())
        assert "loan_amount" in error.lower()
    
    def test_annual_income_negative_rejected(self):
        """Test annual_income rejects negative values."""
        data = self.get_valid_request_data()
        data["annual_income"] = -50000
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        # Accept either Pydantic ge, custom validator, or "greater than or equal" message
        assert ("negative" in error.lower() or "greater than or equal" in error.lower())
        assert "annual_income" in error.lower()
    
    # ═══════════════════════════════════════════════════════════════════════
    # ERROR MESSAGE CLARITY TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_error_messages_include_field_names(self):
        """Test error messages include the field name."""
        data = self.get_valid_request_data()
        data["credit_score"] = 900
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        assert "credit_score" in error.lower()
    
    def test_error_messages_include_allowed_values(self):
        """Test enum error messages include allowed values."""
        data = self.get_valid_request_data()
        data["home_ownership"] = "INVALID"
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(**data)
        
        error = str(exc_info.value)
        # Should mention at least one allowed value
        assert "RENT" in error or "OWN" in error or "MORTGAGE" in error
    
    # ═══════════════════════════════════════════════════════════════════════
    # VALID INPUT ACCEPTANCE TESTS
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_valid_request_accepted(self):
        """Test valid request is accepted."""
        data = self.get_valid_request_data()
        request = CreditRiskRequest(**data)
        
        assert request.annual_income == 75000
        assert request.credit_score == 720
        assert request.home_ownership == "MORTGAGE"
        assert request.purpose == "debt_consolidation"
    
    def test_zero_annual_income_accepted(self):
        """Test zero annual_income is accepted (unemployed case)."""
        data = self.get_valid_request_data()
        data["annual_income"] = 0
        
        request = CreditRiskRequest(**data)
        assert request.annual_income == 0
    
    def test_case_insensitive_home_ownership(self):
        """Test home_ownership is case-insensitive."""
        data = self.get_valid_request_data()
        data["home_ownership"] = "rent"  # lowercase
        
        request = CreditRiskRequest(**data)
        assert request.home_ownership == "RENT"  # normalized to uppercase
    
    def test_case_insensitive_purpose(self):
        """Test purpose is case-insensitive."""
        data = self.get_valid_request_data()
        data["purpose"] = "DEBT_CONSOLIDATION"  # uppercase
        
        request = CreditRiskRequest(**data)
        assert request.purpose == "debt_consolidation"  # normalized to lowercase


class TestCreditRiskResponseRobustness:
    """Test CreditRiskResponse validation robustness."""
    
    def get_valid_response_data(self):
        """Return valid response data for testing."""
        return {
            "schema_version": "v1",
            "risk_score": 0.15,
            "risk_level": "LOW",
            "recommended_action": "APPROVE",
            "model_version": "ml_v1.0.0",
            "prediction_probability": 0.15,
            "confidence_level": "HIGH",
        }
    
    def test_risk_score_rejects_nan(self):
        """Test risk_score rejects NaN values."""
        data = self.get_valid_response_data()
        data["risk_score"] = float("nan")
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(**data)
        
        error = str(exc_info.value)
        assert "nan" in error.lower()
    
    def test_risk_score_rejects_inf(self):
        """Test risk_score rejects Infinity values."""
        data = self.get_valid_response_data()
        data["risk_score"] = float("inf")
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(**data)
        
        error = str(exc_info.value)
        assert "inf" in error.lower()
    
    def test_risk_score_rejects_negative(self):
        """Test risk_score rejects negative values."""
        data = self.get_valid_response_data()
        data["risk_score"] = -0.1
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(**data)
        
        error = str(exc_info.value)
        # Accept either Pydantic ge/le or custom validator message
        assert ("0.0" in error or "0" in error) or "greater than or equal" in error.lower()
    
    def test_risk_score_rejects_above_one(self):
        """Test risk_score rejects values > 1.0."""
        data = self.get_valid_response_data()
        data["risk_score"] = 1.5
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(**data)
        
        error = str(exc_info.value)
        assert "1.0" in error or "1" in error
    
    def test_confidence_level_rejects_empty(self):
        """Test confidence_level rejects empty strings."""
        data = self.get_valid_response_data()
        data["confidence_level"] = ""
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(**data)
        
        error = str(exc_info.value)
        assert "empty" in error.lower()
        assert "confidence" in error.lower()
    
    def test_confidence_level_rejects_invalid(self):
        """Test confidence_level rejects invalid values."""
        data = self.get_valid_response_data()
        data["confidence_level"] = "VERY_HIGH"
        
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(**data)
        
        error = str(exc_info.value)
        assert "HIGH" in error or "MEDIUM" in error or "LOW" in error
    
    def test_valid_response_accepted(self):
        """Test valid response is accepted."""
        data = self.get_valid_response_data()
        response = CreditRiskResponse(**data)
        
        assert response.risk_score == 0.15
        assert response.risk_level == RiskLevel.LOW
        assert response.recommended_action == RecommendedAction.APPROVE


class TestAdvisorResponseRobustness:
    """Test AdvisorResponse validation robustness."""
    
    def get_valid_advice_data(self):
        """Return valid financial advice data."""
        return {
            "category": "credit_score",
            "priority": "HIGH",
            "suggestion": "Pay down credit card balances",
            "expected_impact": "Could reduce risk by 15-20 points",
            "timeframe": "3-6 months",
        }
    
    def get_valid_response_data(self):
        """Return valid advisor response data."""
        return {
            "overall_assessment": "Good financial position",
            "current_risk_score": 0.45,
            "potential_risk_score": 0.25,
            "recommendations": [self.get_valid_advice_data()],
            "strengths": ["Clean payment history"],
        }
    
    def test_current_risk_score_rejects_nan(self):
        """Test current_risk_score rejects NaN."""
        data = self.get_valid_response_data()
        data["current_risk_score"] = float("nan")
        
        with pytest.raises(ValidationError) as exc_info:
            AdvisorResponse(**data)
        
        error = str(exc_info.value)
        assert "nan" in error.lower()
    
    def test_potential_risk_score_rejects_inf(self):
        """Test potential_risk_score rejects Infinity."""
        data = self.get_valid_response_data()
        data["potential_risk_score"] = float("inf")
        
        with pytest.raises(ValidationError) as exc_info:
            AdvisorResponse(**data)
        
        error = str(exc_info.value)
        assert "inf" in error.lower()
    
    def test_advice_category_rejects_empty(self):
        """Test FinancialAdvice category rejects empty strings."""
        data = self.get_valid_advice_data()
        data["category"] = ""
        
        with pytest.raises(ValidationError) as exc_info:
            FinancialAdvice(**data)
        
        error = str(exc_info.value)
        assert "empty" in error.lower()
        assert "category" in error.lower()
    
    def test_advice_category_rejects_invalid(self):
        """Test FinancialAdvice category rejects invalid values."""
        data = self.get_valid_advice_data()
        data["category"] = "invalid_category"
        
        with pytest.raises(ValidationError) as exc_info:
            FinancialAdvice(**data)
        
        error = str(exc_info.value)
        assert "credit_score" in error or "debt_management" in error
    
    def test_advice_priority_rejects_invalid(self):
        """Test FinancialAdvice priority rejects invalid values."""
        data = self.get_valid_advice_data()
        data["priority"] = "URGENT"  # Invalid: must be HIGH, MEDIUM, or LOW
        
        with pytest.raises(ValidationError) as exc_info:
            FinancialAdvice(**data)
        
        error = str(exc_info.value)
        assert "HIGH" in error or "MEDIUM" in error or "LOW" in error
    
    def test_overall_assessment_rejects_empty(self):
        """Test overall_assessment rejects empty strings."""
        data = self.get_valid_response_data()
        data["overall_assessment"] = ""
        
        with pytest.raises(ValidationError) as exc_info:
            AdvisorResponse(**data)
        
        error = str(exc_info.value)
        assert "empty" in error.lower()
    
    def test_empty_recommendations_rejected(self):
        """Test recommendations list cannot be empty."""
        data = self.get_valid_response_data()
        data["recommendations"] = []
        
        with pytest.raises(ValidationError) as exc_info:
            AdvisorResponse(**data)
        
        error = str(exc_info.value)
        assert "recommendation" in error.lower()
    
    def test_valid_advisor_response_accepted(self):
        """Test valid advisor response is accepted."""
        data = self.get_valid_response_data()
        response = AdvisorResponse(**data)
        
        assert response.current_risk_score == 0.45
        assert response.potential_risk_score == 0.25
        assert len(response.recommendations) == 1
        assert response.recommendations[0].category == "credit_score"


class TestEmptyPayloadRejection:
    """Test that empty or missing payloads are rejected."""
    
    def test_empty_request_rejected(self):
        """Test completely empty request is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest()
        
        # Should fail on missing required fields
        error = str(exc_info.value)
        assert "required" in error.lower() or "missing" in error.lower()
    
    def test_partial_request_rejected(self):
        """Test partially filled request is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskRequest(
                annual_income=75000,
                credit_score=720
                # Missing other required fields
            )
        
        error = str(exc_info.value)
        assert "required" in error.lower() or "missing" in error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
