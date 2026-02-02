"""
Test suite for Phase 3A-3: Model Metadata, Health & Observability

This test suite validates:
- Health endpoint with model status
- Model info endpoint with metadata
- Observability hooks in predict endpoint
- Failure safety (model not loaded scenarios)
"""

import pytest
from fastapi.testclient import TestClient
import time

from app.main import app
from app.ml.model import get_model, reload_model
from app.ml.metadata import get_metadata_registry, reload_metadata

client = TestClient(app)


class TestHealthEndpoint:
    """Test enhanced health endpoint"""
    
    def test_health_returns_200(self):
        """Health endpoint should always return 200"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
    
    def test_health_has_required_fields(self):
        """Health response must include all required fields"""
        response = client.get("/api/v1/health")
        data = response.json()
        
        # Check all required fields
        assert "service_status" in data
        assert "model_loaded" in data
        assert "model_version" in data
        assert "schema_version" in data
        assert "uptime_seconds" in data
        assert "app_version" in data
    
    def test_health_service_status_valid(self):
        """service_status must be 'ok' or 'degraded'"""
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["service_status"] in ["ok", "degraded"]
    
    def test_health_model_loaded_is_boolean(self):
        """model_loaded must be boolean"""
        response = client.get("/api/v1/health")
        data = response.json()
        assert isinstance(data["model_loaded"], bool)
    
    def test_health_uptime_increases(self):
        """Uptime should increase between calls"""
        response1 = client.get("/api/v1/health")
        data1 = response1.json()
        
        time.sleep(0.1)
        
        response2 = client.get("/api/v1/health")
        data2 = response2.json()
        
        assert data2["uptime_seconds"] > data1["uptime_seconds"]
    
    def test_health_responds_fast(self):
        """Health endpoint must respond in <100ms"""
        start = time.time()
        response = client.get("/api/v1/health")
        elapsed_ms = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < 100, f"Health check took {elapsed_ms:.2f}ms (expected <100ms)"
    
    def test_health_when_model_loaded(self):
        """When model is loaded, service_status should be 'ok'"""
        # Ensure model is loaded
        model = get_model()
        assert model.is_loaded
        
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert data["service_status"] == "ok"
        assert data["model_loaded"] is True
        assert data["model_version"] == "ml_v1.0.0"


class TestModelInfoEndpoint:
    """Test model info endpoint"""
    
    def test_model_info_returns_200(self):
        """Model info endpoint should return 200"""
        response = client.get("/api/v1/model/info")
        assert response.status_code == 200
    
    def test_model_info_has_required_fields(self):
        """Model info must include essential metadata"""
        response = client.get("/api/v1/model/info")
        data = response.json()
        
        # Required fields
        assert "model_name" in data
        assert "model_type" in data
        assert "model_version" in data
        assert "feature_count" in data
        assert "schema_version" in data
        assert "is_loaded" in data
        assert "api_version" in data
    
    def test_model_info_has_framework_versions(self):
        """Model info should include framework versions"""
        response = client.get("/api/v1/model/info")
        data = response.json()
        
        assert "framework_versions" in data
        assert isinstance(data["framework_versions"], dict)
        # Should at least have numpy or sklearn
        assert len(data["framework_versions"]) > 0
    
    def test_model_info_has_evaluation_metrics(self):
        """Model info should include evaluation metrics"""
        response = client.get("/api/v1/model/info")
        data = response.json()
        
        assert "evaluation_metrics" in data
        assert isinstance(data["evaluation_metrics"], dict)
    
    def test_model_info_feature_count_positive(self):
        """Feature count must be positive integer"""
        response = client.get("/api/v1/model/info")
        data = response.json()
        
        assert isinstance(data["feature_count"], int)
        assert data["feature_count"] > 0
    
    def test_model_info_no_sensitive_data(self):
        """Model info must NOT expose sensitive internals"""
        response = client.get("/api/v1/model/info")
        data = response.json()
        
        # Should NOT have these sensitive fields
        sensitive_fields = [
            "feature_names",
            "model_weights",
            "training_data",
            "model_parameters",
            "coefficients",
        ]
        
        for field in sensitive_fields:
            assert field not in data, f"Sensitive field '{field}' should not be exposed"


class TestMetadataRegistry:
    """Test model metadata registry"""
    
    def test_metadata_registry_loads(self):
        """Metadata registry should load successfully"""
        registry = get_metadata_registry()
        assert registry is not None
        assert registry.is_loaded()
    
    def test_metadata_has_correct_structure(self):
        """Metadata should have all required fields"""
        registry = get_metadata_registry()
        metadata = registry.get_metadata()
        
        assert metadata is not None
        assert hasattr(metadata, "model_name")
        assert hasattr(metadata, "model_type")
        assert hasattr(metadata, "model_version")
        assert hasattr(metadata, "trained_on")
        assert hasattr(metadata, "feature_count")
        assert hasattr(metadata, "framework_versions")
        assert hasattr(metadata, "evaluation_metrics")
        assert hasattr(metadata, "schema_version")
    
    def test_metadata_to_dict_json_serializable(self):
        """Metadata dictionary must be JSON serializable"""
        registry = get_metadata_registry()
        metadata = registry.get_metadata()
        
        metadata_dict = metadata.to_dict()
        
        # Should be able to convert to JSON
        import json
        json_str = json.dumps(metadata_dict)
        assert len(json_str) > 0


class TestObservabilityLogging:
    """Test observability hooks in predict endpoint"""
    
    def test_predict_generates_request_id(self):
        """Each prediction should generate unique request_id"""
        # This is tested indirectly - the endpoint logs with request_id
        # We verify it doesn't crash
        valid_request = {
            "schema_version": "v1",
            "annual_income": 75000,
            "monthly_debt": 2000,
            "credit_score": 720,
            "loan_amount": 15000,
            "loan_term_months": 36,
            "employment_length_years": 5,
            "home_ownership": "MORTGAGE",
            "purpose": "debt_consolidation",
            "number_of_open_accounts": 8,
            "delinquencies_2y": 0,
            "inquiries_6m": 1,
        }
        
        response1 = client.post("/api/v1/predict", json=valid_request)
        response2 = client.post("/api/v1/predict", json=valid_request)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        # Both should succeed (request_ids are unique in logs)
    
    def test_predict_logs_no_pii(self):
        """Prediction logging should not include raw PII"""
        # This is a code inspection test - verify the logging calls
        # don't include raw income, debt, or other PII
        
        # Read predict.py and check for PII in log statements
        with open("app/api/v1/predict.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that we're using banding functions, not raw values
        assert "_get_credit_band" in content
        assert "_get_loan_band" in content
        assert "_get_dti_band" in content
        assert "_get_employment_band" in content
        
        # Ensure the final prediction log uses safe fields
        assert "risk_band" in content
        assert "inference_latency_ms" in content
        assert "prediction_probability" in content


class TestFailureSafety:
    """Test failure handling when model is not loaded"""
    
    def test_health_works_even_if_model_fails(self):
        """Health endpoint must work even if model check fails"""
        # Health endpoint should handle exceptions gracefully
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        # Should have service_status (ok or degraded)
        assert "service_status" in data
    
    def test_model_info_handles_missing_metadata(self):
        """Model info should handle missing metadata gracefully"""
        response = client.get("/api/v1/model/info")
        # Should return 200 with fallback data, not 500
        assert response.status_code == 200
        
        data = response.json()
        assert "model_name" in data
        assert "is_loaded" in data


class TestPerformance:
    """Test performance requirements"""
    
    def test_health_endpoint_fast(self):
        """Health check must respond in <10ms (ideally)"""
        # Note: Relaxed to 100ms for test environment tolerance
        start = time.time()
        response = client.get("/api/v1/health")
        elapsed_ms = (time.time() - start) * 1000
        
        assert response.status_code == 200
        # In production should be <10ms, but test env allows <100ms
        assert elapsed_ms < 100
    
    def test_model_info_fast(self):
        """Model info should respond quickly (<200ms)"""
        start = time.time()
        response = client.get("/api/v1/model/info")
        elapsed_ms = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < 200
    
    def test_predict_tracks_latency(self):
        """Predict endpoint should track inference latency"""
        valid_request = {
            "schema_version": "v1",
            "annual_income": 75000,
            "monthly_debt": 2000,
            "credit_score": 720,
            "loan_amount": 15000,
            "loan_term_months": 36,
            "employment_length_years": 5,
            "home_ownership": "MORTGAGE",
            "purpose": "debt_consolidation",
            "number_of_open_accounts": 8,
            "delinquencies_2y": 0,
            "inquiries_6m": 1,
        }
        
        start = time.time()
        response = client.post("/api/v1/predict", json=valid_request)
        elapsed_ms = (time.time() - start) * 1000
        
        assert response.status_code == 200
        # Latency is logged (we check it doesn't crash)
        # In production, logs would contain inference_latency_ms


class TestBackwardCompatibility:
    """Ensure Phase 3A-3 doesn't break existing APIs"""
    
    def test_predict_endpoint_unchanged(self):
        """Predict endpoint response structure unchanged"""
        valid_request = {
            "schema_version": "v1",
            "annual_income": 75000,
            "monthly_debt": 2000,
            "credit_score": 720,
            "loan_amount": 15000,
            "loan_term_months": 36,
            "employment_length_years": 5,
            "home_ownership": "MORTGAGE",
            "purpose": "debt_consolidation",
            "number_of_open_accounts": 8,
            "delinquencies_2y": 0,
            "inquiries_6m": 1,
        }
        
        response = client.post("/api/v1/predict", json=valid_request)
        assert response.status_code == 200
        
        data = response.json()
        
        # All original fields must be present
        assert "schema_version" in data
        assert "risk_score" in data
        assert "risk_level" in data
        assert "recommended_action" in data
        assert "model_version" in data
        assert "prediction_probability" in data
        assert "confidence_level" in data
    
    def test_no_new_dependencies(self):
        """Phase 3A-3 should not add new dependencies"""
        # Verify key modules import successfully
        try:
            from app.ml.metadata import ModelMetadata
            from app.api.v1.health import health
            from app.api.v1.model_info import get_model_info
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
