"""Decision Policy Engine for Credit Risk Assessment.

Phase 4B: Business Logic Layer

This module converts ML predictions and SHAP explanations into actionable
credit decisions using industry-standard policy rules and safety overrides.

Core Principle:
    Prediction ≠ Decision
    ML informs decisions — policies CONTROL decisions.

Decision Flow:
    1. Assess risk tier based on probability of default (PD)
    2. Apply base decision mapping
    3. Apply mandatory overrides (confidence, explanations)
    4. Generate human-readable reasons
    5. Return structured decision

This engine is:
- Auditable: All decisions logged with reasoning
- Safe: Never auto-rejects without high confidence
- Explainable: Non-technical decision reasons
- Deterministic: Same inputs → same outputs
"""

from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# POLICY CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

class PolicyThresholds:
    """Centralized policy thresholds for credit decisions.
    
    All threshold values are configured here to avoid magic numbers
    scattered across the codebase.
    """
    
    # Risk tier thresholds based on probability of default (PD)
    LOW_RISK_THRESHOLD: float = 0.30
    MEDIUM_RISK_THRESHOLD: float = 0.60
    
    # Strong negative factor threshold for risk escalation
    # If >= this many risk factors, escalate risk tier by one level
    STRONG_NEGATIVE_FACTORS_THRESHOLD: int = 3
    
    # Minimum impact percentage to consider a factor "strong"
    STRONG_FACTOR_IMPACT_THRESHOLD: float = 15.0


# ═══════════════════════════════════════════════════════════════════════
# DECISION SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class CreditDecision(BaseModel):
    """Structured credit decision output."""
    
    decision: Literal["APPROVE", "REVIEW", "REJECT"] = Field(
        description="Final credit decision"
    )
    
    risk_tier: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Assessed risk tier"
    )
    
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Decision confidence level"
    )
    
    decision_reason: str = Field(
        description="Human-readable explanation (non-technical)"
    )
    
    recommended_action: str = Field(
        description="Suggested next steps for this decision"
    )
    
    probability_of_default: float = Field(
        description="Raw model prediction (for audit trail)",
        ge=0.0,
        le=1.0
    )
    
    override_applied: bool = Field(
        default=False,
        description="Whether policy override changed the decision"
    )
    
    override_reason: Optional[str] = Field(
        default=None,
        description="Reason for override (if applied)"
    )


# ═══════════════════════════════════════════════════════════════════════
# DECISION ENGINE
# ═══════════════════════════════════════════════════════════════════════

class DecisionPolicyEngine:
    """Industry-grade decision policy engine for credit risk.
    
    This engine applies business rules on top of ML predictions to produce
    final credit decisions suitable for real-world fintech/banking systems.
    
    Features:
    - Risk-based decision mapping
    - Confidence-based overrides
    - Explanation-driven escalation
    - Human-readable reasons
    - Full audit trail
    """
    
    def __init__(self):
        """Initialize decision policy engine."""
        self.thresholds = PolicyThresholds()
    
    def make_decision(
        self,
        probability_of_default: float,
        model_confidence: Literal["HIGH", "MEDIUM", "LOW"],
        explanation_summary: Optional[Dict[str, Any]] = None
    ) -> CreditDecision:
        """Make credit decision based on ML prediction and explanations.
        
        Args:
            probability_of_default: Model's predicted PD (0.0-1.0)
            model_confidence: Model's confidence level
            explanation_summary: SHAP explanation with top factors
            
        Returns:
            CreditDecision with final decision and reasoning
        """
        logger.info(
            "decision_request",
            pd=probability_of_default,
            confidence=model_confidence,
            has_explanations=explanation_summary is not None
        )
        
        # STEP 1: Assess base risk tier
        base_risk_tier = self._assess_risk_tier(probability_of_default)
        
        # STEP 2: Check for risk escalation based on explanations
        risk_tier, escalated = self._apply_risk_escalation(
            base_risk_tier,
            explanation_summary
        )
        
        # STEP 3: Make base decision
        base_decision = self._map_risk_to_decision(risk_tier, model_confidence)
        
        # STEP 4: Apply mandatory overrides
        final_decision, override_applied, override_reason = self._apply_overrides(
            base_decision=base_decision,
            model_confidence=model_confidence,
            explanation_summary=explanation_summary,
            probability_of_default=probability_of_default
        )
        
        # STEP 5: Generate human-readable reason
        decision_reason = self._generate_decision_reason(
            decision=final_decision,
            risk_tier=risk_tier,
            probability_of_default=probability_of_default,
            model_confidence=model_confidence,
            explanation_summary=explanation_summary,
            override_applied=override_applied
        )
        
        # STEP 6: Generate recommended action
        recommended_action = self._generate_recommended_action(
            decision=final_decision,
            risk_tier=risk_tier,
            model_confidence=model_confidence
        )
        
        # Build final decision object
        credit_decision = CreditDecision(
            decision=final_decision,
            risk_tier=risk_tier,
            confidence=model_confidence,
            decision_reason=decision_reason,
            recommended_action=recommended_action,
            probability_of_default=probability_of_default,
            override_applied=override_applied,
            override_reason=override_reason
        )
        
        # Log decision for audit
        self._log_decision(credit_decision, escalated)
        
        return credit_decision
    
    def _assess_risk_tier(self, probability_of_default: float) -> Literal["LOW", "MEDIUM", "HIGH"]:
        """Assess risk tier based on probability of default.
        
        Thresholds:
        - PD < 0.30 → LOW
        - 0.30 ≤ PD < 0.60 → MEDIUM
        - PD ≥ 0.60 → HIGH
        
        Args:
            probability_of_default: Model's predicted PD
            
        Returns:
            Risk tier
        """
        if probability_of_default < self.thresholds.LOW_RISK_THRESHOLD:
            return "LOW"
        elif probability_of_default < self.thresholds.MEDIUM_RISK_THRESHOLD:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _apply_risk_escalation(
        self,
        base_risk_tier: Literal["LOW", "MEDIUM", "HIGH"],
        explanation_summary: Optional[Dict[str, Any]]
    ) -> tuple[Literal["LOW", "MEDIUM", "HIGH"], bool]:
        """Apply risk escalation based on explanation analysis.
        
        Override Rule:
        If ≥ 3 strong negative risk drivers (impact ≥ 15%), escalate risk tier.
        
        Args:
            base_risk_tier: Initial risk tier from PD
            explanation_summary: SHAP explanation data
            
        Returns:
            Tuple of (final_risk_tier, was_escalated)
        """
        if not explanation_summary or "top_risk_factors" not in explanation_summary:
            return base_risk_tier, False
        
        # Count strong risk factors
        strong_factors = [
            factor for factor in explanation_summary.get("top_risk_factors", [])
            if factor.get("impact_percentage", 0) >= self.thresholds.STRONG_FACTOR_IMPACT_THRESHOLD
        ]
        
        if len(strong_factors) >= self.thresholds.STRONG_NEGATIVE_FACTORS_THRESHOLD:
            # Escalate by one tier
            if base_risk_tier == "LOW":
                logger.info("risk_escalation", from_tier="LOW", to_tier="MEDIUM", reason="strong_risk_factors")
                return "MEDIUM", True
            elif base_risk_tier == "MEDIUM":
                logger.info("risk_escalation", from_tier="MEDIUM", to_tier="HIGH", reason="strong_risk_factors")
                return "HIGH", True
        
        return base_risk_tier, False
    
    def _map_risk_to_decision(
        self,
        risk_tier: Literal["LOW", "MEDIUM", "HIGH"],
        model_confidence: Literal["HIGH", "MEDIUM", "LOW"]
    ) -> Literal["APPROVE", "REVIEW", "REJECT"]:
        """Map risk tier and confidence to base decision.
        
        Rules:
        - LOW risk + HIGH/MEDIUM confidence → APPROVE
        - LOW risk + LOW confidence → REJECT (unsafe to approve)
        - MEDIUM risk → REVIEW
        - HIGH risk → REJECT
        
        Args:
            risk_tier: Assessed risk tier
            model_confidence: Model confidence level
            
        Returns:
            Base decision (before overrides)
        """
        if risk_tier == "LOW":
            if model_confidence in ["HIGH", "MEDIUM"]:
                return "APPROVE"
            else:
                # LOW confidence with LOW risk → don't auto-approve
                return "REJECT"
        elif risk_tier == "MEDIUM":
            return "REVIEW"
        else:  # HIGH risk
            return "REJECT"
    
    def _apply_overrides(
        self,
        base_decision: Literal["APPROVE", "REVIEW", "REJECT"],
        model_confidence: Literal["HIGH", "MEDIUM", "LOW"],
        explanation_summary: Optional[Dict[str, Any]],
        probability_of_default: float
    ) -> tuple[Literal["APPROVE", "REVIEW", "REJECT"], bool, Optional[str]]:
        """Apply mandatory policy overrides.
        
        Override Rules:
        1. If confidence == LOW → force REVIEW
        2. If explanations missing/empty → force REVIEW
        3. Never auto-reject without explanations
        
        Args:
            base_decision: Decision before overrides
            model_confidence: Model confidence
            explanation_summary: SHAP explanations
            probability_of_default: Raw PD value
            
        Returns:
            Tuple of (final_decision, override_applied, override_reason)
        """
        # Override 1: Low confidence always requires review
        if model_confidence == "LOW":
            if base_decision != "REVIEW":
                logger.warning(
                    "override_low_confidence",
                    base_decision=base_decision,
                    final_decision="REVIEW"
                )
                return "REVIEW", True, "Insufficient model confidence for automated decision"
        
        # Override 2: Missing explanations require review
        if not explanation_summary or not explanation_summary.get("top_risk_factors"):
            if base_decision in ["APPROVE", "REJECT"]:
                logger.warning(
                    "override_missing_explanations",
                    base_decision=base_decision,
                    final_decision="REVIEW"
                )
                return "REVIEW", True, "Explanations unavailable - manual review required"
        
        # Override 3: Never auto-reject without high confidence and explanations
        if base_decision == "REJECT":
            if model_confidence != "HIGH" or not explanation_summary:
                logger.warning(
                    "override_unsafe_reject",
                    base_decision="REJECT",
                    final_decision="REVIEW",
                    confidence=model_confidence
                )
                return "REVIEW", True, "High-risk decision requires manual review for safety"
        
        return base_decision, False, None
    
    def _generate_decision_reason(
        self,
        decision: Literal["APPROVE", "REVIEW", "REJECT"],
        risk_tier: Literal["LOW", "MEDIUM", "HIGH"],
        probability_of_default: float,
        model_confidence: Literal["HIGH", "MEDIUM", "LOW"],
        explanation_summary: Optional[Dict[str, Any]],
        override_applied: bool
    ) -> str:
        """Generate human-readable decision reason.
        
        Rules:
        - No ML jargon (SHAP, logits, probabilities)
        - Professional, non-technical language
        - Clear and actionable
        
        Args:
            decision: Final decision
            risk_tier: Risk tier
            probability_of_default: Raw PD
            model_confidence: Confidence level
            explanation_summary: SHAP data
            override_applied: Whether override changed decision
            
        Returns:
            Human-readable reason string
        """
        # Extract key risk factors if available
        top_factor = None
        if explanation_summary and explanation_summary.get("top_risk_factors"):
            factors = explanation_summary["top_risk_factors"]
            if factors:
                top_factor = factors[0].get("feature", "").lower()
        
        # Generate reason based on decision type
        if decision == "APPROVE":
            if risk_tier == "LOW":
                if top_factor:
                    return f"Low predicted default risk with stable financial profile. Application shows strong indicators across credit metrics."
                else:
                    return "Low predicted default risk with stable financial indicators."
            else:
                return "Approved with conditions. Financial profile meets minimum requirements but may require monitoring."
        
        elif decision == "REVIEW":
            if override_applied:
                if model_confidence == "LOW":
                    return "Manual review required due to insufficient model confidence. Additional verification needed."
                else:
                    return "Manual review required for safety validation. Decision requires human oversight."
            
            if risk_tier == "MEDIUM":
                if top_factor and "debt" in top_factor:
                    return "Moderate risk detected due to elevated debt levels. Manual review recommended for assessment."
                elif top_factor and "credit" in top_factor:
                    return "Moderate risk indicated by credit utilization patterns. Manual review recommended."
                elif top_factor and "delinquenc" in top_factor:
                    return "Moderate risk due to payment history concerns. Manual review recommended."
                else:
                    return "Moderate risk profile requires manual assessment. Additional documentation may be needed."
            else:
                return "Application requires detailed manual review due to risk indicators."
        
        else:  # REJECT
            if risk_tier == "HIGH":
                if top_factor and "delinquenc" in top_factor:
                    return "High default probability driven by recent payment delinquencies. Application does not meet approval criteria."
                elif top_factor and "debt" in top_factor:
                    return "High default risk indicated by elevated debt-to-income ratio. Unable to approve at this time."
                elif top_factor and "credit" in top_factor:
                    return "High risk assessment based on credit profile. Application does not meet current lending standards."
                else:
                    return "High default probability based on financial risk assessment. Application does not meet approval criteria."
            else:
                return "Application does not meet minimum approval requirements at this time."
    
    def _generate_recommended_action(
        self,
        decision: Literal["APPROVE", "REVIEW", "REJECT"],
        risk_tier: Literal["LOW", "MEDIUM", "HIGH"],
        model_confidence: Literal["HIGH", "MEDIUM", "LOW"]
    ) -> str:
        """Generate recommended next action.
        
        Args:
            decision: Final decision
            risk_tier: Risk tier
            model_confidence: Confidence level
            
        Returns:
            Recommended action string
        """
        if decision == "APPROVE":
            return "Proceed with standard loan processing and documentation."
        
        elif decision == "REVIEW":
            if model_confidence == "LOW":
                return "Route to senior underwriter for detailed assessment. Request additional documentation."
            elif risk_tier == "MEDIUM":
                return "Route to underwriter for manual review. May require income verification or collateral assessment."
            else:
                return "Escalate to senior credit analyst for comprehensive risk evaluation."
        
        else:  # REJECT
            return "Issue decline notice with reason. Provide information on reapplication criteria and timeline."
    
    def _log_decision(self, decision: CreditDecision, risk_escalated: bool) -> None:
        """Log decision for audit trail.
        
        Special logging for REJECT decisions as required by governance.
        
        Args:
            decision: Final credit decision
            risk_escalated: Whether risk tier was escalated
        """
        log_data = {
            "decision": decision.decision,
            "risk_tier": decision.risk_tier,
            "confidence": decision.confidence,
            "probability_of_default": decision.probability_of_default,
            "override_applied": decision.override_applied,
            "risk_escalated": risk_escalated
        }
        
        if decision.decision == "REJECT":
            # Enhanced logging for rejections (governance requirement)
            logger.warning(
                "credit_decision_reject",
                **log_data,
                decision_reason=decision.decision_reason,
                override_reason=decision.override_reason
            )
        else:
            logger.info(
                "credit_decision_made",
                **log_data
            )


# ═══════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════

_decision_engine: Optional[DecisionPolicyEngine] = None


def get_decision_engine() -> DecisionPolicyEngine:
    """Get global decision engine instance.
    
    Returns:
        Singleton DecisionPolicyEngine instance
    """
    global _decision_engine
    
    if _decision_engine is None:
        _decision_engine = DecisionPolicyEngine()
        logger.info("decision_engine_initialized")
    
    return _decision_engine
