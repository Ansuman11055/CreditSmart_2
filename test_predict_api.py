"""Pytest tests for the prediction API endpoint.

These tests validate the /predict endpoint behavior with various inputs:
- Valid inputs produce successful predictions
- Missing features return 422 errors
- Extra features return 422 errors
- Wrong datatypes return 422 errors
- Model failures return graceful 500 errors

Tests use real model (no mocking) and run without frontend.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import math

from app.main import app
from app.ml.model import get_model


# TestClient for making API requests without running the server
client = TestClient(app)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def valid_request_payload():
    """Fixture providing a valid prediction request payload."""
    return {
        "annual_income": 60000.0,
        "monthly_debt": 2000.0,
        "credit_score": 720,
        "loan_amount": 20000.0,
        "loan_term_months": 48,
        "employment_length_years": 5.0,
        "home_ownership": "MORTGAGE",
        "purpose": "debt_consolidation",
        "number_of_open_accounts": 3,
        "delinquencies_2y": 0,
        "inquiries_6m": 1
    }


@pytest.fixture
def low_risk_payload():
    """Fixture for low-risk applicant."""
    return {
        "annual_income": 100000.0,
        "monthly_debt": 1500.0,
        "credit_score": 780,
        "loan_amount": 15000.0,
        "loan_term_months": 36,
        "employment_length_years": 10.0,
        "home_ownership": "OWN",
        "purpose": "home_improvement",
        "number_of_open_accounts": 2,
        "delinquencies_2y": 0,
        "inquiries_6m": 0
    }


@pytest.fixture
def high_risk_payload():
    """Fixture for high-risk applicant."""
    return {
        "annual_income": 30000.0,
        "monthly_debt": 2500.0,
        "credit_score": 580,
        "loan_amount": 25000.0,
        "loan_term_months": 72,
        "employment_length_years": 1.0,
        "home_ownership": "RENT",
        "purpose": "other",
        "number_of_open_accounts": 10,
        "delinquencies_2y": 3,
        "inquiries_6m": 4
    }


# ============================================================================
# TEST: VALID INPUTS
# ============================================================================

def test_predict_valid_request(valid_request_payload):
    """Test successful prediction with valid input."""
    response = client.post("/api/v1/predict", json=valid_request_payload)
    
    # Assert successful response
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    # Parse response
    data = response.json()
    
    # Validate response structure
    assert "risk_score" in data, "Missing risk_score in response"
    assert "risk_level" in data, "Missing risk_level in response"
    assert "recommended_action" in data, "Missing recommended_action in response"
    assert "explanation" in data, "Missing explanation in response"
    assert "model_version" in data, "Missing model_version in response"
    
    # Validate risk_score range [0, 1]
    assert 0.0 <= data["risk_score"] <= 1.0, f"Risk score {data['risk_score']} out of valid range [0, 1]"
    
    # Validate risk_level is valid enum
    valid_risk_levels = ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
    assert data["risk_level"] in valid_risk_levels, f"Invalid risk level: {data['risk_level']}"
    
    # Validate recommended_action is valid enum
    valid_actions = ["APPROVE", "REVIEW", "REJECT"]
    assert data["recommended_action"] in valid_actions, f"Invalid action: {data['recommended_action']}"
    
    # Validate explanation is non-empty string
    assert isinstance(data["explanation"], str), "Explanation must be string"
    assert len(data["explanation"]) > 0, "Explanation cannot be empty"
    
    # Validate no NaN or infinite values
    assert not math.isnan(data["risk_score"]), "Risk score is NaN"
    assert not math.isinf(data["risk_score"]), "Risk score is infinite"


def test_predict_low_risk_applicant(low_risk_payload):
    """Test prediction for low-risk applicant."""
    response = client.post("/api/v1/predict", json=low_risk_payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Low risk applicant should have lower risk score
    # (Note: specific threshold depends on model, but should be < 0.5)
    assert 0.0 <= data["risk_score"] <= 1.0, "Risk score out of range"
    
    # Should not be VERY_HIGH risk
    assert data["risk_level"] != "VERY_HIGH", "Low-risk applicant classified as VERY_HIGH"


def test_predict_high_risk_applicant(high_risk_payload):
    """Test prediction for high-risk applicant."""
    response = client.post("/api/v1/predict", json=high_risk_payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # High risk applicant should have higher risk score
    assert 0.0 <= data["risk_score"] <= 1.0, "Risk score out of range"
    
    # Should not be LOW risk (given the poor credit profile)
    assert data["risk_level"] != "LOW", "High-risk applicant classified as LOW"


def test_predict_multiple_requests(valid_request_payload):
    """Test multiple consecutive predictions (idempotency)."""
    results = []
    
    for _ in range(3):
        response = client.post("/api/v1/predict", json=valid_request_payload)
        assert response.status_code == 200
        results.append(response.json()["risk_score"])
    
    # All predictions should be identical (same input → same output)
    assert all(score == results[0] for score in results), "Predictions are not consistent"


# ============================================================================
# TEST: MISSING FEATURES (422 ERRORS)
# ============================================================================

def test_predict_missing_single_field(valid_request_payload):
    """Test prediction with single missing required field."""
    required_fields = [
        "annual_income", "monthly_debt", "credit_score", "loan_amount",
        "loan_term_months", "employment_length_years", "home_ownership",
        "purpose", "number_of_open_accounts", "delinquencies_2y", "inquiries_6m"
    ]
    
    for field in required_fields:
        # Create payload missing one field
        incomplete_payload = valid_request_payload.copy()
        del incomplete_payload[field]
        
        response = client.post("/api/v1/predict", json=incomplete_payload)
        
        # Should return 422 Unprocessable Entity
        assert response.status_code == 422, f"Missing {field} should return 422, got {response.status_code}"
        
        # Validate error structure
        error_data = response.json()
        assert "detail" in error_data, "Error response missing 'detail'"
        
        # Error should mention the missing field
        error_str = str(error_data["detail"]).lower()
        assert field.lower() in error_str or "required" in error_str, \
            f"Error for missing {field} should mention the field or 'required'"


def test_predict_missing_multiple_fields(valid_request_payload):
    """Test prediction with multiple missing fields."""
    incomplete_payload = {
        "credit_score": 700,
        "loan_amount": 15000.0
    }
    
    response = client.post("/api/v1/predict", json=incomplete_payload)
    
    assert response.status_code == 422, f"Multiple missing fields should return 422, got {response.status_code}"
    
    error_data = response.json()
    assert "detail" in error_data


def test_predict_empty_payload():
    """Test prediction with completely empty payload."""
    response = client.post("/api/v1/predict", json={})
    
    assert response.status_code == 422, f"Empty payload should return 422, got {response.status_code}"


# ============================================================================
# TEST: EXTRA FEATURES (422 ERRORS)
# ============================================================================

def test_predict_extra_field(valid_request_payload):
    """Test prediction with extra field (schema forbids extra fields)."""
    payload_with_extra = valid_request_payload.copy()
    payload_with_extra["extra_field"] = "unexpected_value"
    
    response = client.post("/api/v1/predict", json=payload_with_extra)
    
    # Should return 422 due to extra='forbid' in Pydantic schema
    assert response.status_code == 422, f"Extra field should return 422, got {response.status_code}"
    
    error_data = response.json()
    assert "detail" in error_data
    
    # Error should mention extra field or forbidden
    error_str = str(error_data["detail"]).lower()
    assert "extra" in error_str or "forbidden" in error_str or "not permitted" in error_str, \
        "Error should indicate extra fields are not allowed"


def test_predict_multiple_extra_fields(valid_request_payload):
    """Test prediction with multiple extra fields."""
    payload_with_extras = valid_request_payload.copy()
    payload_with_extras["extra_field_1"] = "value1"
    payload_with_extras["extra_field_2"] = 123
    payload_with_extras["extra_field_3"] = True
    
    response = client.post("/api/v1/predict", json=payload_with_extras)
    
    assert response.status_code == 422, f"Multiple extra fields should return 422, got {response.status_code}"


# ============================================================================
# TEST: WRONG DATATYPES (422 ERRORS)
# ============================================================================

def test_predict_wrong_datatype_string_as_number(valid_request_payload):
    """Test prediction with string value for numeric field."""
    invalid_payload = valid_request_payload.copy()
    invalid_payload["credit_score"] = "seven hundred"  # String instead of int
    
    response = client.post("/api/v1/predict", json=invalid_payload)
    
    assert response.status_code == 422, f"String for numeric field should return 422, got {response.status_code}"
    
    error_data = response.json()
    assert "detail" in error_data


def test_predict_wrong_datatype_number_as_string(valid_request_payload):
    """Test prediction with numeric value for string field."""
    invalid_payload = valid_request_payload.copy()
    invalid_payload["home_ownership"] = 12345  # Number instead of string
    
    response = client.post("/api/v1/predict", json=invalid_payload)
    
    assert response.status_code == 422, f"Number for string field should return 422, got {response.status_code}"


def test_predict_wrong_datatype_boolean(valid_request_payload):
    """Test prediction with boolean for numeric field.
    
    Note: Pydantic may coerce True->1.0, False->0.0 for numeric fields.
    This tests that the request is either rejected (422) or coerced successfully (200).
    """
    invalid_payload = valid_request_payload.copy()
    invalid_payload["annual_income"] = True  # Boolean instead of float
    
    response = client.post("/api/v1/predict", json=invalid_payload)
    
    # Pydantic may coerce boolean to number (True->1, False->0)
    # Either 422 (strict validation) or 200 (coercion) is acceptable
    # But if 200, the value should be coerced to 1.0
    if response.status_code == 200:
        # Coercion happened - verify it worked
        assert response.json()["risk_score"] >= 0.0, "Coerced boolean produced invalid result"
    else:
        # Strict validation rejected it
        assert response.status_code == 422, f"Expected 422 or 200 (coercion), got {response.status_code}"


def test_predict_wrong_datatype_null(valid_request_payload):
    """Test prediction with null/None value."""
    invalid_payload = valid_request_payload.copy()
    invalid_payload["loan_amount"] = None  # Null instead of float
    
    response = client.post("/api/v1/predict", json=invalid_payload)
    
    assert response.status_code == 422, f"Null value should return 422, got {response.status_code}"


def test_predict_wrong_datatype_array(valid_request_payload):
    """Test prediction with array for scalar field."""
    invalid_payload = valid_request_payload.copy()
    invalid_payload["credit_score"] = [700, 720]  # Array instead of int
    
    response = client.post("/api/v1/predict", json=invalid_payload)
    
    assert response.status_code == 422, f"Array for scalar field should return 422, got {response.status_code}"


# ============================================================================
# TEST: INVALID VALUES (422 ERRORS)
# ============================================================================

def test_predict_negative_income(valid_request_payload):
    """Test prediction with negative annual income."""
    invalid_payload = valid_request_payload.copy()
    invalid_payload["annual_income"] = -50000.0
    
    response = client.post("/api/v1/predict", json=invalid_payload)
    
    # Schema validation should reject negative income
    assert response.status_code == 422, f"Negative income should return 422, got {response.status_code}"


def test_predict_credit_score_out_of_range(valid_request_payload):
    """Test prediction with credit score outside valid range [300, 850]."""
    # Test too low
    invalid_payload_low = valid_request_payload.copy()
    invalid_payload_low["credit_score"] = 250
    
    response_low = client.post("/api/v1/predict", json=invalid_payload_low)
    assert response_low.status_code == 422, "Credit score < 300 should return 422"
    
    # Test too high
    invalid_payload_high = valid_request_payload.copy()
    invalid_payload_high["credit_score"] = 900
    
    response_high = client.post("/api/v1/predict", json=invalid_payload_high)
    assert response_high.status_code == 422, "Credit score > 850 should return 422"


def test_predict_invalid_home_ownership(valid_request_payload):
    """Test prediction with invalid home_ownership enum value."""
    invalid_payload = valid_request_payload.copy()
    invalid_payload["home_ownership"] = "INVALID_VALUE"
    
    response = client.post("/api/v1/predict", json=invalid_payload)
    
    assert response.status_code == 422, f"Invalid enum should return 422, got {response.status_code}"


def test_predict_invalid_purpose(valid_request_payload):
    """Test prediction with invalid purpose enum value."""
    invalid_payload = valid_request_payload.copy()
    invalid_payload["purpose"] = "buy_spaceship"
    
    response = client.post("/api/v1/predict", json=invalid_payload)
    
    assert response.status_code == 422, f"Invalid purpose should return 422, got {response.status_code}"


# ============================================================================
# TEST: MODEL LOADING FAILURE (500 ERRORS)
# ============================================================================

def test_predict_model_not_loaded():
    """Test graceful 500 error when model fails to load."""
    # Mock the model to raise RuntimeError (simulating model not loaded)
    with patch('app.ml.model.CreditRiskModel.predict') as mock_predict:
        mock_predict.side_effect = RuntimeError("Model not loaded")
        
        valid_payload = {
            "annual_income": 60000.0,
            "monthly_debt": 2000.0,
            "credit_score": 720,
            "loan_amount": 20000.0,
            "loan_term_months": 48,
            "employment_length_years": 5.0,
            "home_ownership": "MORTGAGE",
            "purpose": "debt_consolidation",
            "number_of_open_accounts": 3,
            "delinquencies_2y": 0,
            "inquiries_6m": 1
        }
        
        response = client.post("/api/v1/predict", json=valid_payload)
        
        # Should return 500 Internal Server Error (gracefully handled)
        assert response.status_code == 500, f"Model error should return 500, got {response.status_code}"
        
        # Should have error detail
        error_data = response.json()
        assert "detail" in error_data, "Error response should have 'detail' field"
        
        # Should NOT expose internal error details (security)
        detail = error_data["detail"].lower()
        assert "not available" in detail or "error" in detail or "try again" in detail, \
            "Error message should be generic"


def test_predict_model_prediction_failure():
    """Test graceful 500 error when model prediction fails."""
    # Mock the model to raise unexpected exception
    with patch('app.ml.model.CreditRiskModel.predict') as mock_predict:
        mock_predict.side_effect = Exception("Unexpected model error")
        
        valid_payload = {
            "annual_income": 60000.0,
            "monthly_debt": 2000.0,
            "credit_score": 720,
            "loan_amount": 20000.0,
            "loan_term_months": 48,
            "employment_length_years": 5.0,
            "home_ownership": "MORTGAGE",
            "purpose": "debt_consolidation",
            "number_of_open_accounts": 3,
            "delinquencies_2y": 0,
            "inquiries_6m": 1
        }
        
        response = client.post("/api/v1/predict", json=valid_payload)
        
        # Should return 500 (gracefully handled)
        assert response.status_code == 500, f"Unexpected error should return 500, got {response.status_code}"
        
        # Should have generic error message
        error_data = response.json()
        assert "detail" in error_data


# ============================================================================
# TEST: EDGE CASES
# ============================================================================

def test_predict_zero_values(valid_request_payload):
    """Test prediction with zero values for optional metrics."""
    payload = valid_request_payload.copy()
    payload["delinquencies_2y"] = 0
    payload["inquiries_6m"] = 0
    payload["number_of_open_accounts"] = 0
    
    response = client.post("/api/v1/predict", json=payload)
    
    # Should still work (zeros are valid)
    assert response.status_code == 200, f"Zero values should be valid, got {response.status_code}"


def test_predict_maximum_values(valid_request_payload):
    """Test prediction with maximum valid values."""
    payload = valid_request_payload.copy()
    payload["credit_score"] = 850  # Maximum credit score
    payload["annual_income"] = 10000000.0  # High income
    
    response = client.post("/api/v1/predict", json=payload)
    
    # Should work with maximum valid values
    assert response.status_code == 200, f"Maximum values should be valid, got {response.status_code}"


def test_predict_minimum_values(valid_request_payload):
    """Test prediction with minimum valid values."""
    payload = valid_request_payload.copy()
    payload["credit_score"] = 300  # Minimum credit score
    payload["annual_income"] = 0.01  # Very low income (but > 0)
    payload["loan_amount"] = 0.01  # Minimum loan
    
    response = client.post("/api/v1/predict", json=payload)
    
    # Should work with minimum valid values
    assert response.status_code == 200, f"Minimum values should be valid, got {response.status_code}"


def test_predict_very_high_dti():
    """Test prediction with very high debt-to-income ratio."""
    payload = {
        "annual_income": 20000.0,
        "monthly_debt": 5000.0,  # DTI = 300% (extremely high)
        "credit_score": 600,
        "loan_amount": 10000.0,
        "loan_term_months": 36,
        "employment_length_years": 2.0,
        "home_ownership": "RENT",
        "purpose": "debt_consolidation",
        "number_of_open_accounts": 5,
        "delinquencies_2y": 1,
        "inquiries_6m": 2
    }
    
    response = client.post("/api/v1/predict", json=payload)
    
    # Should work (high DTI is valid, just risky)
    assert response.status_code == 200
    
    # Should be classified as high risk
    data = response.json()
    assert data["risk_level"] in ["HIGH", "VERY_HIGH"], "Very high DTI should result in high risk"


# ============================================================================
# TEST: RESPONSE FORMAT
# ============================================================================

def test_predict_response_json_format(valid_request_payload):
    """Test that response is valid JSON with correct Content-Type."""
    response = client.post("/api/v1/predict", json=valid_request_payload)
    
    assert response.status_code == 200
    
    # Verify Content-Type
    assert "application/json" in response.headers.get("content-type", ""), \
        "Response should be JSON"
    
    # Verify response can be parsed as JSON
    data = response.json()
    assert isinstance(data, dict), "Response should be a JSON object"


def test_predict_response_fields_types(valid_request_payload):
    """Test that response fields have correct data types."""
    response = client.post("/api/v1/predict", json=valid_request_payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check field types
    assert isinstance(data["risk_score"], float), "risk_score should be float"
    assert isinstance(data["risk_level"], str), "risk_level should be string"
    assert isinstance(data["recommended_action"], str), "recommended_action should be string"
    assert isinstance(data["explanation"], str), "explanation should be string"
    assert isinstance(data["model_version"], str), "model_version should be string"


# ============================================================================
# SUMMARY
# ============================================================================

if __name__ == "__main__":
    # Run pytest programmatically
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
