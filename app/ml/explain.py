"""Explanation generator for credit risk predictions.

This module generates human-readable explanations for credit risk scores.
All explanations are deterministic and based solely on input features.
"""

from typing import List, Dict, Any, Tuple
from app.schemas.request import CreditRiskRequest
from app.schemas.response import RiskLevel


class CreditRiskExplainer:
    """Generates deterministic explanations for credit risk predictions.
    
    This class analyzes risk factor contributions and produces
    human-readable text explaining the top 2-3 factors that
    most influence the risk assessment.
    """

    def __init__(self):
        """Initialize the explainer with factor templates."""
        # Template strings for each risk factor (deterministic, no randomness)
        self.factor_templates = {
            "credit_score": {
                "excellent": "Excellent credit score ({value}) demonstrates strong financial responsibility",
                "good": "Good credit score ({value}) indicates reliable payment history",
                "fair": "Fair credit score ({value}) suggests some credit management challenges",
                "poor": "Low credit score ({value}) indicates significant credit risk",
            },
            "debt_to_income": {
                "excellent": "Low debt-to-income ratio ({value}%) shows strong ability to repay",
                "good": "Moderate debt-to-income ratio ({value}%) is within acceptable range",
                "concerning": "High debt-to-income ratio ({value}%) limits repayment capacity",
                "critical": "Very high debt-to-income ratio ({value}%) presents serious repayment risk",
            },
            "employment": {
                "strong": "Stable employment history ({value} years) indicates reliable income",
                "moderate": "Moderate employment tenure ({value} years) shows developing stability",
                "weak": "Short employment history ({value} years) raises income stability concerns",
                "unemployed": "Limited employment history increases income uncertainty",
            },
            "delinquencies": {
                "clean": "Clean payment history with no delinquencies demonstrates reliability",
                "minor": "Recent delinquency ({value} in past 2 years) shows payment challenges",
                "moderate": "Multiple delinquencies ({value} in past 2 years) indicate payment struggles",
                "severe": "Frequent delinquencies ({value} in past 2 years) present serious default risk",
            },
            "inquiries": {
                "normal": "Minimal credit inquiries ({value}) suggest stable credit usage",
                "elevated": "Multiple credit inquiries ({value} in 6 months) indicate active credit seeking",
                "excessive": "Excessive credit inquiries ({value} in 6 months) suggest credit desperation",
            },
            "loan_size": {
                "reasonable": "Loan amount is proportionate to income",
                "large": "Large loan amount relative to income ({value}% of annual income) increases risk",
            },
        }

    def explain(
        self,
        request: CreditRiskRequest,
        risk_score: float,
        risk_level: RiskLevel,
        component_scores: Dict[str, float],
    ) -> str:
        """Generate explanation for credit risk prediction.
        
        Args:
            request: Original credit risk request with applicant data
            risk_score: Computed risk score (0-100 scale)
            risk_level: Derived risk level (LOW, MEDIUM, HIGH)
            component_scores: Individual risk component scores (0-100 each)
            
        Returns:
            Human-readable explanation string (2-4 sentences)
        """
        # Rank factors by contribution to risk
        ranked_factors = self._rank_factors(component_scores)
        
        # Build explanation starting with overall assessment
        explanation_parts = [
            self._generate_overall_statement(risk_score, risk_level)
        ]
        
        # Add top 2-3 contributing factors
        explanation_parts.extend(
            self._generate_factor_explanations(request, ranked_factors[:3])
        )
        
        # Combine into single explanation
        return " ".join(explanation_parts)

    def explain_detailed(
        self,
        request: CreditRiskRequest,
        risk_score: float,
        risk_level: RiskLevel,
        component_scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """Generate detailed structured explanation.
        
        Args:
            request: Original credit risk request
            risk_score: Computed risk score (0-100)
            risk_level: Derived risk level
            component_scores: Component risk scores
            
        Returns:
            Dictionary with overall summary, top risks, and top strengths
        """
        ranked_factors = self._rank_factors(component_scores)
        
        # Identify top risks (highest scores) and strengths (lowest scores)
        top_risks = [f for f in ranked_factors if component_scores[f] > 50][:3]
        top_strengths = [f for f in reversed(ranked_factors) if component_scores[f] < 40][:2]
        
        return {
            "overall": self._generate_overall_statement(risk_score, risk_level),
            "risk_level": risk_level.value,
            "risk_score": round(risk_score, 1),
            "top_risks": self._generate_factor_list(request, top_risks, "negative"),
            "top_strengths": self._generate_factor_list(request, top_strengths, "positive"),
            "recommendation": self._generate_recommendation(risk_level, request),
        }

    def _rank_factors(self, component_scores: Dict[str, float]) -> List[str]:
        """Rank factors by risk contribution (highest to lowest).
        
        Args:
            component_scores: Dictionary of factor names to risk scores
            
        Returns:
            List of factor names sorted by risk contribution (descending)
        """
        # Sort by score descending (highest risk first)
        return sorted(component_scores.keys(), key=lambda k: component_scores[k], reverse=True)

    def _generate_overall_statement(self, risk_score: float, risk_level: RiskLevel) -> str:
        """Generate overall risk assessment statement.
        
        Args:
            risk_score: Numeric risk score (0-100)
            risk_level: Categorical risk level
            
        Returns:
            Opening statement describing overall risk
        """
        if risk_level == RiskLevel.LOW:
            return f"Low risk applicant (score: {risk_score:.0f}/100) with strong creditworthiness."
        elif risk_level == RiskLevel.MEDIUM:
            return f"Moderate risk applicant (score: {risk_score:.0f}/100) requiring careful review."
        else:  # HIGH or VERY_HIGH
            return f"High risk applicant (score: {risk_score:.0f}/100) with significant default probability."

    def _generate_factor_explanations(
        self,
        request: CreditRiskRequest,
        factor_names: List[str],
    ) -> List[str]:
        """Generate explanation sentences for top factors.
        
        Args:
            request: Credit risk request with applicant data
            factor_names: List of factor names to explain (ordered by importance)
            
        Returns:
            List of explanation sentences
        """
        explanations = []
        
        for factor in factor_names:
            if factor == "credit_score":
                explanations.append(self._explain_credit_score(request.credit_score))
            elif factor == "debt_to_income":
                explanations.append(self._explain_dti(request.compute_dti()))
            elif factor == "employment":
                explanations.append(self._explain_employment(request.employment_length_years))
            elif factor == "delinquencies":
                explanations.append(self._explain_delinquencies(request.delinquencies_2y))
            elif factor == "inquiries":
                explanations.append(self._explain_inquiries(request.inquiries_6m))
        
        return explanations

    def _generate_factor_list(
        self,
        request: CreditRiskRequest,
        factor_names: List[str],
        sentiment: str,
    ) -> List[Dict[str, Any]]:
        """Generate structured list of factor explanations.
        
        Args:
            request: Credit risk request
            factor_names: Factors to include
            sentiment: "positive" or "negative"
            
        Returns:
            List of dicts with factor, value, and explanation
        """
        factors = []
        
        for factor in factor_names:
            if factor == "credit_score":
                factors.append({
                    "factor": "Credit Score",
                    "value": request.credit_score,
                    "explanation": self._explain_credit_score(request.credit_score),
                })
            elif factor == "debt_to_income":
                dti = request.compute_dti()
                factors.append({
                    "factor": "Debt-to-Income Ratio",
                    "value": f"{dti:.1f}%",
                    "explanation": self._explain_dti(dti),
                })
            elif factor == "employment":
                factors.append({
                    "factor": "Employment Length",
                    "value": f"{request.employment_length_years} years",
                    "explanation": self._explain_employment(request.employment_length_years),
                })
            elif factor == "delinquencies":
                factors.append({
                    "factor": "Payment History",
                    "value": f"{request.delinquencies_2y} delinquencies",
                    "explanation": self._explain_delinquencies(request.delinquencies_2y),
                })
        
        return factors

    def _generate_recommendation(self, risk_level: RiskLevel, request: CreditRiskRequest) -> str:
        """Generate actionable recommendation based on risk level.
        
        Args:
            risk_level: Derived risk level
            request: Credit risk request
            
        Returns:
            Recommendation text
        """
        if risk_level == RiskLevel.LOW:
            return "Recommend approval with standard terms and interest rates."
        elif risk_level == RiskLevel.MEDIUM:
            return "Recommend manual underwriter review. Consider higher interest rate or collateral."
        else:
            return "Recommend rejection or require substantial down payment and collateral."

    def _explain_credit_score(self, score: int) -> str:
        """Generate explanation for credit score.
        
        Args:
            score: FICO credit score (300-850)
            
        Returns:
            Explanation sentence
        """
        if score >= 800:
            template = self.factor_templates["credit_score"]["excellent"]
        elif score >= 670:
            template = self.factor_templates["credit_score"]["good"]
        elif score >= 580:
            template = self.factor_templates["credit_score"]["fair"]
        else:
            template = self.factor_templates["credit_score"]["poor"]
        
        return template.format(value=score)

    def _explain_dti(self, dti: float) -> str:
        """Generate explanation for debt-to-income ratio.
        
        Args:
            dti: Debt-to-income ratio as percentage
            
        Returns:
            Explanation sentence
        """
        if dti < 20:
            template = self.factor_templates["debt_to_income"]["excellent"]
        elif dti < 36:
            template = self.factor_templates["debt_to_income"]["good"]
        elif dti < 50:
            template = self.factor_templates["debt_to_income"]["concerning"]
        else:
            template = self.factor_templates["debt_to_income"]["critical"]
        
        return template.format(value=round(dti, 1))

    def _explain_employment(self, years: float) -> str:
        """Generate explanation for employment length.
        
        Args:
            years: Years at current employment
            
        Returns:
            Explanation sentence
        """
        if years == 0:
            template = self.factor_templates["employment"]["unemployed"]
        elif years < 1:
            template = self.factor_templates["employment"]["weak"]
        elif years < 3:
            template = self.factor_templates["employment"]["moderate"]
        else:
            template = self.factor_templates["employment"]["strong"]
        
        return template.format(value=years)

    def _explain_delinquencies(self, count: int) -> str:
        """Generate explanation for delinquency count.
        
        Args:
            count: Number of delinquencies in past 2 years
            
        Returns:
            Explanation sentence
        """
        if count == 0:
            template = self.factor_templates["delinquencies"]["clean"]
        elif count == 1:
            template = self.factor_templates["delinquencies"]["minor"]
        elif count <= 2:
            template = self.factor_templates["delinquencies"]["moderate"]
        else:
            template = self.factor_templates["delinquencies"]["severe"]
        
        return template.format(value=count)

    def _explain_inquiries(self, count: int) -> str:
        """Generate explanation for credit inquiry count.
        
        Args:
            count: Number of credit inquiries in past 6 months
            
        Returns:
            Explanation sentence
        """
        if count <= 1:
            template = self.factor_templates["inquiries"]["normal"]
        elif count <= 3:
            template = self.factor_templates["inquiries"]["elevated"]
        else:
            template = self.factor_templates["inquiries"]["excessive"]
        
        return template.format(value=count)


# Module-level singleton instance
_explainer_instance = None


def get_explainer() -> CreditRiskExplainer:
    """Get or create the global explainer instance.
    
    Returns:
        CreditRiskExplainer singleton instance
    """
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = CreditRiskExplainer()
    return _explainer_instance
