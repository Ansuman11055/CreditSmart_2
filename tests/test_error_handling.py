"""
Integration tests for centralized error handling.

Tests verify:
- All errors include request_id and timestamp
- Stack traces are never exposed to clients
- X-Request-ID header is present on all responses
- Error codes and messages are consistent
- HTTP status codes are correct
"""
import pytest
import re
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestErrorHandling:
    """Test suite for centralized error handling."""
    
    def test_validation_error_structure(self):
        """Test validation error returns proper structure with request_id."""
        response = client.post(
            "/api/v1/risk-analysis",
            json={
                "annualIncome": -1000,  # Invalid: negative income
                "monthlyDebt": 1200,
                "creditScore": 720,
                "loanAmount": 25000,
                "employmentYears": 5,
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        
        # Verify required fields
        assert "error_code" in data
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "message" in data
        assert "request_id" in data
        assert "timestamp" in data
        assert "details" in data
        
        # Verify request_id is valid UUID
        try:
            uuid.UUID(data["request_id"])
        except ValueError:
            pytest.fail(f"Invalid UUID format: {data['request_id']}")
        
        # Verify timestamp is ISO 8601
        try:
            datetime.fromisoformat(data["timestamp"].replace("+00:00", ""))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {data['timestamp']}")
        
        # Verify no stack trace
        assert "stack_trace" not in data
        assert "traceback" not in str(data).lower()
    
    def test_x_request_id_header_on_success(self):
        """Test successful requests include X-Request-ID header."""
        response = client.post(
            "/api/v1/risk-analysis",
            json={
                "annualIncome": 75000,
                "monthlyDebt": 1200,
                "creditScore": 720,
                "loanAmount": 25000,
                "employmentYears": 5,
            }
        )
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        
        # Verify header value is valid UUID
        request_id = response.headers["X-Request-ID"]
        try:
            uuid.UUID(request_id)
        except ValueError:
            pytest.fail(f"Invalid UUID in X-Request-ID header: {request_id}")
    
    def test_x_request_id_header_on_error(self):
        """Test error responses include X-Request-ID header."""
        response = client.post(
            "/api/v1/risk-analysis",
            json={
                "annualIncome": -1000,
                "monthlyDebt": 1200,
                "creditScore": 720,
                "loanAmount": 25000,
                "employmentYears": 5,
            }
        )
        
        assert response.status_code == 422
        assert "X-Request-ID" in response.headers
        
        # Verify header UUID matches response body request_id
        header_request_id = response.headers["X-Request-ID"]
        body_request_id = response.json()["request_id"]
        assert header_request_id == body_request_id
    
    def test_multiple_validation_errors(self):
        """Test multiple validation errors are properly aggregated."""
        response = client.post(
            "/api/v1/risk-analysis",
            json={
                "annualIncome": -1000,  # Invalid: negative
                "monthlyDebt": -500,    # Invalid: negative
                "creditScore": 900,     # Invalid: > 850
                "loanAmount": -10000,   # Invalid: negative
                "employmentYears": -5,  # Invalid: negative
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        
        # Should have multiple errors
        assert "details" in data
        assert "errors" in data["details"]
        assert len(data["details"]["errors"]) > 1
        
        # Verify each error has field and message
        for error in data["details"]["errors"]:
            assert "field" in error
            assert "message" in error
            assert "type" in error
    
    def test_invalid_json_error(self):
        """Test invalid JSON returns proper error structure."""
        response = client.post(
            "/api/v1/risk-analysis",
            data="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        
        # FastAPI returns 422 for invalid JSON
        assert response.status_code == 422
        data = response.json()
        
        # Should still have error structure
        assert "detail" in data or "error_code" in data
    
    def test_missing_required_fields(self):
        """Test missing required fields returns validation error."""
        response = client.post(
            "/api/v1/risk-analysis",
            json={
                "annualIncome": 75000,
                # Missing other required fields
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "request_id" in data
        assert "timestamp" in data
    
    def test_timestamp_format_consistency(self):
        """Test timestamp format is consistent across errors."""
        # ISO 8601 format: YYYY-MM-DDTHH:MM:SS.ffffff+00:00
        iso_8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00$'
        
        response = client.post(
            "/api/v1/risk-analysis",
            json={
                "annualIncome": -1000,
                "monthlyDebt": 1200,
                "creditScore": 720,
                "loanAmount": 25000,
                "employmentYears": 5,
            }
        )
        
        timestamp = response.json()["timestamp"]
        assert re.match(iso_8601_pattern, timestamp), \
            f"Timestamp {timestamp} does not match ISO 8601 format"
    
    def test_error_message_clarity(self):
        """Test error messages are clear and actionable."""
        response = client.post(
            "/api/v1/risk-analysis",
            json={
                "annualIncome": -1000,
                "monthlyDebt": 1200,
                "creditScore": 720,
                "loanAmount": 25000,
                "employmentYears": 5,
            }
        )
        
        data = response.json()
        message = data["message"]
        
        # Message should mention the field name
        assert "annualIncome" in message or "annual income" in message.lower()
        # Should not contain internal details
        assert "traceback" not in message.lower()
        assert "exception" not in message.lower()
        assert "error:" not in message.lower() or "Error:" not in message.lower()


class TestErrorNonLeakage:
    """Test that sensitive information never leaks in errors."""
    
    def test_no_stack_traces_in_response(self):
        """Verify stack traces are never returned to clients."""
        response = client.post(
            "/api/v1/risk-analysis",
            json={
                "annualIncome": -1000,
                "monthlyDebt": 1200,
                "creditScore": 720,
                "loanAmount": 25000,
                "employmentYears": 5,
            }
        )
        
        response_text = response.text.lower()
        
        # Check for common stack trace indicators
        assert "traceback" not in response_text
        assert "file \"" not in response_text
        assert "line " not in response_text
        assert ".py\"" not in response_text
        assert "exception:" not in response_text
    
    def test_no_internal_paths_in_response(self):
        """Verify internal file paths are never exposed."""
        response = client.post(
            "/api/v1/risk-analysis",
            json={
                "annualIncome": -1000,
                "monthlyDebt": 1200,
                "creditScore": 720,
                "loanAmount": 25000,
                "employmentYears": 5,
            }
        )
        
        response_text = response.text
        
        # Check for path indicators
        assert "app/" not in response_text
        assert "app\\" not in response_text
        assert "/api/" not in response_text.lower() or "/api/v1" in response_text.lower()  # API path is OK
        assert "d:\\" not in response_text.lower()
        assert "c:\\" not in response_text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
