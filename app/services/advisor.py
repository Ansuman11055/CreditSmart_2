"""Financial advisor service for generating improvement recommendations."""

from typing import List, Tuple
from app.schemas.request import CreditRiskRequest
from app.schemas.advisor import AdvisorResponse, FinancialAdvice


class FinancialAdvisorService:
    """Deterministic financial advisor that generates actionable recommendations.
    
    This service analyzes credit risk factors and produces prioritized
    suggestions for improving creditworthiness. All logic is rule-based
    and deterministic (no LLM required).
    """
    
    def __init__(self):
        """Initialize the advisor service."""
        pass
    
    def generate_advice(
        self,
        request: CreditRiskRequest,
        current_risk_score: float,
    ) -> AdvisorResponse:
        """Generate personalized financial advice.
        
        Args:
            request: Applicant's financial data
            current_risk_score: Current risk score (0-1 scale)
            
        Returns:
            AdvisorResponse with prioritized recommendations
        """
        # Compute debt-to-income ratio
        dti = request.compute_dti()
        
        # Analyze current situation and identify improvement areas
        recommendations = []
        strengths = []
        
        # Analyze each risk factor and generate targeted advice
        recommendations.extend(self._analyze_credit_score(request.credit_score))
        recommendations.extend(self._analyze_debt_to_income(dti, request.monthly_debt))
        recommendations.extend(self._analyze_employment(request.employment_length_years))
        recommendations.extend(self._analyze_payment_history(request.delinquencies_2y))
        recommendations.extend(self._analyze_credit_inquiries(request.inquiries_6m))
        recommendations.extend(self._analyze_credit_utilization(request.number_of_open_accounts))
        
        # Identify strengths
        strengths = self._identify_strengths(request, dti)
        
        # Sort recommendations by priority (HIGH -> MEDIUM -> LOW)
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        # Limit to top 8 recommendations
        recommendations = recommendations[:8]
        
        # Estimate potential improvement
        potential_score = self._estimate_potential_score(current_risk_score, recommendations)
        
        # Generate overall assessment
        assessment = self._generate_overall_assessment(current_risk_score, recommendations)
        
        # Generate next steps
        next_steps = self._generate_next_steps(recommendations)
        
        return AdvisorResponse(
            overall_assessment=assessment,
            current_risk_score=current_risk_score,
            potential_risk_score=potential_score,
            recommendations=recommendations,
            strengths=strengths,
            next_steps=next_steps,
        )
    
    def _analyze_credit_score(self, credit_score: int) -> List[FinancialAdvice]:
        """Analyze credit score and generate recommendations."""
        advice = []
        
        if credit_score < 580:
            # Poor credit - critical priority
            advice.append(FinancialAdvice(
                category="credit_score",
                priority="HIGH",
                suggestion=f"Improve credit score from {credit_score} to at least 620 through consistent on-time payments",
                expected_impact="Could reduce risk score by 25-30 points",
                timeframe="6-12 months"
            ))
            advice.append(FinancialAdvice(
                category="payment_history",
                priority="HIGH",
                suggestion="Set up automatic payments to ensure zero missed payments going forward",
                expected_impact="Prevents further score deterioration and builds positive history",
                timeframe="Immediate"
            ))
        elif credit_score < 670:
            # Fair credit - high priority
            advice.append(FinancialAdvice(
                category="credit_score",
                priority="HIGH",
                suggestion=f"Boost credit score from {credit_score} to 700+ by maintaining payment history and reducing utilization",
                expected_impact="Could reduce risk score by 15-20 points",
                timeframe="3-6 months"
            ))
        elif credit_score < 740:
            # Good credit - medium priority for improvement
            advice.append(FinancialAdvice(
                category="credit_score",
                priority="MEDIUM",
                suggestion=f"Optimize credit score from {credit_score} to 760+ through credit mix diversification",
                expected_impact="Could reduce risk score by 8-12 points",
                timeframe="3-6 months"
            ))
        
        return advice
    
    def _analyze_debt_to_income(self, dti: float, monthly_debt: float) -> List[FinancialAdvice]:
        """Analyze debt-to-income ratio and generate recommendations."""
        advice = []
        
        if dti > 50:
            # Critical DTI - highest priority
            advice.append(FinancialAdvice(
                category="debt_management",
                priority="HIGH",
                suggestion=f"Reduce debt-to-income ratio from {dti:.1f}% to below 43% by paying down ${monthly_debt * 0.15:.0f}/month extra",
                expected_impact="Could reduce risk score by 30-35 points",
                timeframe="12-24 months"
            ))
            advice.append(FinancialAdvice(
                category="income",
                priority="HIGH",
                suggestion="Consider additional income sources to improve debt-to-income ratio",
                expected_impact="Could reduce risk score by 15-20 points",
                timeframe="3-6 months"
            ))
        elif dti > 43:
            # High DTI - high priority
            advice.append(FinancialAdvice(
                category="debt_management",
                priority="HIGH",
                suggestion=f"Lower debt-to-income ratio from {dti:.1f}% to below 36% through debt consolidation or increased payments",
                expected_impact="Could reduce risk score by 20-25 points",
                timeframe="6-12 months"
            ))
        elif dti > 36:
            # Moderate DTI - medium priority
            advice.append(FinancialAdvice(
                category="debt_management",
                priority="MEDIUM",
                suggestion=f"Optimize debt-to-income ratio from {dti:.1f}% to below 30% for better loan terms",
                expected_impact="Could reduce risk score by 10-15 points",
                timeframe="6-12 months"
            ))
        elif dti > 20:
            # Good DTI - low priority optimization
            advice.append(FinancialAdvice(
                category="debt_management",
                priority="LOW",
                suggestion=f"Maintain healthy debt-to-income ratio of {dti:.1f}% or reduce further if pursuing premium rates",
                expected_impact="Could reduce risk score by 3-5 points",
                timeframe="3-6 months"
            ))
        
        return advice
    
    def _analyze_employment(self, employment_years: float) -> List[FinancialAdvice]:
        """Analyze employment length and generate recommendations."""
        advice = []
        
        if employment_years < 1:
            advice.append(FinancialAdvice(
                category="income",
                priority="MEDIUM",
                suggestion=f"Build employment history (currently {employment_years} years). Avoid job changes before applying for credit",
                expected_impact="Could reduce risk score by 10-15 points",
                timeframe="6-12 months"
            ))
        elif employment_years < 2:
            advice.append(FinancialAdvice(
                category="income",
                priority="LOW",
                suggestion="Continue building stable employment history to improve creditworthiness",
                expected_impact="Could reduce risk score by 5-8 points",
                timeframe="6-12 months"
            ))
        
        return advice
    
    def _analyze_payment_history(self, delinquencies: int) -> List[FinancialAdvice]:
        """Analyze payment history and generate recommendations."""
        advice = []
        
        if delinquencies >= 3:
            advice.append(FinancialAdvice(
                category="payment_history",
                priority="HIGH",
                suggestion=f"Address {delinquencies} recent delinquencies. Set up payment reminders and automatic payments",
                expected_impact="Could reduce risk score by 20-25 points over time",
                timeframe="12-24 months"
            ))
            advice.append(FinancialAdvice(
                category="payment_history",
                priority="HIGH",
                suggestion="Contact creditors about payment plans for past-due accounts to prevent further damage",
                expected_impact="Stops additional negative marks on credit report",
                timeframe="Immediate"
            ))
        elif delinquencies >= 1:
            advice.append(FinancialAdvice(
                category="payment_history",
                priority="MEDIUM",
                suggestion=f"Build consistent payment history to offset {delinquencies} past delinquency/-ies",
                expected_impact="Could reduce risk score by 10-15 points",
                timeframe="6-12 months"
            ))
        
        return advice
    
    def _analyze_credit_inquiries(self, inquiries: int) -> List[FinancialAdvice]:
        """Analyze credit inquiries and generate recommendations."""
        advice = []
        
        if inquiries >= 4:
            advice.append(FinancialAdvice(
                category="credit_score",
                priority="MEDIUM",
                suggestion=f"Avoid new credit applications for 6+ months ({inquiries} recent inquiries signals credit seeking)",
                expected_impact="Could reduce risk score by 8-12 points",
                timeframe="6 months"
            ))
        elif inquiries >= 2:
            advice.append(FinancialAdvice(
                category="credit_score",
                priority="LOW",
                suggestion="Minimize new credit inquiries to improve credit score",
                expected_impact="Could reduce risk score by 3-5 points",
                timeframe="3-6 months"
            ))
        
        return advice
    
    def _analyze_credit_utilization(self, open_accounts: int) -> List[FinancialAdvice]:
        """Analyze credit utilization and generate recommendations."""
        advice = []
        
        if open_accounts <= 2:
            advice.append(FinancialAdvice(
                category="credit_score",
                priority="LOW",
                suggestion=f"Consider diversifying credit mix (currently {open_accounts} accounts) with a credit builder account",
                expected_impact="Could reduce risk score by 5-8 points",
                timeframe="6-12 months"
            ))
        elif open_accounts > 12:
            advice.append(FinancialAdvice(
                category="debt_management",
                priority="MEDIUM",
                suggestion=f"Consolidate or close some unused accounts (currently {open_accounts}) to simplify credit profile",
                expected_impact="Could reduce risk score by 5-10 points",
                timeframe="3-6 months"
            ))
        
        return advice
    
    def _identify_strengths(self, request: CreditRiskRequest, dti: float) -> List[str]:
        """Identify financial strengths to maintain."""
        strengths = []
        
        if request.credit_score >= 740:
            strengths.append(f"Excellent credit score ({request.credit_score})")
        elif request.credit_score >= 670:
            strengths.append(f"Good credit score ({request.credit_score})")
        
        if dti < 20:
            strengths.append(f"Very low debt-to-income ratio ({dti:.1f}%)")
        elif dti < 36:
            strengths.append(f"Healthy debt-to-income ratio ({dti:.1f}%)")
        
        if request.employment_length_years >= 5:
            strengths.append(f"Stable long-term employment ({request.employment_length_years} years)")
        elif request.employment_length_years >= 2:
            strengths.append(f"Stable employment history ({request.employment_length_years} years)")
        
        if request.delinquencies_2y == 0:
            strengths.append("Clean payment history with no delinquencies")
        
        if request.inquiries_6m <= 1:
            strengths.append("Minimal recent credit inquiries")
        
        if 3 <= request.number_of_open_accounts <= 10:
            strengths.append(f"Healthy credit mix ({request.number_of_open_accounts} accounts)")
        
        return strengths
    
    def _estimate_potential_score(
        self, current_score: float, recommendations: List[FinancialAdvice]
    ) -> float:
        """Estimate potential risk score if recommendations are followed."""
        # Count high-priority recommendations
        high_priority_count = sum(1 for r in recommendations if r.priority == "HIGH")
        medium_priority_count = sum(1 for r in recommendations if r.priority == "MEDIUM")
        
        # Estimate improvement (conservative)
        # Each HIGH priority recommendation could reduce score by ~15-20%
        # Each MEDIUM priority recommendation could reduce score by ~8-12%
        improvement = (high_priority_count * 0.15) + (medium_priority_count * 0.08)
        improvement = min(improvement, 0.5)  # Cap at 50% improvement
        
        potential = current_score * (1 - improvement)
        return max(0.0, min(1.0, round(potential, 3)))
    
    def _generate_overall_assessment(
        self, current_score: float, recommendations: List[FinancialAdvice]
    ) -> str:
        """Generate overall assessment summary."""
        high_count = sum(1 for r in recommendations if r.priority == "HIGH")
        
        if current_score < 0.35:
            if high_count == 0:
                return "Strong financial position with minimal areas for improvement"
            else:
                return "Good financial foundation with some opportunities to optimize further"
        elif current_score < 0.65:
            if high_count >= 2:
                return "Moderate risk profile with multiple priority areas requiring attention"
            else:
                return "Moderate risk profile with clear improvement opportunities"
        else:
            if high_count >= 3:
                return "High risk profile requiring immediate action across multiple areas"
            else:
                return "Elevated risk profile with significant room for improvement"
    
    def _generate_next_steps(self, recommendations: List[FinancialAdvice]) -> str:
        """Generate immediate next steps from top recommendations."""
        high_priority = [r for r in recommendations if r.priority == "HIGH"]
        
        if not high_priority:
            medium_priority = [r for r in recommendations if r.priority == "MEDIUM"]
            if medium_priority:
                return f"Focus on: {medium_priority[0].suggestion}"
            return "Continue maintaining current healthy financial habits"
        
        if len(high_priority) == 1:
            return f"Immediate priority: {high_priority[0].suggestion}"
        else:
            # Combine top 2 priorities
            categories = [r.category for r in high_priority[:2]]
            return f"Focus on {' and '.join(categories)} as immediate priorities"


# Singleton instance
_advisor_instance = None


def get_advisor() -> FinancialAdvisorService:
    """Get or create the global advisor service instance."""
    global _advisor_instance
    if _advisor_instance is None:
        _advisor_instance = FinancialAdvisorService()
    return _advisor_instance
