"""
Test suite for Response Schema v1 Contract Enforcement
Phase 3A-2: Response Schema Freeze Validation

This test suite validates that the response schema contract is frozen and enforced:
- Schema version field validation
- Required fields enforcement  
- Field type and range validation
- Enum validation for risk_level, recommended_action, confidence_level
- prediction_probability consistency with risk_score
- model_version is always present
- Extra fields are forbidden
- Factory method field derivation
- Backward compatibility with existing API tests
"""

import pytest
from pydantic import ValidationError
from app.schemas.response import (
    CreditRiskResponse,
    RiskLevel,
    RecommendedAction
)


class TestResponseSchemaVersion:
    """Test schema versioning contract"""
    
    def test_response_has_schema_version_field(self):
        """Schema version must be v1 for all responses"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.25,
            model_version="ml_v1.0.0"
        )
        assert response.schema_version == "v1"
        assert isinstance(response.schema_version, str)
    
    def test_schema_version_is_required(self):
        """schema_version field must be present (auto-populated)"""
        # Factory method should auto-populate
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.5,
            model_version="ml_v1.0.0"
        )
        response_dict = response.model_dump()
        assert "schema_version" in response_dict
        assert response_dict["schema_version"] == "v1"
    
    def test_schema_version_cannot_be_modified(self):
        """schema_version is a Literal and cannot be changed"""
        # The field defaults to "v1" and is a Literal type
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.3,
            model_version="ml_v1.0.0"
        )
        # Attempting to create with wrong version should fail
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(
                schema_version="v2",  # Wrong version
                risk_score=0.25,
                risk_level=RiskLevel.LOW,
                recommended_action=RecommendedAction.APPROVE,
                model_version="ml_v1.0.0",
                prediction_probability=0.25,
                confidence_level="HIGH"
            )
        assert "schema_version" in str(exc_info.value)


class TestRequiredFields:
    """Test that all required fields are enforced"""
    
    def test_all_required_fields_present(self):
        """All 7 required fields must be present in response"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.35,
            model_version="ml_v1.0.0"
        )
        # Check all required fields exist
        assert response.schema_version is not None
        assert response.risk_score is not None
        assert response.risk_level is not None
        assert response.recommended_action is not None
        assert response.model_version is not None
        assert response.prediction_probability is not None
        assert response.confidence_level is not None
    
    def test_model_version_is_required(self):
        """model_version field is required (changed from Optional to required)"""
        # Factory method requires model_version
        with pytest.raises(TypeError):
            CreditRiskResponse.from_risk_score(risk_score=0.5)
        
        # Direct instantiation requires model_version
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(
                schema_version="v1",
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                recommended_action=RecommendedAction.REVIEW,
                prediction_probability=0.5,
                confidence_level="MEDIUM"
                # model_version missing
            )
        assert "model_version" in str(exc_info.value)
    
    def test_prediction_probability_is_required(self):
        """prediction_probability is a new required field"""
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(
                schema_version="v1",
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                recommended_action=RecommendedAction.REVIEW,
                model_version="ml_v1.0.0",
                confidence_level="MEDIUM"
                # prediction_probability missing
            )
        assert "prediction_probability" in str(exc_info.value)
    
    def test_confidence_level_is_required(self):
        """confidence_level is a new required field"""
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(
                schema_version="v1",
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                recommended_action=RecommendedAction.REVIEW,
                model_version="ml_v1.0.0",
                prediction_probability=0.5
                # confidence_level missing
            )
        assert "confidence_level" in str(exc_info.value)


class TestFieldTypesAndRanges:
    """Test field types and value ranges"""
    
    def test_risk_score_range_validation(self):
        """risk_score must be float in [0, 1]"""
        # Valid range
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.5,
            model_version="ml_v1.0.0"
        )
        assert 0.0 <= response.risk_score <= 1.0
        
        # Invalid: negative
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(
                schema_version="v1",
                risk_score=-0.1,
                risk_level=RiskLevel.LOW,
                recommended_action=RecommendedAction.APPROVE,
                model_version="ml_v1.0.0",
                prediction_probability=-0.1,
                confidence_level="HIGH"
            )
        assert "risk_score" in str(exc_info.value)
        
        # Invalid: > 1
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(
                schema_version="v1",
                risk_score=1.5,
                risk_level=RiskLevel.VERY_HIGH,
                recommended_action=RecommendedAction.REJECT,
                model_version="ml_v1.0.0",
                prediction_probability=1.5,
                confidence_level="HIGH"
            )
        assert "risk_score" in str(exc_info.value)
    
    def test_risk_score_precision_rounding(self):
        """risk_score should be rounded to 4 decimal places"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.123456789,
            model_version="ml_v1.0.0"
        )
        # Check precision (should be rounded to 4 decimals)
        assert response.risk_score == pytest.approx(0.1235, abs=1e-4)
    
    def test_prediction_probability_matches_risk_score(self):
        """prediction_probability should equal risk_score"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.42,
            model_version="ml_v1.0.0"
        )
        assert response.prediction_probability == response.risk_score
    
    def test_model_version_is_string(self):
        """model_version must be non-empty string"""
        # Valid string
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.3,
            model_version="ml_v1.0.0"
        )
        assert isinstance(response.model_version, str)
        assert len(response.model_version) > 0
        
        # Note: Empty string validation would require Field(min_length=1)
        # Currently not enforced, so we just test valid case


class TestEnumValidation:
    """Test enum fields validation"""
    
    def test_risk_level_enum_validation(self):
        """risk_level must be valid RiskLevel enum"""
        # Valid enum values
        valid_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.VERY_HIGH]
        for level in valid_levels:
            response = CreditRiskResponse(
                schema_version="v1",
                risk_score=0.5,
                risk_level=level,
                recommended_action=RecommendedAction.REVIEW,
                model_version="ml_v1.0.0",
                prediction_probability=0.5,
                confidence_level="MEDIUM"
            )
            assert isinstance(response.risk_level, RiskLevel)
        
        # Invalid enum value
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(
                schema_version="v1",
                risk_score=0.5,
                risk_level="INVALID_LEVEL",
                recommended_action=RecommendedAction.REVIEW,
                model_version="ml_v1.0.0",
                prediction_probability=0.5,
                confidence_level="MEDIUM"
            )
        assert "risk_level" in str(exc_info.value)
    
    def test_recommended_action_enum_validation(self):
        """recommended_action must be valid RecommendedAction enum"""
        # Valid enum values
        valid_actions = [RecommendedAction.APPROVE, RecommendedAction.REVIEW, RecommendedAction.REJECT]
        for action in valid_actions:
            response = CreditRiskResponse(
                schema_version="v1",
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                recommended_action=action,
                model_version="ml_v1.0.0",
                prediction_probability=0.5,
                confidence_level="MEDIUM"
            )
            assert isinstance(response.recommended_action, RecommendedAction)
        
        # Invalid enum value
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(
                schema_version="v1",
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                recommended_action="INVALID_ACTION",
                model_version="ml_v1.0.0",
                prediction_probability=0.5,
                confidence_level="MEDIUM"
            )
        assert "recommended_action" in str(exc_info.value)
    
    def test_confidence_level_validation(self):
        """confidence_level must be HIGH, MEDIUM, or LOW"""
        # Valid values
        valid_levels = ["HIGH", "MEDIUM", "LOW"]
        for conf_level in valid_levels:
            response = CreditRiskResponse(
                schema_version="v1",
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                recommended_action=RecommendedAction.REVIEW,
                model_version="ml_v1.0.0",
                prediction_probability=0.5,
                confidence_level=conf_level
            )
            assert response.confidence_level in valid_levels
        
        # Invalid value
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(
                schema_version="v1",
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                recommended_action=RecommendedAction.REVIEW,
                model_version="ml_v1.0.0",
                prediction_probability=0.5,
                confidence_level="VERY_HIGH"  # Invalid
            )
        assert "confidence_level" in str(exc_info.value)


class TestFactoryMethodDerivation:
    """Test factory method auto-derives fields correctly"""
    
    def test_factory_derives_risk_level_low(self):
        """Factory should derive LOW risk for score < 0.25"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.15,
            model_version="ml_v1.0.0"
        )
        assert response.risk_level == RiskLevel.LOW
    
    def test_factory_derives_risk_level_medium(self):
        """Factory should derive MEDIUM risk for 0.25 <= score < 0.5"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.35,
            model_version="ml_v1.0.0"
        )
        assert response.risk_level == RiskLevel.MEDIUM
    
    def test_factory_derives_risk_level_high(self):
        """Factory should derive HIGH risk for 0.5 <= score < 0.75"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.6,
            model_version="ml_v1.0.0"
        )
        assert response.risk_level == RiskLevel.HIGH
    
    def test_factory_derives_risk_level_very_high(self):
        """Factory should derive VERY_HIGH risk for score >= 0.75"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.8,
            model_version="ml_v1.0.0"
        )
        assert response.risk_level == RiskLevel.VERY_HIGH
    
    def test_factory_derives_recommended_action_approve(self):
        """Factory should derive APPROVE for score < 0.25"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.15,
            model_version="ml_v1.0.0"
        )
        assert response.recommended_action == RecommendedAction.APPROVE
    
    def test_factory_derives_recommended_action_review(self):
        """Factory should derive REVIEW for 0.25 <= score < 0.5"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.35,
            model_version="ml_v1.0.0"
        )
        assert response.recommended_action == RecommendedAction.REVIEW
    
    def test_factory_derives_recommended_action_reject(self):
        """Factory should derive REJECT for score >= 0.5"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.6,
            model_version="ml_v1.0.0"
        )
        assert response.recommended_action == RecommendedAction.REJECT
    
    def test_factory_derives_confidence_level_high(self):
        """Factory should derive HIGH confidence for extreme scores"""
        # Low score -> HIGH confidence
        response_low = CreditRiskResponse.from_risk_score(
            risk_score=0.05,
            model_version="ml_v1.0.0"
        )
        assert response_low.confidence_level == "HIGH"
        
        # High score -> HIGH confidence
        response_high = CreditRiskResponse.from_risk_score(
            risk_score=0.95,
            model_version="ml_v1.0.0"
        )
        assert response_high.confidence_level == "HIGH"
    
    def test_factory_derives_confidence_level_medium(self):
        """Factory should derive MEDIUM confidence for moderate scores"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.35,
            model_version="ml_v1.0.0"
        )
        assert response.confidence_level == "MEDIUM"
    
    def test_factory_derives_confidence_level_low(self):
        """Factory should derive LOW confidence for mid-range scores"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.5,
            model_version="ml_v1.0.0"
        )
        assert response.confidence_level == "LOW"
    
    def test_factory_sets_prediction_probability(self):
        """Factory should set prediction_probability equal to risk_score"""
        risk_score = 0.6234
        response = CreditRiskResponse.from_risk_score(
            risk_score=risk_score,
            model_version="ml_v1.0.0"
        )
        assert response.prediction_probability == response.risk_score


class TestExtraFieldsRejection:
    """Test extra='forbid' enforcement"""
    
    def test_extra_fields_forbidden(self):
        """Schema should reject extra fields not in contract"""
        with pytest.raises(ValidationError) as exc_info:
            CreditRiskResponse(
                schema_version="v1",
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                recommended_action=RecommendedAction.REVIEW,
                model_version="ml_v1.0.0",
                prediction_probability=0.5,
                confidence_level="MEDIUM",
                extra_field="not_allowed",  # Extra field
                another_extra=123
            )
        error_str = str(exc_info.value)
        assert "extra_field" in error_str or "Extra inputs are not permitted" in error_str
    
    def test_model_dump_excludes_extra_fields(self):
        """Serialized response should only contain contract fields"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.4,
            model_version="ml_v1.0.0"
        )
        response_dict = response.model_dump()
        
        # Check only expected fields are present
        expected_fields = {
            "schema_version", "risk_score", "risk_level",
            "recommended_action", "model_version",
            "prediction_probability", "confidence_level",
            "explanation", "key_factors"
        }
        actual_fields = set(response_dict.keys())
        assert actual_fields == expected_fields


class TestBackwardCompatibility:
    """Test backward compatibility with existing API contracts"""
    
    def test_all_original_fields_present(self):
        """All original fields must still be present"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.5,
            model_version="ml_v1.0.0"
        )
        response_dict = response.model_dump()
        
        # Original required fields
        assert "risk_score" in response_dict
        assert "risk_level" in response_dict
        assert "recommended_action" in response_dict
        assert "model_version" in response_dict
        
        # Original optional fields
        assert "explanation" in response_dict
        assert "key_factors" in response_dict
    
    def test_field_types_backward_compatible(self):
        """Field types should match original contract"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.5,
            model_version="ml_v1.0.0"
        )
        
        # Type checks
        assert isinstance(response.risk_score, float)
        assert isinstance(response.risk_level, RiskLevel)
        assert isinstance(response.recommended_action, RecommendedAction)
        assert isinstance(response.model_version, str)
        assert response.explanation is None or isinstance(response.explanation, str)
        assert response.key_factors is None or isinstance(response.key_factors, dict)
    
    def test_enum_string_serialization(self):
        """Enums should serialize to strings for JSON compatibility"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.5,
            model_version="ml_v1.0.0"
        )
        response_dict = response.model_dump()
        
        # Enums serialize to strings
        assert isinstance(response_dict["risk_level"], str)
        assert isinstance(response_dict["recommended_action"], str)
        assert response_dict["risk_level"] in ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
        assert response_dict["recommended_action"] in ["APPROVE", "REVIEW", "REJECT"]


class TestOptionalFields:
    """Test optional fields behavior"""
    
    def test_explanation_is_optional(self):
        """explanation field should be optional"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.5,
            model_version="ml_v1.0.0"
        )
        # Factory doesn't set explanation by default
        assert response.explanation is None
        
        # Can be set manually
        response_with_explanation = CreditRiskResponse(
            schema_version="v1",
            risk_score=0.5,
            risk_level=RiskLevel.MEDIUM,
            recommended_action=RecommendedAction.REVIEW,
            model_version="ml_v1.0.0",
            prediction_probability=0.5,
            confidence_level="MEDIUM",
            explanation="Test explanation"
        )
        assert response_with_explanation.explanation == "Test explanation"
    
    def test_key_factors_is_optional(self):
        """key_factors field should be optional"""
        response = CreditRiskResponse.from_risk_score(
            risk_score=0.5,
            model_version="ml_v1.0.0"
        )
        # Factory doesn't set key_factors by default
        assert response.key_factors is None
        
        # Can be set manually
        response_with_factors = CreditRiskResponse(
            schema_version="v1",
            risk_score=0.5,
            risk_level=RiskLevel.MEDIUM,
            recommended_action=RecommendedAction.REVIEW,
            model_version="ml_v1.0.0",
            prediction_probability=0.5,
            confidence_level="MEDIUM",
            key_factors={"credit_score": 0.3, "debt_to_income": 0.2}
        )
        assert response_with_factors.key_factors == {"credit_score": 0.3, "debt_to_income": 0.2}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
