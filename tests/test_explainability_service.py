# Phase 4D Explainability - Unit tests for explainability service

"""Unit tests for explainability service.

Tests cover:
- Feature name mapping
- Risk band logic
- SHAP magnitude categorization
- Natural language explanation generation
- Explanation consistency
"""

import pytest
import numpy as np
from app.services.explainability_service import (
    ExplainabilityService,
    FeatureContribution,
    ExplanationResult,
    FEATURE_NAME_MAPPING,
    RISK_BANDS
)


class TestFeatureNameMapping:
    """Test human-readable feature name mapping."""
    
    def test_mapping_completeness(self):
        """Phase 4D Explainability - All expected features have mappings."""
        service = ExplainabilityService()
        
        # Core features
        assert "annual_income" in service.feature_mapping
        assert "credit_score" in service.feature_mapping
        assert "monthly_debt" in service.feature_mapping
        
        # Verify human-readable format
        assert service.feature_mapping["annual_income"] == "Annual Income"
        assert service.feature_mapping["credit_score"] == "Credit Score"
    
    def test_mapping_consistency(self):
        """Phase 4D Explainability - Mapping is deterministic."""
        service1 = ExplainabilityService()
        service2 = ExplainabilityService()
        
        assert service1.feature_mapping == service2.feature_mapping


class TestRiskBandLogic:
    """Test risk band categorization."""
    
    def test_low_risk_band(self):
        """Phase 4D Explainability - Low risk: probability < 0.3."""
        service = ExplainabilityService()
        
        band, description = service.get_risk_band(0.15)
        assert band == "low"
        assert "minimal" in description.lower()
        
        # Edge case: exactly 0.0
        band, _ = service.get_risk_band(0.0)
        assert band == "low"
        
        # Edge case: just below threshold
        band, _ = service.get_risk_band(0.29)
        assert band == "low"
    
    def test_medium_risk_band(self):
        """Phase 4D Explainability - Medium risk: 0.3 <= probability < 0.6."""
        service = ExplainabilityService()
        
        band, description = service.get_risk_band(0.45)
        assert band == "medium"
        assert "moderate" in description.lower() or "acceptable" in description.lower()
        
        # Edge case: exactly 0.3
        band, _ = service.get_risk_band(0.3)
        assert band == "medium"
        
        # Edge case: just below upper threshold
        band, _ = service.get_risk_band(0.59)
        assert band == "medium"
    
    def test_high_risk_band(self):
        """Phase 4D Explainability - High risk: probability >= 0.6."""
        service = ExplainabilityService()
        
        band, description = service.get_risk_band(0.75)
        assert band == "high"
        assert "elevated" in description.lower() or "high" in description.lower()
        
        # Edge case: exactly 0.6
        band, _ = service.get_risk_band(0.6)
        assert band == "high"
        
        # Edge case: exactly 1.0
        band, _ = service.get_risk_band(1.0)
        assert band == "high"
    
    def test_risk_band_determinism(self):
        """Phase 4D Explainability - Same probability always returns same band."""
        service = ExplainabilityService()
        
        probabilities = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        for prob in probabilities:
            band1, desc1 = service.get_risk_band(prob)
            band2, desc2 = service.get_risk_band(prob)
            
            assert band1 == band2
            assert desc1 == desc2


class TestSHAPMagnitude:
    """Test SHAP value magnitude categorization."""
    
    def test_magnitude_high(self):
        """Phase 4D Explainability - High magnitude: >= 75th percentile."""
        service = ExplainabilityService()
        
        # Create SHAP values where one is clearly high
        shap_values = np.array([0.01, 0.02, 0.03, 0.04, 0.10])
        
        magnitude = service.categorize_shap_magnitude(0.10, shap_values)
        assert magnitude == "high"
    
    def test_magnitude_medium(self):
        """Phase 4D Explainability - Medium magnitude: 50th-75th percentile."""
        service = ExplainabilityService()
        
        shap_values = np.array([0.01, 0.02, 0.03, 0.04, 0.10])
        
        magnitude = service.categorize_shap_magnitude(0.03, shap_values)
        assert magnitude in ["medium", "high"]  # Depends on percentile calculation
    
    def test_magnitude_low(self):
        """Phase 4D Explainability - Low magnitude: < 50th percentile."""
        service = ExplainabilityService()
        
        shap_values = np.array([0.01, 0.02, 0.03, 0.04, 0.10])
        
        magnitude = service.categorize_shap_magnitude(0.01, shap_values)
        assert magnitude == "low"


class TestExplanationGeneration:
    """Test natural language explanation generation."""
    
    def test_credit_score_positive_explanation(self):
        """Phase 4D Explainability - Good credit score gets positive explanation."""
        service = ExplainabilityService()
        
        explanation = service.generate_feature_explanation(
            feature_name="credit_score",
            feature_value=750,
            shap_value=-0.15,
            impact="positive"
        )
        
        assert "750" in explanation
        assert "excellent" in explanation.lower() or "good" in explanation.lower()
        assert "credit score" in explanation.lower()
    
    def test_credit_score_negative_explanation(self):
        """Phase 4D Explainability - Low credit score gets negative explanation."""
        service = ExplainabilityService()
        
        explanation = service.generate_feature_explanation(
            feature_name="credit_score",
            feature_value=580,
            shap_value=0.20,
            impact="negative"
        )
        
        assert "580" in explanation
        assert "low" in explanation.lower() or "concern" in explanation.lower()
    
    def test_income_positive_explanation(self):
        """Phase 4D Explainability - High income gets positive explanation."""
        service = ExplainabilityService()
        
        explanation = service.generate_feature_explanation(
            feature_name="annual_income",
            feature_value=85000,
            shap_value=-0.10,
            impact="positive"
        )
        
        assert "85,000" in explanation or "85000" in explanation
        assert "income" in explanation.lower()
        assert "support" in explanation.lower() or "strong" in explanation.lower()
    
    def test_delinquencies_explanation(self):
        """Phase 4D Explainability - Delinquencies get clear explanation."""
        service = ExplainabilityService()
        
        # With delinquencies
        explanation = service.generate_feature_explanation(
            feature_name="delinquencies_2y",
            feature_value=2,
            shap_value=0.15,
            impact="negative"
        )
        
        assert "2" in explanation
        assert "delinquenc" in explanation.lower()
        
        # No delinquencies
        explanation_zero = service.generate_feature_explanation(
            feature_name="delinquencies_2y",
            feature_value=0,
            shap_value=-0.05,
            impact="positive"
        )
        
        assert "no" in explanation_zero.lower() or "0" in explanation_zero


class TestImprovementSuggestions:
    """Test actionable improvement suggestions."""
    
    def test_suggestions_for_credit_score(self):
        """Phase 4D Explainability - Credit score issue gets improvement advice."""
        service = ExplainabilityService()
        
        # Create negative contribution for credit score
        contrib = FeatureContribution(
            feature_name="credit_score",
            human_name="Credit Score",
            shap_value=0.15,
            feature_value=600,
            impact="negative",
            magnitude="high",
            explanation="Low credit score"
        )
        
        suggestions = service.generate_improvement_suggestions([contrib], "high")
        
        assert len(suggestions) > 0
        # Check for actionable advice
        suggestions_text = " ".join(suggestions).lower()
        assert "credit" in suggestions_text or "payment" in suggestions_text
    
    def test_suggestions_for_debt(self):
        """Phase 4D Explainability - High debt gets debt reduction advice."""
        service = ExplainabilityService()
        
        contrib = FeatureContribution(
            feature_name="monthly_debt",
            human_name="Monthly Debt Payments",
            shap_value=0.20,
            feature_value=2500,
            impact="negative",
            magnitude="high",
            explanation="High monthly debt"
        )
        
        suggestions = service.generate_improvement_suggestions([contrib], "high")
        
        suggestions_text = " ".join(suggestions).lower()
        assert "debt" in suggestions_text or "reduce" in suggestions_text
    
    def test_suggestions_limited_to_three(self):
        """Phase 4D Explainability - Maximum 3 suggestions returned."""
        service = ExplainabilityService()
        
        # Create many negative contributions
        contribs = [
            FeatureContribution(
                feature_name=f"feature_{i}",
                human_name=f"Feature {i}",
                shap_value=0.1,
                feature_value=100,
                impact="negative",
                magnitude="medium",
                explanation=f"Issue {i}"
            )
            for i in range(10)
        ]
        
        suggestions = service.generate_improvement_suggestions(contribs, "high")
        
        assert len(suggestions) <= 3


class TestCompleteExplanation:
    """Test complete explanation generation."""
    
    def test_explanation_structure(self):
        """Phase 4D Explainability - Explanation has all required fields."""
        service = ExplainabilityService()
        
        # Create sample SHAP values
        shap_values = np.array([0.05, -0.10, 0.15, -0.08, 0.02])
        feature_names = ["credit_score", "annual_income", "monthly_debt", "loan_amount", "employment_length_years"]
        feature_values = {
            "credit_score": 720,
            "annual_income": 75000,
            "monthly_debt": 1200,
            "loan_amount": 25000,
            "employment_length_years": 5
        }
        
        result = service.explain_prediction(
            shap_values=shap_values,
            feature_names=feature_names,
            feature_values=feature_values,
            prediction_probability=0.35
        )
        
        # Check structure
        assert isinstance(result, ExplanationResult)
        assert result.risk_band in ["low", "medium", "high"]
        assert len(result.risk_band_description) > 0
        assert isinstance(result.top_positive_features, list)
        assert isinstance(result.top_negative_features, list)
        assert isinstance(result.what_helped, list)
        assert isinstance(result.what_hurt, list)
        assert isinstance(result.how_to_improve, list)
        assert len(result.disclaimer) > 0
    
    def test_explanation_top_features_limited(self):
        """Phase 4D Explainability - Top features limited to 3 each."""
        service = ExplainabilityService()
        
        # Create many features
        shap_values = np.random.randn(20)
        feature_names = [f"feature_{i}" for i in range(20)]
        feature_values = {name: 100 for name in feature_names}
        
        result = service.explain_prediction(
            shap_values=shap_values,
            feature_names=feature_names,
            feature_values=feature_values,
            prediction_probability=0.5
        )
        
        assert len(result.top_positive_features) <= 3
        assert len(result.top_negative_features) <= 3
    
    def test_explanation_consistency(self):
        """Phase 4D Explainability - Same input produces same explanation."""
        service = ExplainabilityService()
        
        shap_values = np.array([0.05, -0.10, 0.15])
        feature_names = ["credit_score", "annual_income", "monthly_debt"]
        feature_values = {
            "credit_score": 720,
            "annual_income": 75000,
            "monthly_debt": 1200
        }
        
        result1 = service.explain_prediction(shap_values, feature_names, feature_values, 0.35)
        result2 = service.explain_prediction(shap_values, feature_names, feature_values, 0.35)
        
        assert result1.risk_band == result2.risk_band
        assert len(result1.top_positive_features) == len(result2.top_positive_features)
        assert len(result1.top_negative_features) == len(result2.top_negative_features)


class TestComplianceDisclaimer:
    """Test compliance disclaimer presence."""
    
    def test_disclaimer_always_present(self):
        """Phase 4D Explainability - Disclaimer is always included."""
        service = ExplainabilityService()
        
        shap_values = np.array([0.1, -0.2])
        feature_names = ["credit_score", "annual_income"]
        feature_values = {"credit_score": 700, "annual_income": 60000}
        
        result = service.explain_prediction(shap_values, feature_names, feature_values, 0.4)
        
        assert len(result.disclaimer) > 0
        assert "advisory" in result.disclaimer.lower()
        assert "not constitute" in result.disclaimer.lower() or "does not" in result.disclaimer.lower()
    
    def test_disclaimer_content(self):
        """Phase 4D Explainability - Disclaimer has required content."""
        service = ExplainabilityService()
        
        disclaimer = service.disclaimer
        
        # Check for key compliance phrases
        assert "advisory" in disclaimer.lower()
        assert "financial advice" in disclaimer.lower()
        assert "not constitute" in disclaimer.lower() or "does not" in disclaimer.lower()


class TestArraySafety:
    """Test safety with edge case inputs."""
    
    def test_empty_shap_values(self):
        """Phase 4D Explainability - Handle empty SHAP values gracefully."""
        service = ExplainabilityService()
        
        shap_values = np.array([])
        feature_names = []
        feature_values = {}
        
        result = service.explain_prediction(shap_values, feature_names, feature_values, 0.5)
        
        # Should still return valid structure
        assert isinstance(result, ExplanationResult)
        assert result.what_helped == ["Overall financial profile is stable"]
        assert result.what_hurt == ["No significant risk factors identified"]
    
    def test_single_feature(self):
        """Phase 4D Explainability - Handle single feature correctly."""
        service = ExplainabilityService()
        
        shap_values = np.array([0.15])
        feature_names = ["credit_score"]
        feature_values = {"credit_score": 650}
        
        result = service.explain_prediction(shap_values, feature_names, feature_values, 0.6)
        
        assert isinstance(result, ExplanationResult)
        assert result.risk_band == "high"
