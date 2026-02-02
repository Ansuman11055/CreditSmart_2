"""Deterministic credit risk inference engine.

This module implements a rule-based scoring system for credit risk assessment.
The engine applies weighted factors to compute a risk score between 0-100.
"""

from typing import Dict, Any
from app.schemas.request import CreditRiskRequest
from app.schemas.response import CreditRiskResponse, RiskLevel
from app.ml.explain import get_explainer


class CreditRiskInferenceEngine:
    """Rule-based inference engine for credit risk prediction.
    
    This engine computes risk scores using transparent, deterministic rules
    rather than black-box ML models. Each factor contributes to the overall
    risk score with clear, explainable weights.
    """

    def __init__(self):
        """Initialize the inference engine with default weights."""
        # Weight configuration for each risk factor (sum to 1.0 for interpretability)
        self.weights = {
            "credit_score": 0.30,      # 30% - Most important factor
            "debt_to_income": 0.25,    # 25% - Ability to repay
            "employment": 0.15,        # 15% - Income stability
            "delinquencies": 0.15,     # 15% - Payment history
            "inquiries": 0.10,         # 10% - Credit seeking behavior
            "open_accounts": 0.05,     # 5% - Credit utilization
        }
        # Initialize explainer for generating human-readable explanations
        self.explainer = get_explainer()

    def predict(self, request: CreditRiskRequest) -> CreditRiskResponse:
        """Generate credit risk prediction from applicant data.
        
        Args:
            request: Validated credit risk request with applicant features
            
        Returns:
            CreditRiskResponse with risk score, level, and explanation
        """
        # Compute individual risk components (0-100 scale each)
        credit_score_risk = self._score_credit_score(request.credit_score)
        dti_risk = self._score_debt_to_income(request.compute_dti())
        employment_risk = self._score_employment(request.employment_length_years)
        delinquency_risk = self._score_delinquencies(request.delinquencies_2y)
        inquiry_risk = self._score_inquiries(request.inquiries_6m)
        account_risk = self._score_open_accounts(request.number_of_open_accounts)

        # Combine weighted components into final risk score (0-100)
        risk_score = (
            credit_score_risk * self.weights["credit_score"] +
            dti_risk * self.weights["debt_to_income"] +
            employment_risk * self.weights["employment"] +
            delinquency_risk * self.weights["delinquencies"] +
            inquiry_risk * self.weights["inquiries"] +
            account_risk * self.weights["open_accounts"]
        )

        # Apply loan-specific adjustments
        risk_score = self._adjust_for_loan_characteristics(risk_score, request)

        # Clamp to valid range [0, 100]
        risk_score = max(0.0, min(100.0, risk_score))

        # Determine categorical risk level from numeric score
        risk_level = self._derive_risk_level(risk_score)

        # Determine recommended action
        recommended_action = self._derive_recommended_action(risk_level)

        # Build explanation of key risk factors using dedicated explainer
        component_scores = {
            "credit_score": credit_score_risk,
            "debt_to_income": dti_risk,
            "employment": employment_risk,
            "delinquencies": delinquency_risk,
            "inquiries": inquiry_risk,
            "open_accounts": account_risk,
        }
        explanation = self.explainer.explain(request, risk_score, risk_level, component_scores)

        # Collect key factors for interpretability
        key_factors = {
            "credit_score": {
                "value": request.credit_score,
                "impact": "positive" if credit_score_risk < 50 else "negative",
                "risk_contribution": round(credit_score_risk, 1),
            },
            "debt_to_income": {
                "value": round(request.compute_dti(), 1),
                "impact": "positive" if dti_risk < 50 else "negative",
                "risk_contribution": round(dti_risk, 1),
            },
            "employment_length": {
                "value": request.employment_length_years,
                "impact": "positive" if employment_risk < 50 else "negative",
                "risk_contribution": round(employment_risk, 1),
            },
            "delinquencies": {
                "value": request.delinquencies_2y,
                "impact": "positive" if delinquency_risk < 50 else "negative",
                "risk_contribution": round(delinquency_risk, 1),
            },
        }

        return CreditRiskResponse(
            risk_score=round(risk_score / 100, 3),  # Convert to 0-1 scale for API
            risk_level=risk_level,
            prediction_probability=round(risk_score / 100, 3),  # Same as risk_score for compatibility
            confidence_level="HIGH",  # Deterministic model has high confidence
            recommended_action=recommended_action,
            explanation=explanation,
            key_factors=key_factors,
            model_version="deterministic-v1.0.0",
        )

    def _score_credit_score(self, credit_score: int) -> float:
        """Score credit score component (0-100 risk scale).
        
        Logic:
        - 800+: Excellent (0-10 risk)
        - 740-799: Very good (10-25 risk)
        - 670-739: Good (25-45 risk)
        - 580-669: Fair (45-70 risk)
        - <580: Poor (70-100 risk)
        """
        if credit_score >= 800:
            return 5.0  # Minimal risk
        elif credit_score >= 740:
            # Linear interpolation: 740->25, 800->10
            return 25.0 - ((credit_score - 740) / 60) * 15
        elif credit_score >= 670:
            # Linear interpolation: 670->45, 740->25
            return 45.0 - ((credit_score - 670) / 70) * 20
        elif credit_score >= 580:
            # Linear interpolation: 580->70, 670->45
            return 70.0 - ((credit_score - 580) / 90) * 25
        else:
            # Below 580: high risk (70-100)
            return 70.0 + ((580 - credit_score) / 280) * 30

    def _score_debt_to_income(self, dti: float) -> float:
        """Score debt-to-income ratio (0-100 risk scale).
        
        Logic:
        - <20%: Excellent (0-15 risk)
        - 20-36%: Good (15-40 risk)
        - 36-43%: Fair (40-60 risk)
        - 43-50%: Poor (60-80 risk)
        - >50%: Very poor (80-100 risk)
        """
        if dti < 20:
            # Low DTI: minimal risk
            return 15.0 * (dti / 20)
        elif dti < 36:
            # Moderate DTI: increasing risk
            return 15.0 + ((dti - 20) / 16) * 25
        elif dti < 43:
            # High DTI: elevated risk
            return 40.0 + ((dti - 36) / 7) * 20
        elif dti < 50:
            # Very high DTI: severe risk
            return 60.0 + ((dti - 43) / 7) * 20
        else:
            # Extreme DTI: maximum risk
            return min(100.0, 80.0 + (dti - 50) * 0.5)

    def _score_employment(self, employment_years: float) -> float:
        """Score employment length (0-100 risk scale).
        
        Logic:
        - Short tenure (<1 year): Higher risk due to income instability
        - Medium tenure (1-5 years): Moderate risk
        - Long tenure (>5 years): Lower risk, stable income
        """
        if employment_years < 1:
            # New job or unemployed: high risk (60-80)
            return 80.0 - (employment_years * 20)
        elif employment_years < 3:
            # 1-3 years: moderate risk (40-60)
            return 60.0 - ((employment_years - 1) / 2) * 20
        elif employment_years < 5:
            # 3-5 years: lower risk (25-40)
            return 40.0 - ((employment_years - 3) / 2) * 15
        else:
            # 5+ years: minimal risk (10-25)
            return max(10.0, 25.0 - ((employment_years - 5) / 10) * 15)

    def _score_delinquencies(self, delinquencies: int) -> float:
        """Score delinquencies in past 2 years (0-100 risk scale).
        
        Logic:
        - 0 delinquencies: Excellent payment history (5 risk)
        - 1-2 delinquencies: Some issues (30-50 risk)
        - 3+ delinquencies: Serious payment problems (70-100 risk)
        """
        if delinquencies == 0:
            return 5.0  # Clean payment history
        elif delinquencies == 1:
            return 30.0  # Minor issue
        elif delinquencies == 2:
            return 50.0  # Moderate concern
        elif delinquencies == 3:
            return 70.0  # Major concern
        else:
            # 4+ delinquencies: severe risk
            return min(100.0, 70.0 + (delinquencies - 3) * 10)

    def _score_inquiries(self, inquiries: int) -> float:
        """Score credit inquiries in past 6 months (0-100 risk scale).
        
        Logic:
        - 0-1 inquiries: Normal (10-20 risk)
        - 2-3 inquiries: Moderate credit seeking (30-50 risk)
        - 4+ inquiries: Excessive credit seeking (60-100 risk)
        """
        if inquiries <= 1:
            return 10.0 + (inquiries * 10)
        elif inquiries <= 3:
            return 20.0 + ((inquiries - 1) * 15)
        else:
            # 4+ inquiries: potential credit desperation
            return min(100.0, 50.0 + ((inquiries - 3) * 12.5))

    def _score_open_accounts(self, accounts: int) -> float:
        """Score number of open credit accounts (0-100 risk scale).
        
        Logic:
        - 0-2 accounts: Limited credit history (40 risk)
        - 3-10 accounts: Healthy credit mix (20 risk)
        - 11+ accounts: Over-extended (30-60 risk)
        """
        if accounts <= 2:
            # Very few accounts: limited history
            return 40.0
        elif accounts <= 10:
            # Optimal range: healthy credit mix
            return 20.0
        else:
            # Too many accounts: over-leveraged
            return min(60.0, 30.0 + ((accounts - 10) * 3))

    def _adjust_for_loan_characteristics(
        self, base_risk: float, request: CreditRiskRequest
    ) -> float:
        """Apply adjustments based on loan-specific characteristics.
        
        Logic:
        - Large loans relative to income increase risk
        - Long-term loans slightly increase risk
        - Certain loan purposes have different risk profiles
        """
        adjusted_risk = base_risk

        # Loan-to-income ratio adjustment
        loan_to_income = request.loan_amount / max(request.annual_income, 1)
        if loan_to_income > 0.5:
            # Loan exceeds 50% of annual income: add 5-15 risk points
            adjusted_risk += min(15.0, (loan_to_income - 0.5) * 30)

        # Loan term adjustment (longer terms = slightly higher risk)
        if request.loan_term_months > 60:
            # Terms over 5 years: add 0-5 risk points
            adjusted_risk += min(5.0, (request.loan_term_months - 60) / 60)

        # Purpose-based adjustment
        high_risk_purposes = {"business", "vacation", "other"}
        if request.purpose in high_risk_purposes:
            adjusted_risk += 5.0  # Add 5 points for higher-risk purposes

        return adjusted_risk

    def _derive_risk_level(self, risk_score: float) -> RiskLevel:
        """Derive categorical risk level from numeric score.
        
        Thresholds:
        - 0-35: Low risk
        - 36-65: Medium risk  
        - 66-100: High risk
        """
        if risk_score <= 35:
            return RiskLevel.LOW
        elif risk_score <= 65:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def _derive_recommended_action(self, risk_level: RiskLevel) -> str:
        """Derive recommended action from risk level.
        
        Logic:
        - LOW: Approve automatically
        - MEDIUM: Manual review required
        - HIGH: Reject automatically
        """
        if risk_level == RiskLevel.LOW:
            return "APPROVE"
        elif risk_level == RiskLevel.MEDIUM:
            return "REVIEW"
        else:
            return "REJECT"

    def _generate_explanation(
        self,
        request: CreditRiskRequest,
        risk_score: float,
        risk_level: RiskLevel,
        component_scores: Dict[str, float],
    ) -> str:
        """Generate human-readable explanation of risk assessment.
        
        Args:
            request: Original request data
            risk_score: Computed risk score (0-100)
            risk_level: Derived risk level
            component_scores: Individual component risk scores
            
        Returns:
            Explanation string describing key risk factors
        """
        # Identify top risk drivers (highest component scores)
        sorted_components = sorted(
            component_scores.items(), key=lambda x: x[1], reverse=True
        )
        top_risk = sorted_components[0][0]
        top_strength = sorted_components[-1][0]

        explanation_parts = [
            f"Risk Score: {risk_score:.1f}/100 ({risk_level.value} risk)."
        ]

        # Explain primary concern
        if component_scores[top_risk] > 60:
            if top_risk == "credit_score":
                explanation_parts.append(
                    f"Primary concern: Low credit score ({request.credit_score})."
                )
            elif top_risk == "debt_to_income":
                explanation_parts.append(
                    f"Primary concern: High debt-to-income ratio ({request.compute_dti():.1f}%)."
                )
            elif top_risk == "employment":
                explanation_parts.append(
                    f"Primary concern: Short employment tenure ({request.employment_length_years} years)."
                )
            elif top_risk == "delinquencies":
                explanation_parts.append(
                    f"Primary concern: Recent delinquencies ({request.delinquencies_2y})."
                )

        # Highlight strengths
        if component_scores[top_strength] < 30:
            if top_strength == "credit_score":
                explanation_parts.append(
                    f"Strength: Excellent credit score ({request.credit_score})."
                )
            elif top_strength == "debt_to_income":
                explanation_parts.append(
                    f"Strength: Low debt-to-income ratio ({request.compute_dti():.1f}%)."
                )
            elif top_strength == "employment":
                explanation_parts.append(
                    f"Strength: Stable employment history ({request.employment_length_years} years)."
                )

        return " ".join(explanation_parts)
