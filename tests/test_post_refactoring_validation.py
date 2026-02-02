"""Post-refactoring validation tests for ML stability implementation.

Tests validate that after the ML inference stability refactoring:
1. Health endpoint works correctly
2. Predict endpoint works with valid input
3. Invalid inputs return structured errors
4. System info endpoint works (new endpoint)
5. All endpoints respond correctly

These tests are fast, deterministic, and use pytest with minimal mocking.
"""

import pytest
from fastapi.testclient import TestClient
import time
from typing import Dict, Any

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def valid_predict_request() -> Dict[str, Any]:
    """Valid prediction request payload."""
    return {
        "credit_score": 720,
        "annual_income": 75000,
        "monthly_debt": 2000,
        "employment_length_years": 5.0,
        "loan_amount": 25000,
        "loan_term_months": 36,
        "home_ownership": "RENT",
        "purpose": "debt_consolidation",
        "number_of_open_accounts": 8,
        "delinquencies_2y": 0,
        "inquiries_6m": 1
    }


# ═══════════════════════════════════════════════════════════════════════
# HEALTH ENDPOINT VALIDATION
# ═══════════════════════════════════════════════════════════════════════


def test_health_endpoint_returns_200(client):
    """Test /api/v1/health returns HTTP 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_endpoint_returns_json(client):
    """Test /api/v1/health returns valid JSON."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    # Should be valid JSON
    data = response.json()
    assert isinstance(data, dict)


def test_health_endpoint_has_required_fields(client):
    """Test /api/v1/health has all required fields."""
    response = client.get("/api/v1/health")
    data = response.json()
    
    # Required fields from HealthResponse schema
    assert "service_status" in data
    assert "api_version" in data
    assert "model_loaded" in data
    assert "model_version" in data
    assert "schema_version" in data
    assert "uptime_seconds" in data
    assert "app_version" in data


def test_health_endpoint_service_status_valid(client):
    """Test /api/v1/health service_status is valid."""
    response = client.get("/api/v1/health")
    data = response.json()
    
    assert data["service_status"] in ["ok", "degraded"]


def test_health_endpoint_api_version_correct(client):
    """Test /api/v1/health returns correct API version."""
    response = client.get("/api/v1/health")
    data = response.json()
    
    assert data["api_version"] == "v1"


def test_health_endpoint_model_loaded_is_boolean(client):
    """Test /api/v1/health model_loaded is boolean."""
    response = client.get("/api/v1/health")
    data = response.json()
    
    assert isinstance(data["model_loaded"], bool)


def test_health_endpoint_uptime_is_positive(client):
    """Test /api/v1/health uptime_seconds is positive."""
    response = client.get("/api/v1/health")
    data = response.json()
    
    assert data["uptime_seconds"] >= 0
    assert isinstance(data["uptime_seconds"], (int, float))


def test_health_endpoint_is_fast_after_warmup(client):
    """Test /api/v1/health is fast after initial warmup."""
    # Warmup call
    client.get("/api/v1/health")
    
    # Timed call
    start = time.time()
    response = client.get("/api/v1/health")
    duration_ms = (time.time() - start) * 1000
    
    assert response.status_code == 200
    # Should be very fast after warmup (< 500ms is reasonable)
    assert duration_ms < 500


# ═══════════════════════════════════════════════════════════════════════
# PREDICT ENDPOINT VALIDATION
# ═══════════════════════════════════════════════════════════════════════


def test_predict_endpoint_returns_200_with_valid_input(client, valid_predict_request):
    """Test /api/v1/predict returns HTTP 200 with valid input."""
    response = client.post("/api/v1/predict", json=valid_predict_request)
    assert response.status_code == 200


def test_predict_endpoint_returns_json(client, valid_predict_request):
    """Test /api/v1/predict returns valid JSON."""
    response = client.post("/api/v1/predict", json=valid_predict_request)
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    
    data = response.json()
    assert isinstance(data, dict)


def test_predict_endpoint_has_required_fields(client, valid_predict_request):
    """Test /api/v1/predict response has required fields."""
    response = client.post("/api/v1/predict", json=valid_predict_request)
    data = response.json()
    
    # Required fields from CreditRiskResponse schema
    assert "risk_score" in data or ("data" in data and "risk_score" in data.get("data", {}))
    assert "model_version" in data or ("data" in data and "model_version" in data.get("data", {}))
    
    # The response might be wrapped in a data field (UX-safe response format)
    if "data" in data:
        inner_data = data["data"]
        assert "risk_score" in inner_data or "risk_level" in inner_data


def test_predict_endpoint_risk_score_in_valid_range(client, valid_predict_request):
    """Test /api/v1/predict risk_score is in valid range [0, 1]."""
    response = client.post("/api/v1/predict", json=valid_predict_request)
    data = response.json()
    
    # Extract risk_score from nested structure if needed
    if "data" in data and isinstance(data["data"], dict):
        risk_score = data["data"].get("risk_score", data["data"].get("prediction_probability"))
    else:
        risk_score = data.get("risk_score", data.get("prediction_probability"))
    
    assert risk_score is not None
    assert isinstance(risk_score, (int, float))
    assert 0 <= risk_score <= 1


def test_predict_endpoint_risk_tier_is_valid(client, valid_predict_request):
    """Test /api/v1/predict risk_level is valid enum value."""
    response = client.post("/api/v1/predict", json=valid_predict_request)
    data = response.json()
    
    # Extract risk_level from nested structure if needed
    if "data" in data and isinstance(data["data"], dict):
        risk_level = data["data"].get("risk_level")
    else:
        risk_level = data.get("risk_level")
    
    # Valid risk levels from schema
    valid_levels = ["LOW", "MEDIUM", "HIGH", "VERY_HIGH", "MINIMAL", "MODERATE", "EXTREME"]
    assert risk_level in valid_levels


def test_predict_endpoint_approval_chance_is_valid(client, valid_predict_request):
    """Test /api/v1/predict recommended_action is valid enum value."""
    response = client.post("/api/v1/predict", json=valid_predict_request)
    data = response.json()
    
    # Extract recommended_action from nested structure if needed
    if "data" in data and isinstance(data["data"], dict):
        action = data["data"].get("recommended_action")
    else:
        action = data.get("recommended_action")
    
    # Valid actions from schema
    valid_actions = ["APPROVE", "REVIEW", "REJECT"]
    # May not always be present depending on response format
    if action is not None:
        assert action in valid_actions


def test_predict_endpoint_model_version_present(client, valid_predict_request):
    """Test /api/v1/predict includes model_version."""
    response = client.post("/api/v1/predict", json=valid_predict_request)
    data = response.json()
    
    assert data["model_version"] is not None
    assert len(data["model_version"]) > 0


def test_predict_endpoint_is_deterministic(client, valid_predict_request):
    """Test /api/v1/predict returns same result for same input."""
    response1 = client.post("/api/v1/predict", json=valid_predict_request)
    response2 = client.post("/api/v1/predict", json=valid_predict_request)
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Extract risk scores from potentially nested structure
    if "data" in data1 and isinstance(data1["data"], dict):
        score1 = data1["data"].get("risk_score", data1["data"].get("prediction_probability"))
        score2 = data2["data"].get("risk_score", data2["data"].get("prediction_probability"))
    else:
        score1 = data1.get("risk_score", data1.get("prediction_probability"))
        score2 = data2.get("risk_score", data2.get("prediction_probability"))
    
    # Same input should give same risk score
    assert score1 == score2


# ═══════════════════════════════════════════════════════════════════════
# ERROR HANDLING VALIDATION
# ═══════════════════════════════════════════════════════════════════════


def test_predict_missing_required_field_returns_422(client):
    """Test /api/v1/predict returns 422 for missing required field."""
    invalid_request = {
        "credit_score": 720,
        # Missing annual_income (required)
        "monthly_debt": 2000,
        "employment_length_years": 5.0,
        "loan_amount": 25000,
        "loan_term_months": 36,
        "home_ownership": "RENT",
        "purpose": "debt_consolidation",
        "number_of_open_accounts": 8,
        "delinquencies_2y": 0,
        "inquiries_6m": 1
    }
    
    response = client.post("/api/v1/predict", json=invalid_request)
    assert response.status_code == 422


def test_predict_invalid_field_type_returns_422(client):
    """Test /api/v1/predict returns 422 for invalid field type."""
    invalid_request = {
        "credit_score": "not_a_number",  # Should be int
        "annual_income": 75000,
        "monthly_debt": 2000,
        "employment_length_years": 5.0,
        "loan_amount": 25000,
        "loan_term_months": 36,
        "home_ownership": "RENT",
        "purpose": "debt_consolidation",
        "number_of_open_accounts": 8,
        "delinquencies_2y": 0,
        "inquiries_6m": 1
    }
    
    response = client.post("/api/v1/predict", json=invalid_request)
    assert response.status_code == 422


def test_predict_invalid_enum_value_returns_422(client):
    """Test /api/v1/predict returns 422 for invalid enum value."""
    invalid_request = {
        "credit_score": 720,
        "annual_income": 75000,
        "monthly_debt": 2000,
        "employment_length_years": 5.0,
        "loan_amount": 25000,
        "loan_term_months": 36,
        "home_ownership": "INVALID_VALUE",  # Invalid enum
        "purpose": "debt_consolidation",
        "number_of_open_accounts": 8,
        "delinquencies_2y": 0,
        "inquiries_6m": 1
    }
    
    response = client.post("/api/v1/predict", json=invalid_request)
    assert response.status_code == 422


def test_predict_out_of_range_value_returns_422(client):
    """Test /api/v1/predict returns 422 for out-of-range value."""
    invalid_request = {
        "credit_score": 1000,  # Max is 850
        "annual_income": 75000,
        "monthly_debt": 2000,
        "employment_length_years": 5.0,
        "loan_amount": 25000,
        "loan_term_months": 36,
        "home_ownership": "RENT",
        "purpose": "debt_consolidation",
        "number_of_open_accounts": 8,
        "delinquencies_2y": 0,
        "inquiries_6m": 1
    }
    
    response = client.post("/api/v1/predict", json=invalid_request)
    assert response.status_code == 422


def test_error_response_has_detail_field(client):
    """Test error responses have detail or details field."""
    invalid_request = {"invalid": "data"}
    
    response = client.post("/api/v1/predict", json=invalid_request)
    assert response.status_code == 422
    
    data = response.json()
    # Structured error responses have either 'detail' or 'details' field
    assert "detail" in data or "details" in data or "message" in data


def test_error_response_is_json(client):
    """Test error responses are JSON formatted."""
    invalid_request = {"invalid": "data"}
    
    response = client.post("/api/v1/predict", json=invalid_request)
    assert response.status_code == 422
    assert "application/json" in response.headers["content-type"]
    
    # Should be parseable JSON
    data = response.json()
    assert isinstance(data, dict)


# ═══════════════════════════════════════════════════════════════════════
# SYSTEM INFO ENDPOINT VALIDATION (NEW)
# ═══════════════════════════════════════════════════════════════════════


def test_system_info_endpoint_returns_200(client):
    """Test /api/v1/system/info returns HTTP 200."""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200


def test_system_info_endpoint_returns_json(client):
    """Test /api/v1/system/info returns valid JSON."""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    
    data = response.json()
    assert isinstance(data, dict)


def test_system_info_has_required_sections(client):
    """Test /api/v1/system/info has all required sections."""
    response = client.get("/api/v1/system/info")
    data = response.json()
    
    # Required top-level fields
    assert "service_name" in data
    assert "api_version" in data
    assert "app_version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    
    # Required nested sections
    assert "model" in data
    assert "artifacts" in data
    assert "startup" in data


def test_system_info_model_section_complete(client):
    """Test /api/v1/system/info model section has required fields."""
    response = client.get("/api/v1/system/info")
    data = response.json()
    
    model = data["model"]
    assert "model_name" in model
    assert "model_type" in model
    assert "model_version" in model
    assert "training_timestamp" in model
    assert "is_loaded" in model
    assert "engine" in model
    assert "feature_count" in model
    assert "schema_version" in model


def test_system_info_artifacts_section_complete(client):
    """Test /api/v1/system/info artifacts section has required fields."""
    response = client.get("/api/v1/system/info")
    data = response.json()
    
    artifacts = data["artifacts"]
    assert "model_file_present" in artifacts
    assert "preprocessor_present" in artifacts
    assert "shap_explainer_present" in artifacts
    
    # All should be booleans
    assert isinstance(artifacts["model_file_present"], bool)
    assert isinstance(artifacts["preprocessor_present"], bool)
    assert isinstance(artifacts["shap_explainer_present"], bool)


def test_system_info_startup_section_complete(client):
    """Test /api/v1/system/info startup section has required fields."""
    response = client.get("/api/v1/system/info")
    data = response.json()
    
    startup = data["startup"]
    assert "healthy" in startup
    assert "degraded" in startup
    assert "errors" in startup
    
    # Validate types
    assert isinstance(startup["healthy"], bool)
    assert isinstance(startup["degraded"], bool)
    assert isinstance(startup["errors"], list)


def test_system_info_engine_is_valid(client):
    """Test /api/v1/system/info model.engine is valid value."""
    response = client.get("/api/v1/system/info")
    data = response.json()
    
    engine = data["model"]["engine"]
    assert engine in ["ml", "rule_based"]


# ═══════════════════════════════════════════════════════════════════════
# API VERSION HEADER VALIDATION
# ═══════════════════════════════════════════════════════════════════════


def test_all_endpoints_have_api_version_header(client, valid_predict_request):
    """Test all endpoints return X-API-Version header."""
    # Health endpoint
    response = client.get("/api/v1/health")
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "v1"
    
    # Predict endpoint
    response = client.post("/api/v1/predict", json=valid_predict_request)
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "v1"
    
    # System info endpoint
    response = client.get("/api/v1/system/info")
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "v1"


# ═══════════════════════════════════════════════════════════════════════
# INTEGRATION VALIDATION
# ═══════════════════════════════════════════════════════════════════════


def test_health_and_predict_consistency(client, valid_predict_request):
    """Test health endpoint model_loaded matches predict functionality."""
    health_response = client.get("/api/v1/health")
    health_data = health_response.json()
    
    predict_response = client.post("/api/v1/predict", json=valid_predict_request)
    
    # If model is loaded, predict should work
    if health_data["model_loaded"]:
        assert predict_response.status_code == 200
    
    # If predict works, model must be loaded
    if predict_response.status_code == 200:
        assert health_data["model_loaded"] or health_data["service_status"] == "degraded"


def test_system_info_matches_health(client):
    """Test system/info model status matches health endpoint."""
    health_response = client.get("/api/v1/health")
    health_data = health_response.json()
    
    system_response = client.get("/api/v1/system/info")
    system_data = system_response.json()
    
    # Model loaded status should match
    assert health_data["model_loaded"] == system_data["model"]["is_loaded"]
    
    # API versions should match
    assert health_data["api_version"] == system_data["api_version"]


def test_no_regression_predict_still_works(client, valid_predict_request):
    """Test predict endpoint still works after refactoring (no regression)."""
    response = client.post("/api/v1/predict", json=valid_predict_request)
    
    # Should succeed
    assert response.status_code == 200
    
    # Should return valid prediction
    data = response.json()
    
    # Handle both nested and flat response structures
    if "data" in data and isinstance(data["data"], dict):
        inner_data = data["data"]
        assert "risk_score" in inner_data or "prediction_probability" in inner_data
        risk_score = inner_data.get("risk_score", inner_data.get("prediction_probability"))
    else:
        assert "risk_score" in data or "prediction_probability" in data
        risk_score = data.get("risk_score", data.get("prediction_probability"))
    
    # Risk score should be reasonable
    assert risk_score is not None
    assert 0 <= risk_score <= 1
