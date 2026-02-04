"""AI Credit Advisor - Natural Language Advisory Layer.

Phase 4C: Human-Centered Explainability

This module converts ML predictions and policy decisions into natural-language
advice that helps users understand their credit assessment and provides
actionable steps for improvement.

Core Principles:
- Professional, calm, non-judgmental tone
- No ML jargon (SHAP, probability, features, etc.)
- Action-oriented guidance
- Deterministic (rule-based, no LLM calls)
- Graceful degradation when data is missing

Advisory Philosophy:
- NEVER shame the user
- NEVER use terms like "bad credit" or "poor profile"
- ALWAYS emphasize improvement path
- ALWAYS provide realistic, achievable actions
"""

from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class CreditAdvice(BaseModel):
    """Natural language credit advisory response."""
    
    summary: str = Field(
        description="High-level summary of the decision in plain English"
    )
    
    key_risk_factors: List[str] = Field(
        description="Main credit factors translated to plain English"
    )
    
    recommended_actions: List[str] = Field(
        description="Specific, actionable steps to improve credit profile (max 4)"
    )
    
    user_tone: Literal["POSITIVE", "NEUTRAL", "CAUTIONARY"] = Field(
        description="Overall advisory tone based on decision"
    )
    
    next_steps: Optional[str] = Field(
        default=None,
        description="Immediate next steps for the user"
    )


# ═══════════════════════════════════════════════════════════════════════
# FEATURE NAME TRANSLATION
# ═══════════════════════════════════════════════════════════════════════

FEATURE_TRANSLATION_MAP = {
    # Financial metrics
    "debt-to-income ratio": "High debt relative to income",
    "debt to income": "High debt relative to income",
    "monthly debt": "High monthly debt obligations",
    "annual income": "Income level considerations",
    "credit utilization": "High usage of available credit",
    "utilization": "High credit card usage",
    
    # Credit history
    "credit score": "Credit score factors",
    "recent delinquencies": "Recent missed or delayed payments",
    "delinquencies": "Payment history concerns",
    "payment history": "Past payment patterns",
    "credit inquiries": "Multiple recent credit applications",
    "inquiries": "Recent credit checks",
    
    # Account metrics
    "open accounts": "Number of active credit accounts",
    "number of accounts": "Credit account activity",
    "employment length": "Length of current employment",
    
    # Loan specifics
    "loan amount": "Requested loan size",
    "loan term": "Loan duration considerations",
    
    # Home ownership
    "home ownership": "Housing situation",
    "mortgage": "Homeownership status",
    "rent": "Current housing arrangement",
    
    # Loan purpose
    "debt consolidation": "Purpose: Debt consolidation",
    "credit card": "Purpose: Credit card",
    "home improvement": "Purpose: Home improvement",
    "major purchase": "Purpose: Major purchase",
    "medical": "Purpose: Medical expenses",
}


# ═══════════════════════════════════════════════════════════════════════
# ACTIONABLE ADVICE MAPPING
# ═══════════════════════════════════════════════════════════════════════

ADVICE_TEMPLATES = {
    # Debt-related advice
    "debt": [
        "Reducing outstanding balances can significantly improve your credit strength.",
        "Consider creating a debt paydown plan to lower your debt-to-income ratio.",
        "Focusing on high-interest debt first may accelerate your progress."
    ],
    
    # Payment history
    "delinquenc": [
        "Maintaining consistent, on-time payments over the next few months will help rebuild trust.",
        "Setting up automatic payments can ensure you never miss a due date.",
        "Even a few months of perfect payment history can begin to offset past delays."
    ],
    
    # Credit utilization
    "utilization": [
        "Reducing credit card balances below 30% of limits is a quick way to improve your profile.",
        "Paying down balances before statement dates can positively impact utilization.",
        "Consider requesting credit limit increases to lower your utilization ratio."
    ],
    
    "credit": [
        "Keeping credit card balances low relative to limits strengthens your profile.",
        "Avoid maxing out credit cards, even if you pay them off monthly."
    ],
    
    # Credit inquiries
    "inquir": [
        "Limiting new credit applications over the next 6-12 months may positively impact future evaluations.",
        "Multiple credit checks in a short period can raise concerns. Space out applications when possible."
    ],
    
    # Employment
    "employment": [
        "Stable employment history demonstrates financial reliability.",
        "If changing jobs, maintaining consistent income can help offset shorter tenure."
    ],
    
    # Income
    "income": [
        "Increasing your income through raises, promotions, or additional work can improve your debt-to-income ratio.",
        "Documenting all sources of income ensures a complete financial picture."
    ],
    
    # Credit history length
    "history": [
        "Allowing your credit accounts to mature over time can improve stability.",
        "Keeping older accounts open helps demonstrate a longer credit history."
    ],
    
    # General improvements
    "general": [
        "Regularly monitoring your credit report helps identify areas for improvement.",
        "Building an emergency fund can prevent future missed payments.",
        "Consider speaking with a non-profit credit counselor for personalized guidance."
    ]
}


# ═══════════════════════════════════════════════════════════════════════
# CREDIT ADVISOR ENGINE
# ═══════════════════════════════════════════════════════════════════════

class CreditAdvisorEngine:
    """Natural language credit advisory engine.
    
    Converts technical ML outputs and policy decisions into user-friendly
    advice with actionable steps for credit profile improvement.
    """
    
    def __init__(self):
        """Initialize credit advisor engine."""
        self.feature_map = FEATURE_TRANSLATION_MAP
        self.advice_map = ADVICE_TEMPLATES
    
    def generate_advice(
        self,
        decision: Literal["APPROVE", "REVIEW", "REJECT"],
        risk_tier: Literal["LOW", "MEDIUM", "HIGH"],
        explanation_summary: Optional[Dict[str, Any]] = None,
        confidence: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM",
        override_applied: bool = False
    ) -> CreditAdvice:
        """Generate natural language credit advice.
        
        Args:
            decision: Final credit decision
            risk_tier: Risk tier assessment
            explanation_summary: SHAP explanations with top factors
            confidence: Model confidence level
            override_applied: Whether policy override changed decision
            
        Returns:
            CreditAdvice with summary, factors, and recommended actions
        """
        logger.info(
            "generating_credit_advice",
            decision=decision,
            risk_tier=risk_tier,
            confidence=confidence,
            has_explanations=explanation_summary is not None
        )
        
        # Determine advisory tone
        user_tone = self._determine_tone(decision)
        
        # Generate summary
        summary = self._generate_summary(
            decision=decision,
            risk_tier=risk_tier,
            confidence=confidence,
            override_applied=override_applied
        )
        
        # Extract and translate key risk factors
        key_risk_factors = self._extract_key_factors(explanation_summary)
        
        # Generate actionable recommendations
        recommended_actions = self._generate_actions(
            decision=decision,
            risk_tier=risk_tier,
            explanation_summary=explanation_summary,
            confidence=confidence
        )
        
        # Generate next steps
        next_steps = self._generate_next_steps(decision, override_applied, confidence)
        
        advice = CreditAdvice(
            summary=summary,
            key_risk_factors=key_risk_factors,
            recommended_actions=recommended_actions,
            user_tone=user_tone,
            next_steps=next_steps
        )
        
        logger.info(
            "credit_advice_generated",
            user_tone=user_tone,
            factors_count=len(key_risk_factors),
            actions_count=len(recommended_actions)
        )
        
        return advice
    
    def _determine_tone(self, decision: str) -> Literal["POSITIVE", "NEUTRAL", "CAUTIONARY"]:
        """Determine advisory tone based on decision.
        
        Args:
            decision: Final credit decision
            
        Returns:
            Advisory tone
        """
        if decision == "APPROVE":
            return "POSITIVE"
        elif decision == "REVIEW":
            return "NEUTRAL"
        else:  # REJECT
            return "CAUTIONARY"
    
    def _generate_summary(
        self,
        decision: str,
        risk_tier: str,
        confidence: str,
        override_applied: bool
    ) -> str:
        """Generate high-level summary in natural language.
        
        Args:
            decision: Final credit decision
            risk_tier: Risk tier
            confidence: Model confidence
            override_applied: Whether override was applied
            
        Returns:
            Summary string
        """
        if decision == "APPROVE":
            if risk_tier == "LOW":
                return "Your credit profile shows strong stability with manageable risk indicators. Based on the available information, your application is well-positioned for approval."
            else:
                return "Your application meets the approval criteria. While some factors require attention, your overall profile demonstrates financial capability."
        
        elif decision == "REVIEW":
            if override_applied:
                if confidence == "LOW":
                    return "Your application requires additional review to ensure a thorough and fair assessment. This is a standard process for applications with varied credit factors."
                else:
                    return "Some aspects of your credit profile require closer attention. A manual review helps ensure a fair and accurate decision tailored to your situation."
            else:
                if risk_tier == "MEDIUM":
                    return "Your credit profile shows a mix of positive and concerning factors. A personalized review will help determine the best path forward."
                else:
                    return "Your application requires detailed evaluation due to certain risk indicators. This review process ensures we consider all aspects of your financial situation."
        
        else:  # REJECT
            if risk_tier == "HIGH":
                return "At this time, your credit profile shows elevated risk indicators that don't align with current approval standards. This decision is not final and can improve with targeted financial actions."
            else:
                return "Based on the current assessment, your application does not meet the minimum requirements at this time. However, there are clear steps you can take to strengthen your profile for future applications."
    
    def _extract_key_factors(self, explanation_summary: Optional[Dict[str, Any]]) -> List[str]:
        """Extract and translate key risk factors to plain English.
        
        Args:
            explanation_summary: SHAP explanations
            
        Returns:
            List of translated risk factors (max 4)
        """
        if not explanation_summary or "top_risk_factors" not in explanation_summary:
            return ["Credit profile factors require additional review"]
        
        risk_factors = explanation_summary.get("top_risk_factors", [])
        
        translated_factors = []
        for factor in risk_factors[:4]:  # Max 4 factors
            feature_name = factor.get("feature", "").lower()
            
            # Try to translate using mapping
            translated = self._translate_feature_name(feature_name)
            if translated and translated not in translated_factors:
                translated_factors.append(translated)
        
        # If no factors translated, provide generic message
        if not translated_factors:
            translated_factors = ["Multiple credit profile factors were considered"]
        
        return translated_factors
    
    def _translate_feature_name(self, feature_name: str) -> Optional[str]:
        """Translate raw feature name to user-friendly description.
        
        Args:
            feature_name: Raw feature name from SHAP
            
        Returns:
            Translated name or None
        """
        feature_lower = feature_name.lower()
        
        # Direct match
        if feature_lower in self.feature_map:
            return self.feature_map[feature_lower]
        
        # Partial match
        for key, translation in self.feature_map.items():
            if key in feature_lower or feature_lower in key:
                return translation
        
        # Fallback: Clean up the raw name
        if feature_name:
            # Remove underscores, capitalize
            cleaned = feature_name.replace("_", " ").replace("-", " ").title()
            if ":" not in cleaned:  # Don't return already formatted names
                return cleaned
        
        return None
    
    def _generate_actions(
        self,
        decision: str,
        risk_tier: str,
        explanation_summary: Optional[Dict[str, Any]],
        confidence: str
    ) -> List[str]:
        """Generate actionable recommendations (max 4).
        
        Args:
            decision: Final decision
            risk_tier: Risk tier
            explanation_summary: SHAP explanations
            confidence: Model confidence
            
        Returns:
            List of actionable recommendations
        """
        actions = []
        
        # If confidence is LOW, prioritize manual review
        if confidence == "LOW":
            actions.append(
                "Contacting a loan officer for a personalized review may provide additional options."
            )
        
        # Extract actions based on risk factors
        if explanation_summary and "top_risk_factors" in explanation_summary:
            risk_factors = explanation_summary["top_risk_factors"]
            
            for factor in risk_factors[:3]:  # Look at top 3 factors
                feature_name = factor.get("feature", "").lower()
                
                # Find relevant advice
                relevant_advice = self._find_relevant_advice(feature_name)
                
                for advice_text in relevant_advice:
                    if advice_text not in actions and len(actions) < 4:
                        actions.append(advice_text)
        
        # Add decision-specific actions
        if decision == "APPROVE":
            if len(actions) < 4:
                actions.append(
                    "Maintaining current positive financial habits will support future credit needs."
                )
        
        elif decision == "REVIEW":
            if len(actions) < 4 and "personalized review" not in " ".join(actions).lower():
                actions.append(
                    "Gathering recent income documentation may help expedite the review process."
                )
        
        elif decision == "REJECT":
            # Ensure reject has helpful improvement actions
            if len(actions) < 4:
                actions.append(
                    "Regularly monitoring your credit report helps track improvement and identify errors."
                )
        
        # Add general advice if needed
        if len(actions) < 2:
            actions.extend(self.advice_map["general"][:4 - len(actions)])
        
        # Ensure max 4 actions
        return actions[:4]
    
    def _find_relevant_advice(self, feature_name: str) -> List[str]:
        """Find relevant advice based on feature name.
        
        Args:
            feature_name: Feature name (lowercase)
            
        Returns:
            List of relevant advice strings
        """
        relevant_advice = []
        
        # Check each advice category
        for keyword, advice_list in self.advice_map.items():
            if keyword in feature_name or feature_name in keyword:
                relevant_advice.extend(advice_list)
        
        return relevant_advice
    
    def _generate_next_steps(
        self,
        decision: str,
        override_applied: bool,
        confidence: str
    ) -> str:
        """Generate immediate next steps for the user.
        
        Args:
            decision: Final decision
            override_applied: Whether override was applied
            confidence: Model confidence
            
        Returns:
            Next steps string
        """
        if decision == "APPROVE":
            return "You may proceed with the next stage of the application process. A loan officer will contact you with further details."
        
        elif decision == "REVIEW":
            if confidence == "LOW":
                return "Your application has been forwarded to our underwriting team. They will contact you within 2-3 business days with next steps or requests for additional information."
            else:
                return "A credit specialist will review your application manually within 2-3 business days. You may be contacted for additional documentation."
        
        else:  # REJECT
            return "While this application was not approved, you can reapply after addressing the key factors listed above. We recommend waiting 60-90 days and working on the recommended actions."


# ═══════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════

_credit_advisor: Optional[CreditAdvisorEngine] = None


def get_credit_advisor() -> CreditAdvisorEngine:
    """Get global credit advisor instance.
    
    Returns:
        Singleton CreditAdvisorEngine instance
    """
    global _credit_advisor
    
    if _credit_advisor is None:
        _credit_advisor = CreditAdvisorEngine()
        logger.info("credit_advisor_initialized")
    
    return _credit_advisor
