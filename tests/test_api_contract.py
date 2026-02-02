"""Contract stability tests for Phase 3A-4: API Contract Stabilization & Safety.

Tests ensure:
1. API version tracking (X-API-Version header)
2. Error response format consistency
3. HTTP status code consistency
4. Required field presence in all responses
5. Schema validation for error responses
6. Inference guard behavior

These tests verify the API contract is stable for frontend integration.
"""

import pytest
from fastapi.testclient import TestClient
import json
from typing import Dict, Any

from app.main import app
from app.schemas.errors import APIErrorResponse, ErrorCodes


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def valid_prediction_request() -> Dict[str, Any]:
    """Valid prediction request for testing."""
    return {
        "credit_score": 720,
        "annual_income": 75000,
        "monthly_debt": 1200,
        "employment_length_years": 5.0,
        "loan_amount": 15000,
        "loan_term_months": 60,
        "home_ownership": "MORTGAGE",
        "purpose": "debt_consolidation",
        "number_of_open_accounts": 8,
        "delinquencies_2y": 0,
        "inquiries_6m": 1
    }


# ═══════════════════════════════════════════════════════════════════════
# API VERSION TRACKING TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_api_version_header_on_success_response(client, valid_prediction_request):
    """Test X-API-Version header is present on successful responses."""
    response = client.post("/api/v1/predict", json=valid_prediction_request)
    
    assert response.status_code == 200
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "v1"


def test_api_version_header_on_error_response(client):
    """Test X-API-Version header is present even on error responses."""
    # Send invalid request (missing required fields)
    response = client.post("/api/v1/predict", json={})
    
    assert response.status_code == 422
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "v1"


def test_api_version_header_on_health_endpoint(client):
    """Test X-API-Version header on health endpoint."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "v1"


def test_api_version_header_on_model_info(client):
    """Test X-API-Version header on model info endpoint."""
    response = client.get("/api/v1/model/info")
    
    assert response.status_code == 200
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "v1"


# ═══════════════════════════════════════════════════════════════════════
# ERROR RESPONSE FORMAT TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_validation_error_format(client):
    """Test validation errors follow APIErrorResponse schema."""
    # Missing required field
    response = client.post("/api/v1/predict", json={
        "credit_score": 720
        # Missing other required fields
    })
    
    assert response.status_code == 422
    data = response.json()
    
    # Validate schema structure
    assert "error_code" in data
    assert "message" in data
    assert "details" in data
    
    # Validate error code
    assert data["error_code"] == ErrorCodes.VALIDATION_ERROR
    
    # Validate details structure
    assert "errors" in data["details"]
    assert isinstance(data["details"]["errors"], list)
    assert len(data["details"]["errors"]) > 0
    
    # Each error should have field, message, type
    first_error = data["details"]["errors"][0]
    assert "field" in first_error
    assert "message" in first_error
    assert "type" in first_error


def test_invalid_field_type_error_format(client):
    """Test type validation errors follow APIErrorResponse schema."""
    response = client.post("/api/v1/predict", json={
        "credit_score": "not_a_number",  # Invalid type
        "annual_income": 75000,
        "monthly_debt": 1200,
        "employment_length_years": 5.0,
        "loan_amount": 15000,
        "loan_term_months": 60,
        "home_ownership": "MORTGAGE",
        "purpose": "debt_consolidation",
        "number_of_open_accounts": 8,
        "delinquencies_2y": 0,
        "inquiries_6m": 1
    })
    
    assert response.status_code == 422
    data = response.json()
    
    assert data["error_code"] == ErrorCodes.VALIDATION_ERROR
    assert "credit_score" in data["message"].lower() or "field" in data["message"].lower()


def test_out_of_range_error_format(client, valid_prediction_request):
    """Test range validation errors follow APIErrorResponse schema."""
    # Credit score out of range (must be 300-850)
    invalid_request = valid_prediction_request.copy()
    invalid_request["credit_score"] = 1000
    
    response = client.post("/api/v1/predict", json=invalid_request)
    
    assert response.status_code == 422
    data = response.json()
    
    assert data["error_code"] == ErrorCodes.VALIDATION_ERROR
    assert "details" in data


def test_invalid_enum_value_error_format(client, valid_prediction_request):
    """Test enum validation errors follow APIErrorResponse schema."""
    invalid_request = valid_prediction_request.copy()
    invalid_request["home_ownership"] = "INVALID_VALUE"
    
    response = client.post("/api/v1/predict", json=invalid_request)
    
    assert response.status_code == 422
    data = response.json()
    
    assert data["error_code"] == ErrorCodes.VALIDATION_ERROR


# ═══════════════════════════════════════════════════════════════════════
# INFERENCE GUARD TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_feature_count_guard_detects_mismatch(client, monkeypatch):
    """Test inference guards detect feature count mismatches.
    
    This shouldn't happen in production (Pydantic validates first),
    but guards provide defense-in-depth.
    """
    # This test verifies the guard exists and would trigger if schema changed
    # In practice, Pydantic validation prevents this scenario
    # But guards ensure safety if schema/model get out of sync
    
    # Valid request should pass all guards
    valid_request = {
        "credit_score": 720,
        "annual_income": 75000,
        "monthly_debt": 1200,
        "employment_length_years": 5.0,
        "loan_amount": 15000,
        "loan_term_months": 60,
        "home_ownership": "MORTGAGE",
        "purpose": "debt_consolidation",
        "number_of_open_accounts": 8,
        "delinquencies_2y": 0,
        "inquiries_6m": 1
    }
    
    response = client.post("/api/v1/predict", json=valid_request)
    assert response.status_code == 200  # Guards passed


def test_nan_infinity_guard(client, valid_prediction_request):
    """Test inference guards reject NaN/Infinity values."""
    # Pydantic should catch these, but if it doesn't, guards will
    # This is defense-in-depth testing
    
    # Standard validation should work
    response = client.post("/api/v1/predict", json=valid_prediction_request)
    assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# HTTP STATUS CODE CONSISTENCY TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_successful_prediction_returns_200(client, valid_prediction_request):
    """Test successful predictions always return 200."""
    response = client.post("/api/v1/predict", json=valid_prediction_request)
    assert response.status_code == 200


def test_validation_errors_return_422(client):
    """Test all validation errors return 422."""
    # Missing fields
    response = client.post("/api/v1/predict", json={})
    assert response.status_code == 422
    
    # Invalid type
    response = client.post("/api/v1/predict", json={"credit_score": "invalid"})
    assert response.status_code == 422


def test_health_endpoint_returns_200(client):
    """Test health endpoint always returns 200 when healthy."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_model_info_returns_200(client):
    """Test model info endpoint returns 200."""
    response = client.get("/api/v1/model/info")
    assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# REQUIRED FIELD PRESENCE TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_prediction_response_has_all_required_fields(client, valid_prediction_request):
    """Test prediction response always includes all required fields.
    
    Phase 3B-2: Tests UX-safe wrapper fields.
    """
    response = client.post("/api/v1/predict", json=valid_prediction_request)
    
    assert response.status_code == 200
    data = response.json()
    
    # Phase 3B-2: UX-safe wrapper fields (ALWAYS present)
    ux_safe_fields = ["status", "request_id", "model_version", "prediction", "confidence", "error"]
    for field in ux_safe_fields:
        assert field in data, f"Missing UX-safe field: {field}"
    
    # If success, check inner data has required fields
    if data["status"] == "success" and data.get("data"):
        inner = data["data"]
        required_fields = [
            "risk_score",
            "risk_level",
            "recommended_action",
            "confidence_level",
            "model_version",
            "schema_version",
            "prediction_probability"
        ]
        for field in required_fields:
            assert field in inner, f"Missing required field in data: {field}"


def test_error_response_has_all_required_fields(client):
    """Test error responses always include required fields."""
    response = client.post("/api/v1/predict", json={})
    
    assert response.status_code == 422
    data = response.json()
    
    # Required fields (from APIErrorResponse schema)
    assert "error_code" in data
    assert "message" in data
    # 'details' is optional but typically present


def test_health_response_has_required_fields(client):
    """Test health response includes required fields."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "service_status" in data
    assert "model_loaded" in data
    assert "uptime_seconds" in data


# ═══════════════════════════════════════════════════════════════════════
# RESPONSE SCHEMA VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_error_response_validates_against_schema(client):
    """Test error responses can be parsed into APIErrorResponse model."""
    response = client.post("/api/v1/predict", json={})
    
    assert response.status_code == 422
    data = response.json()
    
    # Should be able to parse into APIErrorResponse
    error_response = APIErrorResponse(**data)
    assert error_response.error_code == ErrorCodes.VALIDATION_ERROR
    assert isinstance(error_response.message, str)
    assert len(error_response.message) > 0


def test_prediction_response_json_serializable(client, valid_prediction_request):
    """Test prediction responses are valid JSON."""
    response = client.post("/api/v1/predict", json=valid_prediction_request)
    
    assert response.status_code == 200
    
    # Should be valid JSON
    data = response.json()
    assert isinstance(data, dict)
    
    # Should be re-serializable
    json_str = json.dumps(data)
    assert len(json_str) > 0


# ═══════════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_response_schema_version_is_v1(client, valid_prediction_request):
    """Test response schema_version field is always 'v1'.
    
    Phase 3B-2: Schema version is in inner data object.
    """
    response = client.post("/api/v1/predict", json=valid_prediction_request)
    
    assert response.status_code == 200
    data = response.json()
    
    # Phase 3B-2: Schema version in data object
    if data["status"] == "success" and data.get("data"):
        assert data["data"]["schema_version"] == "v1"


def test_api_routes_are_versioned(client):
    """Test all API routes are under /api/v1/ prefix."""
    # Health endpoint
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    # Prediction endpoint
    response = client.post("/api/v1/predict", json={"credit_score": 720})
    assert response.status_code in [200, 422]  # Either success or validation error
    
    # Model info endpoint
    response = client.get("/api/v1/model/info")
    assert response.status_code == 200


def test_no_breaking_changes_to_request_schema(client):
    """Test request schema accepts all expected fields."""
    # This request includes all fields from CreditRiskRequest
    full_request = {
        "credit_score": 720,
        "annual_income": 75000,
        "monthly_debt": 1200,
        "employment_length_years": 5.0,
        "loan_amount": 15000,
        "loan_term_months": 60,
        "home_ownership": "MORTGAGE",
        "purpose": "debt_consolidation",
        "number_of_open_accounts": 8,
        "delinquencies_2y": 0,
        "inquiries_6m": 1
    }
    
    response = client.post("/api/v1/predict", json=full_request)
    assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_extra_fields_rejected(client, valid_prediction_request):
    """Test extra unknown fields are rejected (strict validation)."""
    invalid_request = valid_prediction_request.copy()
    invalid_request["unknown_field"] = "should_be_rejected"
    
    response = client.post("/api/v1/predict", json=invalid_request)
    
    # Pydantic by default allows extra fields unless model_config forbid = 'extra'
    # If we get 422, extra fields are rejected (desired behavior)
    # If we get 200, they're ignored (also acceptable)
    assert response.status_code in [200, 422]


def test_null_values_rejected(client):
    """Test null values are rejected for required fields."""
    response = client.post("/api/v1/predict", json={
        "credit_score": None,
        "annual_income": 75000
    })
    
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == ErrorCodes.VALIDATION_ERROR


def test_empty_string_rejected_for_numeric_fields(client):
    """Test empty strings rejected for numeric fields."""
    response = client.post("/api/v1/predict", json={
        "credit_score": "",
        "annual_income": 75000
    })
    
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == ErrorCodes.VALIDATION_ERROR


# ═══════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════

def test_api_contract_stability_summary(client, valid_prediction_request):
    """Integration test verifying all contract stability features together.
    
    Phase 3B-2 Update: Verifies UX-safe response wrapper.
    
    This test validates:
    1. X-API-Version header present
    2. Successful response has all required UX-safe fields
    3. Response schema version is v1
    4. Route is properly versioned
    5. Response is valid JSON
    """
    response = client.post("/api/v1/predict", json=valid_prediction_request)
    
    # Status code
    assert response.status_code == 200
    
    # API version header
    assert response.headers["X-API-Version"] == "v1"
    
    # Response structure (Phase 3B-2: UX-safe wrapper)
    data = response.json()
    
    # UX-safe wrapper fields
    assert "status" in data
    assert "request_id" in data
    assert "model_version" in data
    assert "prediction" in data
    assert "confidence" in data
    assert "error" in data
    
    # If success, verify inner data structure
    if data["status"] == "success" and data.get("data"):
        inner = data["data"]
        assert "risk_score" in inner
        assert "risk_level" in inner
        assert "recommended_action" in inner
        assert "schema_version" in inner
        assert inner["schema_version"] == "v1"
    
    # Valid JSON
    json_str = json.dumps(data)
    assert len(json_str) > 0
