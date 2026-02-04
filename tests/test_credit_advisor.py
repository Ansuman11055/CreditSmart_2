"""Tests for Credit Advisor Engine.

Phase 4C: AI Credit Advisor Testing

Test Coverage:
- Tone correctness per decision type
- Action relevance and quality
- No ML jargon leakage
- Feature name translation
- Deterministic behavior
- Graceful fallback when data missing
- Safety and governance rules
"""

import pytest
from app.services.credit_advisor import (
    CreditAdvisorEngine,
    CreditAdvice,
    FEATURE_TRANSLATION_MAP
)


# ═══════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def advisor():
    """Create fresh credit advisor for each test."""
    return CreditAdvisorEngine()


@pytest.fixture
def mock_explanations_debt_heavy():
    """Mock explanations for high debt scenario."""
    return {
        "top_risk_factors": [
            {"feature": "Debt-to-Income Ratio", "impact": 0.20, "impact_percentage": 30.0, "direction": "increase"},
            {"feature": "Monthly Debt", "impact": 0.15, "impact_percentage": 22.0, "direction": "increase"},
            {"feature": "Credit Utilization", "impact": 0.12, "impact_percentage": 18.0, "direction": "increase"}
        ],
        "top_protective_factors": []
    }


@pytest.fixture
def mock_explanations_delinquency():
    """Mock explanations for delinquency scenario."""
    return {
        "top_risk_factors": [
            {"feature": "Recent Delinquencies", "impact": 0.25, "impact_percentage": 35.0, "direction": "increase"},
            {"feature": "Credit Score", "impact": 0.18, "impact_percentage": 25.0, "direction": "increase"}
        ],
        "top_protective_factors": []
    }


@pytest.fixture
def mock_explanations_low_risk():
    """Mock explanations for low risk scenario."""
    return {
        "top_risk_factors": [
            {"feature": "Loan Amount", "impact": 0.05, "impact_percentage": 12.0, "direction": "increase"}
        ],
        "top_protective_factors": [
            {"feature": "Credit Score", "impact": -0.15, "impact_percentage": 30.0, "direction": "decrease"},
            {"feature": "Annual Income", "impact": -0.12, "impact_percentage": 25.0, "direction": "decrease"}
        ]
    }


@pytest.fixture
def mock_explanations_empty():
    """Mock empty explanations."""
    return {
        "top_risk_factors": [],
        "top_protective_factors": []
    }


# ═══════════════════════════════════════════════════════════════════════
# TEST: TONE CORRECTNESS
# ═══════════════════════════════════════════════════════════════════════

def test_tone_approve(advisor):
    """Test APPROVE decision produces POSITIVE tone."""
    tone = advisor._determine_tone("APPROVE")
    assert tone == "POSITIVE"


def test_tone_review(advisor):
    """Test REVIEW decision produces NEUTRAL tone."""
    tone = advisor._determine_tone("REVIEW")
    assert tone == "NEUTRAL"


def test_tone_reject(advisor):
    """Test REJECT decision produces CAUTIONARY tone."""
    tone = advisor._determine_tone("REJECT")
    assert tone == "CAUTIONARY"


# ═══════════════════════════════════════════════════════════════════════
# TEST: NO ML JARGON
# ═══════════════════════════════════════════════════════════════════════

def test_no_shap_jargon(advisor, mock_explanations_debt_heavy):
    """Test that SHAP is never mentioned in advice."""
    advice = advisor.generate_advice(
        decision="REJECT",
        risk_tier="HIGH",
        explanation_summary=mock_explanations_debt_heavy,
        confidence="MEDIUM"
    )
    
    # Check all text fields
    all_text = (
        advice.summary + " " +
        " ".join(advice.key_risk_factors) + " " +
        " ".join(advice.recommended_actions) + " " +
        (advice.next_steps or "")
    ).lower()
    
    assert "shap" not in all_text
    assert "probability" not in all_text
    assert "logit" not in all_text
    assert "feature" not in all_text
    assert "model" not in all_text


def test_no_technical_terms(advisor, mock_explanations_debt_heavy):
    """Test that technical ML terms are not exposed."""
    advice = advisor.generate_advice(
        decision="APPROVE",
        risk_tier="LOW",
        explanation_summary=mock_explanations_debt_heavy,
        confidence="HIGH"
    )
    
    all_text = (
        advice.summary + " " +
        " ".join(advice.key_risk_factors) + " " +
        " ".join(advice.recommended_actions)
    ).lower()
    
    # Should not contain technical terms
    assert "prediction" not in all_text
    assert "inference" not in all_text
    assert "algorithm" not in all_text
    assert "machine learning" not in all_text


# ═══════════════════════════════════════════════════════════════════════
# TEST: FEATURE NAME TRANSLATION
# ═══════════════════════════════════════════════════════════════════════

def test_translate_debt_features(advisor):
    """Test debt-related features are translated."""
    translated = advisor._translate_feature_name("debt-to-income ratio")
    assert "debt" in translated.lower()
    assert "income" in translated.lower()


def test_translate_delinquency_features(advisor):
    """Test delinquency features are translated."""
    translated = advisor._translate_feature_name("recent delinquencies")
    assert "payment" in translated.lower() or "delinquenc" in translated.lower()


def test_translate_unknown_feature(advisor):
    """Test unknown features are cleaned up."""
    translated = advisor._translate_feature_name("some_unknown_feature")
    # Should not contain underscores
    assert "_" not in translated
    # Should be capitalized
    assert translated[0].isupper()


# ═══════════════════════════════════════════════════════════════════════
# TEST: ACTION GENERATION
# ═══════════════════════════════════════════════════════════════════════

def test_actions_debt_related(advisor, mock_explanations_debt_heavy):
    """Test debt-heavy scenario generates debt-related actions."""
    advice = advisor.generate_advice(
        decision="REJECT",
        risk_tier="HIGH",
        explanation_summary=mock_explanations_debt_heavy,
        confidence="MEDIUM"
    )
    
    actions_text = " ".join(advice.recommended_actions).lower()
    
    # Should mention debt or balances
    assert "debt" in actions_text or "balance" in actions_text


def test_actions_delinquency_related(advisor, mock_explanations_delinquency):
    """Test delinquency scenario generates payment-related actions."""
    advice = advisor.generate_advice(
        decision="REJECT",
        risk_tier="HIGH",
        explanation_summary=mock_explanations_delinquency,
        confidence="MEDIUM"
    )
    
    actions_text = " ".join(advice.recommended_actions).lower()
    
    # Should mention payments or on-time
    assert "payment" in actions_text or "on-time" in actions_text or "on time" in actions_text


def test_actions_max_four(advisor, mock_explanations_debt_heavy):
    """Test maximum 4 actions are returned."""
    advice = advisor.generate_advice(
        decision="REJECT",
        risk_tier="HIGH",
        explanation_summary=mock_explanations_debt_heavy,
        confidence="MEDIUM"
    )
    
    assert len(advice.recommended_actions) <= 4


def test_actions_are_actionable(advisor, mock_explanations_debt_heavy):
    """Test actions are specific and actionable."""
    advice = advisor.generate_advice(
        decision="REVIEW",
        risk_tier="MEDIUM",
        explanation_summary=mock_explanations_debt_heavy,
        confidence="MEDIUM"
    )
    
    # Each action should be a complete sentence
    for action in advice.recommended_actions:
        assert len(action) > 20  # Substantial advice
        assert action[-1] == "."  # Proper punctuation


# ═══════════════════════════════════════════════════════════════════════
# TEST: SUMMARY GENERATION
# ═══════════════════════════════════════════════════════════════════════

def test_summary_approve_positive(advisor):
    """Test APPROVE summary is positive and encouraging."""
    summary = advisor._generate_summary(
        decision="APPROVE",
        risk_tier="LOW",
        confidence="HIGH",
        override_applied=False
    )
    
    summary_lower = summary.lower()
    
    # Should be positive
    assert any(word in summary_lower for word in ["strong", "well-positioned", "positive", "good"])
    # Should not be negative
    assert not any(word in summary_lower for word in ["poor", "bad", "weak"])


def test_summary_reject_cautionary_not_shaming(advisor):
    """Test REJECT summary is cautionary but not shaming."""
    summary = advisor._generate_summary(
        decision="REJECT",
        risk_tier="HIGH",
        confidence="HIGH",
        override_applied=False
    )
    
    summary_lower = summary.lower()
    
    # Should emphasize improvement
    assert "improve" in summary_lower or "strengthen" in summary_lower or "action" in summary_lower
    # Should not shame
    assert "bad" not in summary_lower
    assert "poor" not in summary_lower
    assert "failure" not in summary_lower


def test_summary_review_neutral(advisor):
    """Test REVIEW summary is neutral and fair."""
    summary = advisor._generate_summary(
        decision="REVIEW",
        risk_tier="MEDIUM",
        confidence="MEDIUM",
        override_applied=False
    )
    
    summary_lower = summary.lower()
    
    # Should mention review or evaluation
    assert "review" in summary_lower or "evaluation" in summary_lower or "assessment" in summary_lower


# ═══════════════════════════════════════════════════════════════════════
# TEST: KEY RISK FACTORS EXTRACTION
# ═══════════════════════════════════════════════════════════════════════

def test_extract_key_factors_translates(advisor, mock_explanations_debt_heavy):
    """Test key factors are translated to plain English."""
    factors = advisor._extract_key_factors(mock_explanations_debt_heavy)
    
    assert len(factors) > 0
    
    # Should not contain raw feature names with underscores
    for factor in factors:
        assert "_" not in factor or ":" in factor  # Allow "Purpose: ..." format


def test_extract_key_factors_max_four(advisor, mock_explanations_debt_heavy):
    """Test maximum 4 key factors are returned."""
    factors = advisor._extract_key_factors(mock_explanations_debt_heavy)
    
    assert len(factors) <= 4


def test_extract_key_factors_graceful_fallback(advisor):
    """Test graceful fallback when explanations missing."""
    factors = advisor._extract_key_factors(None)
    
    assert len(factors) > 0  # Should still return something
    assert isinstance(factors[0], str)


# ═══════════════════════════════════════════════════════════════════════
# TEST: NEXT STEPS GENERATION
# ═══════════════════════════════════════════════════════════════════════

def test_next_steps_approve(advisor):
    """Test APPROVE next steps are clear."""
    next_steps = advisor._generate_next_steps(
        decision="APPROVE",
        override_applied=False,
        confidence="HIGH"
    )
    
    assert "proceed" in next_steps.lower() or "next" in next_steps.lower()


def test_next_steps_review(advisor):
    """Test REVIEW next steps mention review process."""
    next_steps = advisor._generate_next_steps(
        decision="REVIEW",
        override_applied=False,
        confidence="MEDIUM"
    )
    
    assert "review" in next_steps.lower()
    assert "days" in next_steps.lower()  # Should give timeframe


def test_next_steps_reject(advisor):
    """Test REJECT next steps offer reapplication path."""
    next_steps = advisor._generate_next_steps(
        decision="REJECT",
        override_applied=False,
        confidence="HIGH"
    )
    
    assert "reapply" in next_steps.lower() or "future" in next_steps.lower()


# ═══════════════════════════════════════════════════════════════════════
# TEST: END-TO-END ADVICE GENERATION
# ═══════════════════════════════════════════════════════════════════════

def test_e2e_approve_low_risk(advisor, mock_explanations_low_risk):
    """Test end-to-end advice for APPROVE decision."""
    advice = advisor.generate_advice(
        decision="APPROVE",
        risk_tier="LOW",
        explanation_summary=mock_explanations_low_risk,
        confidence="HIGH",
        override_applied=False
    )
    
    assert advice.user_tone == "POSITIVE"
    assert len(advice.summary) > 50
    assert len(advice.key_risk_factors) > 0
    assert len(advice.recommended_actions) > 0
    assert advice.next_steps is not None


def test_e2e_reject_high_risk(advisor, mock_explanations_delinquency):
    """Test end-to-end advice for REJECT decision."""
    advice = advisor.generate_advice(
        decision="REJECT",
        risk_tier="HIGH",
        explanation_summary=mock_explanations_delinquency,
        confidence="HIGH",
        override_applied=False
    )
    
    assert advice.user_tone == "CAUTIONARY"
    assert "improve" in advice.summary.lower() or "action" in advice.summary.lower()
    assert len(advice.recommended_actions) > 0
    # Should have payment-related actions
    actions_text = " ".join(advice.recommended_actions).lower()
    assert "payment" in actions_text or "delinquenc" in actions_text


def test_e2e_review_medium_risk(advisor, mock_explanations_debt_heavy):
    """Test end-to-end advice for REVIEW decision."""
    advice = advisor.generate_advice(
        decision="REVIEW",
        risk_tier="MEDIUM",
        explanation_summary=mock_explanations_debt_heavy,
        confidence="MEDIUM",
        override_applied=False
    )
    
    assert advice.user_tone == "NEUTRAL"
    assert "review" in advice.summary.lower()
    assert len(advice.recommended_actions) > 0


def test_e2e_low_confidence_override(advisor, mock_explanations_low_risk):
    """Test advice when LOW confidence override is applied."""
    advice = advisor.generate_advice(
        decision="REVIEW",
        risk_tier="LOW",
        explanation_summary=mock_explanations_low_risk,
        confidence="LOW",
        override_applied=True
    )
    
    # Should mention manual review or additional assessment
    combined_text = (advice.summary + " " + " ".join(advice.recommended_actions)).lower()
    assert "review" in combined_text or "additional" in combined_text


# ═══════════════════════════════════════════════════════════════════════
# TEST: DETERMINISM
# ═══════════════════════════════════════════════════════════════════════

def test_deterministic_advice(advisor, mock_explanations_debt_heavy):
    """Test same inputs produce same advice."""
    advice1 = advisor.generate_advice(
        decision="REVIEW",
        risk_tier="MEDIUM",
        explanation_summary=mock_explanations_debt_heavy,
        confidence="MEDIUM"
    )
    
    advice2 = advisor.generate_advice(
        decision="REVIEW",
        risk_tier="MEDIUM",
        explanation_summary=mock_explanations_debt_heavy,
        confidence="MEDIUM"
    )
    
    assert advice1.summary == advice2.summary
    assert advice1.key_risk_factors == advice2.key_risk_factors
    assert advice1.recommended_actions == advice2.recommended_actions
    assert advice1.user_tone == advice2.user_tone


# ═══════════════════════════════════════════════════════════════════════
# TEST: SAFETY & GOVERNANCE
# ═══════════════════════════════════════════════════════════════════════

def test_no_financial_guarantees(advisor, mock_explanations_debt_heavy):
    """Test advice does not make financial guarantees."""
    advice = advisor.generate_advice(
        decision="REJECT",
        risk_tier="HIGH",
        explanation_summary=mock_explanations_debt_heavy,
        confidence="MEDIUM"
    )
    
    all_text = (
        advice.summary + " " +
        " ".join(advice.recommended_actions)
    ).lower()
    
    # Should not guarantee approval
    assert "guarantee" not in all_text
    assert "will be approved" not in all_text
    assert "will approve" not in all_text


def test_graceful_degradation_missing_explanations(advisor):
    """Test advisor works even without explanations."""
    advice = advisor.generate_advice(
        decision="REVIEW",
        risk_tier="MEDIUM",
        explanation_summary=None,
        confidence="MEDIUM"
    )
    
    # Should still provide useful advice
    assert len(advice.summary) > 50
    assert len(advice.recommended_actions) > 0
    assert advice.user_tone == "NEUTRAL"


def test_graceful_degradation_empty_explanations(advisor, mock_explanations_empty):
    """Test advisor works with empty explanation data."""
    advice = advisor.generate_advice(
        decision="REVIEW",
        risk_tier="MEDIUM",
        explanation_summary=mock_explanations_empty,
        confidence="MEDIUM"
    )
    
    # Should still provide useful advice
    assert len(advice.summary) > 50
    assert len(advice.recommended_actions) > 0


# ═══════════════════════════════════════════════════════════════════════
# TEST: PROFESSIONAL TONE
# ═══════════════════════════════════════════════════════════════════════

def test_professional_language(advisor, mock_explanations_debt_heavy):
    """Test advice uses professional, respectful language."""
    advice = advisor.generate_advice(
        decision="REJECT",
        risk_tier="HIGH",
        explanation_summary=mock_explanations_debt_heavy,
        confidence="HIGH"
    )
    
    all_text = advice.summary + " " + " ".join(advice.recommended_actions)
    
    # Should be professional
    assert len(all_text) > 100  # Substantial content
    # Should have proper capitalization and punctuation
    assert all_text[0].isupper()
    assert "." in all_text


def test_no_negative_language(advisor, mock_explanations_delinquency):
    """Test advice avoids negative or shaming language."""
    advice = advisor.generate_advice(
        decision="REJECT",
        risk_tier="HIGH",
        explanation_summary=mock_explanations_delinquency,
        confidence="HIGH"
    )
    
    all_text = (
        advice.summary + " " +
        " ".join(advice.key_risk_factors) + " " +
        " ".join(advice.recommended_actions)
    ).lower()
    
    # Should not use negative terms
    assert "bad credit" not in all_text
    assert "poor credit" not in all_text
    assert "terrible" not in all_text
    assert "awful" not in all_text
