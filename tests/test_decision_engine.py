"""Tests for Decision Policy Engine.

Phase 4B: Decision Engine Testing

Test Coverage:
- Risk tier assessment correctness
- Decision mapping logic
- Override rule application
- Risk escalation based on explanations
- Human-readable reason generation
- Deterministic behavior
- Edge cases and boundary conditions
"""

import pytest
from app.services.decision_engine import (
    DecisionPolicyEngine,
    PolicyThresholds,
    CreditDecision
)


# ═══════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def engine():
    """Create fresh decision engine for each test."""
    return DecisionPolicyEngine()


@pytest.fixture
def mock_explanations_low_risk():
    """Mock explanations for low risk case."""
    return {
        "top_risk_factors": [
            {"feature": "Monthly Debt", "impact": 0.05, "impact_percentage": 10.0, "direction": "increase"}
        ],
        "top_protective_factors": [
            {"feature": "Credit Score", "impact": -0.15, "impact_percentage": 30.0, "direction": "decrease"},
            {"feature": "Annual Income", "impact": -0.12, "impact_percentage": 25.0, "direction": "decrease"}
        ]
    }


@pytest.fixture
def mock_explanations_high_risk():
    """Mock explanations for high risk case with strong negative factors."""
    return {
        "top_risk_factors": [
            {"feature": "Recent Delinquencies", "impact": 0.20, "impact_percentage": 25.0, "direction": "increase"},
            {"feature": "Debt-to-Income Ratio", "impact": 0.18, "impact_percentage": 22.0, "direction": "increase"},
            {"feature": "Credit Inquiries", "impact": 0.15, "impact_percentage": 18.0, "direction": "increase"}
        ],
        "top_protective_factors": []
    }


@pytest.fixture
def mock_explanations_empty():
    """Mock empty explanations."""
    return {
        "top_risk_factors": [],
        "top_protective_factors": []
    }


# ═══════════════════════════════════════════════════════════════════════
# TEST: RISK TIER ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════

def test_risk_tier_low(engine):
    """Test risk tier assessment for low risk."""
    assert engine._assess_risk_tier(0.10) == "LOW"
    assert engine._assess_risk_tier(0.29) == "LOW"


def test_risk_tier_medium(engine):
    """Test risk tier assessment for medium risk."""
    assert engine._assess_risk_tier(0.30) == "MEDIUM"
    assert engine._assess_risk_tier(0.45) == "MEDIUM"
    assert engine._assess_risk_tier(0.59) == "MEDIUM"


def test_risk_tier_high(engine):
    """Test risk tier assessment for high risk."""
    assert engine._assess_risk_tier(0.60) == "HIGH"
    assert engine._assess_risk_tier(0.75) == "HIGH"
    assert engine._assess_risk_tier(0.99) == "HIGH"


def test_risk_tier_boundaries(engine):
    """Test exact boundary values."""
    thresholds = PolicyThresholds()
    
    # Just below LOW threshold
    assert engine._assess_risk_tier(thresholds.LOW_RISK_THRESHOLD - 0.001) == "LOW"
    
    # Exactly at LOW threshold
    assert engine._assess_risk_tier(thresholds.LOW_RISK_THRESHOLD) == "MEDIUM"
    
    # Just below MEDIUM threshold
    assert engine._assess_risk_tier(thresholds.MEDIUM_RISK_THRESHOLD - 0.001) == "MEDIUM"
    
    # Exactly at MEDIUM threshold
    assert engine._assess_risk_tier(thresholds.MEDIUM_RISK_THRESHOLD) == "HIGH"


# ═══════════════════════════════════════════════════════════════════════
# TEST: DECISION MAPPING
# ═══════════════════════════════════════════════════════════════════════

def test_decision_low_risk_high_confidence(engine):
    """Test LOW risk + HIGH confidence → APPROVE."""
    decision = engine._map_risk_to_decision("LOW", "HIGH")
    assert decision == "APPROVE"


def test_decision_low_risk_medium_confidence(engine):
    """Test LOW risk + MEDIUM confidence → APPROVE."""
    decision = engine._map_risk_to_decision("LOW", "MEDIUM")
    assert decision == "APPROVE"


def test_decision_low_risk_low_confidence(engine):
    """Test LOW risk + LOW confidence → REJECT (before override)."""
    # Base decision is REJECT for LOW confidence, but override will force REVIEW
    decision = engine._map_risk_to_decision("LOW", "LOW")
    # With LOW confidence, should not auto-approve
    assert decision == "REJECT"


def test_decision_medium_risk(engine):
    """Test MEDIUM risk always → REVIEW."""
    assert engine._map_risk_to_decision("MEDIUM", "HIGH") == "REVIEW"
    assert engine._map_risk_to_decision("MEDIUM", "MEDIUM") == "REVIEW"
    assert engine._map_risk_to_decision("MEDIUM", "LOW") == "REVIEW"


def test_decision_high_risk(engine):
    """Test HIGH risk → REJECT."""
    assert engine._map_risk_to_decision("HIGH", "HIGH") == "REJECT"
    assert engine._map_risk_to_decision("HIGH", "MEDIUM") == "REJECT"
    assert engine._map_risk_to_decision("HIGH", "LOW") == "REJECT"


# ═══════════════════════════════════════════════════════════════════════
# TEST: OVERRIDE RULES
# ═══════════════════════════════════════════════════════════════════════

def test_override_low_confidence(engine, mock_explanations_low_risk):
    """Test LOW confidence always forces REVIEW."""
    decision, override, reason = engine._apply_overrides(
        base_decision="APPROVE",
        model_confidence="LOW",
        explanation_summary=mock_explanations_low_risk,
        probability_of_default=0.20
    )
    
    assert decision == "REVIEW"
    assert override is True
    assert "confidence" in reason.lower()


def test_override_missing_explanations(engine):
    """Test missing explanations force REVIEW."""
    # Test with None explanations
    decision, override, reason = engine._apply_overrides(
        base_decision="APPROVE",
        model_confidence="HIGH",
        explanation_summary=None,
        probability_of_default=0.20
    )
    
    assert decision == "REVIEW"
    assert override is True
    assert "explanation" in reason.lower()


def test_override_empty_explanations(engine, mock_explanations_empty):
    """Test empty explanations force REVIEW."""
    decision, override, reason = engine._apply_overrides(
        base_decision="APPROVE",
        model_confidence="HIGH",
        explanation_summary=mock_explanations_empty,
        probability_of_default=0.20
    )
    
    assert decision == "REVIEW"
    assert override is True


def test_override_unsafe_reject(engine):
    """Test never auto-reject without high confidence + explanations."""
    # Reject with LOW confidence
    decision, override, reason = engine._apply_overrides(
        base_decision="REJECT",
        model_confidence="LOW",
        explanation_summary=None,
        probability_of_default=0.80
    )
    
    assert decision == "REVIEW"
    assert override is True
    assert "confidence" in reason.lower()


def test_no_override_approve_with_confidence(engine, mock_explanations_low_risk):
    """Test no override when APPROVE is safe."""
    decision, override, reason = engine._apply_overrides(
        base_decision="APPROVE",
        model_confidence="HIGH",
        explanation_summary=mock_explanations_low_risk,
        probability_of_default=0.20
    )
    
    assert decision == "APPROVE"
    assert override is False
    assert reason is None


def test_no_override_reject_with_high_confidence(engine, mock_explanations_high_risk):
    """Test no override for REJECT with HIGH confidence + explanations."""
    decision, override, reason = engine._apply_overrides(
        base_decision="REJECT",
        model_confidence="HIGH",
        explanation_summary=mock_explanations_high_risk,
        probability_of_default=0.80
    )
    
    assert decision == "REJECT"
    assert override is False
    assert reason is None


# ═══════════════════════════════════════════════════════════════════════
# TEST: RISK ESCALATION
# ═══════════════════════════════════════════════════════════════════════

def test_risk_escalation_low_to_medium(engine, mock_explanations_high_risk):
    """Test risk escalation from LOW to MEDIUM with strong factors."""
    risk_tier, escalated = engine._apply_risk_escalation(
        base_risk_tier="LOW",
        explanation_summary=mock_explanations_high_risk
    )
    
    assert risk_tier == "MEDIUM"
    assert escalated is True


def test_risk_escalation_medium_to_high(engine, mock_explanations_high_risk):
    """Test risk escalation from MEDIUM to HIGH with strong factors."""
    risk_tier, escalated = engine._apply_risk_escalation(
        base_risk_tier="MEDIUM",
        explanation_summary=mock_explanations_high_risk
    )
    
    assert risk_tier == "HIGH"
    assert escalated is True


def test_no_risk_escalation_already_high(engine, mock_explanations_high_risk):
    """Test no escalation when already at HIGH tier."""
    risk_tier, escalated = engine._apply_risk_escalation(
        base_risk_tier="HIGH",
        explanation_summary=mock_explanations_high_risk
    )
    
    assert risk_tier == "HIGH"
    assert escalated is False


def test_no_risk_escalation_weak_factors(engine, mock_explanations_low_risk):
    """Test no escalation with weak risk factors."""
    risk_tier, escalated = engine._apply_risk_escalation(
        base_risk_tier="LOW",
        explanation_summary=mock_explanations_low_risk
    )
    
    assert risk_tier == "LOW"
    assert escalated is False


def test_no_risk_escalation_missing_explanations(engine):
    """Test no escalation when explanations missing."""
    risk_tier, escalated = engine._apply_risk_escalation(
        base_risk_tier="LOW",
        explanation_summary=None
    )
    
    assert risk_tier == "LOW"
    assert escalated is False


# ═══════════════════════════════════════════════════════════════════════
# TEST: END-TO-END DECISION FLOW
# ═══════════════════════════════════════════════════════════════════════

def test_e2e_approve_low_risk(engine, mock_explanations_low_risk):
    """Test end-to-end APPROVE decision for low risk."""
    decision = engine.make_decision(
        probability_of_default=0.20,
        model_confidence="HIGH",
        explanation_summary=mock_explanations_low_risk
    )
    
    assert decision.decision == "APPROVE"
    assert decision.risk_tier == "LOW"
    assert decision.confidence == "HIGH"
    assert decision.override_applied is False
    assert "low" in decision.decision_reason.lower()


def test_e2e_review_medium_risk(engine):
    """Test end-to-end REVIEW decision for medium risk."""
    decision = engine.make_decision(
        probability_of_default=0.45,
        model_confidence="MEDIUM",
        explanation_summary={"top_risk_factors": [{"feature": "Debt", "impact": 0.10, "impact_percentage": 12.0}], "top_protective_factors": []}
    )
    
    assert decision.decision == "REVIEW"
    assert decision.risk_tier == "MEDIUM"
    assert decision.confidence == "MEDIUM"


def test_e2e_reject_high_risk(engine, mock_explanations_high_risk):
    """Test end-to-end REJECT decision for high risk."""
    decision = engine.make_decision(
        probability_of_default=0.80,
        model_confidence="HIGH",
        explanation_summary=mock_explanations_high_risk
    )
    
    assert decision.decision == "REJECT"
    assert decision.risk_tier == "HIGH"
    assert decision.confidence == "HIGH"
    assert "high" in decision.decision_reason.lower()


def test_e2e_review_override_low_confidence(engine, mock_explanations_low_risk):
    """Test REVIEW due to LOW confidence override."""
    decision = engine.make_decision(
        probability_of_default=0.20,
        model_confidence="LOW",
        explanation_summary=mock_explanations_low_risk
    )
    
    assert decision.decision == "REVIEW"
    assert decision.override_applied is True
    assert "confidence" in decision.override_reason.lower()


def test_e2e_review_override_missing_explanations(engine):
    """Test REVIEW due to missing explanations override."""
    decision = engine.make_decision(
        probability_of_default=0.20,
        model_confidence="HIGH",
        explanation_summary=None
    )
    
    assert decision.decision == "REVIEW"
    assert decision.override_applied is True
    assert "explanation" in decision.override_reason.lower()


def test_e2e_escalated_risk_tier(engine, mock_explanations_high_risk):
    """Test risk tier escalation affects final decision."""
    # LOW risk PD (0.25) but strong negative factors should escalate to MEDIUM → REVIEW
    decision = engine.make_decision(
        probability_of_default=0.25,
        model_confidence="HIGH",
        explanation_summary=mock_explanations_high_risk
    )
    
    # Risk should escalate from LOW to MEDIUM
    assert decision.risk_tier == "MEDIUM"
    assert decision.decision == "REVIEW"


# ═══════════════════════════════════════════════════════════════════════
# TEST: DECISION REASON GENERATION
# ═══════════════════════════════════════════════════════════════════════

def test_decision_reason_no_ml_jargon(engine, mock_explanations_low_risk):
    """Test decision reasons have no ML jargon."""
    decision = engine.make_decision(
        probability_of_default=0.20,
        model_confidence="HIGH",
        explanation_summary=mock_explanations_low_risk
    )
    
    reason = decision.decision_reason.lower()
    
    # Should NOT contain ML terms
    assert "shap" not in reason
    assert "logit" not in reason
    assert "probability" not in reason
    assert "feature importance" not in reason


def test_decision_reason_professional(engine, mock_explanations_low_risk):
    """Test decision reasons are professional and clear."""
    decision = engine.make_decision(
        probability_of_default=0.20,
        model_confidence="HIGH",
        explanation_summary=mock_explanations_low_risk
    )
    
    reason = decision.decision_reason
    
    # Should be non-empty and professional
    assert len(reason) > 20
    assert reason[0].isupper()  # Starts with capital
    assert "." in reason  # Contains proper punctuation


def test_recommended_action_exists(engine, mock_explanations_low_risk):
    """Test recommended action is always generated."""
    decision = engine.make_decision(
        probability_of_default=0.20,
        model_confidence="HIGH",
        explanation_summary=mock_explanations_low_risk
    )
    
    assert decision.recommended_action
    assert len(decision.recommended_action) > 10


# ═══════════════════════════════════════════════════════════════════════
# TEST: DETERMINISM
# ═══════════════════════════════════════════════════════════════════════

def test_deterministic_decisions(engine, mock_explanations_low_risk):
    """Test same inputs produce same outputs."""
    decision1 = engine.make_decision(
        probability_of_default=0.25,
        model_confidence="HIGH",
        explanation_summary=mock_explanations_low_risk
    )
    
    decision2 = engine.make_decision(
        probability_of_default=0.25,
        model_confidence="HIGH",
        explanation_summary=mock_explanations_low_risk
    )
    
    assert decision1.decision == decision2.decision
    assert decision1.risk_tier == decision2.risk_tier
    assert decision1.confidence == decision2.confidence
    assert decision1.override_applied == decision2.override_applied


# ═══════════════════════════════════════════════════════════════════════
# TEST: EDGE CASES
# ═══════════════════════════════════════════════════════════════════════

def test_edge_case_zero_probability(engine, mock_explanations_low_risk):
    """Test handling of 0.0 probability."""
    decision = engine.make_decision(
        probability_of_default=0.0,
        model_confidence="HIGH",
        explanation_summary=mock_explanations_low_risk
    )
    
    assert decision.decision == "APPROVE"
    assert decision.risk_tier == "LOW"


def test_edge_case_one_probability(engine, mock_explanations_high_risk):
    """Test handling of 1.0 probability."""
    decision = engine.make_decision(
        probability_of_default=1.0,
        model_confidence="HIGH",
        explanation_summary=mock_explanations_high_risk
    )
    
    assert decision.decision == "REJECT"
    assert decision.risk_tier == "HIGH"


def test_edge_case_exact_threshold_values(engine):
    """Test exact threshold boundary values."""
    thresholds = PolicyThresholds()
    
    # Exactly at LOW threshold
    decision = engine.make_decision(
        probability_of_default=thresholds.LOW_RISK_THRESHOLD,
        model_confidence="HIGH",
        explanation_summary={"top_risk_factors": [], "top_protective_factors": []}
    )
    assert decision.risk_tier == "MEDIUM"
    
    # Exactly at MEDIUM threshold
    decision = engine.make_decision(
        probability_of_default=thresholds.MEDIUM_RISK_THRESHOLD,
        model_confidence="HIGH",
        explanation_summary={"top_risk_factors": [], "top_protective_factors": []}
    )
    assert decision.risk_tier == "HIGH"
