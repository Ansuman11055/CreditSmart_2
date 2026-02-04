# Phase 4D Explainability - Natural Language Explanation Engine

from typing import List, Dict, Any, Tuple
import numpy as np
from dataclasses import dataclass

# Phase 4D Explainability - Human-readable feature name mapping
FEATURE_NAME_MAPPING = {
    "annual_income": "Annual Income",
    "monthly_debt": "Monthly Debt Payments",
    "credit_score": "Credit Score",
    "loan_amount": "Requested Loan Amount",
    "loan_term_months": "Loan Term Length",
    "employment_length_years": "Employment History",
    "home_ownership": "Home Ownership Status",
    "purpose": "Loan Purpose",
    "number_of_open_accounts": "Number of Open Accounts",
    "delinquencies_2y": "Recent Delinquencies",
    "inquiries_6m": "Recent Credit Inquiries"
}

# Phase 4D Explainability - Risk band definitions
RISK_BANDS = {
    "low": {
        "threshold_max": 0.3,
        "label": "Low Risk",
        "description": "Strong financial profile with minimal default risk",
        "color": "green"
    },
    "medium": {
        "threshold_min": 0.3,
        "threshold_max": 0.6,
        "label": "Moderate Risk",
        "description": "Acceptable risk with some areas of concern",
        "color": "yellow"
    },
    "high": {
        "threshold_min": 0.6,
        "label": "High Risk",
        "description": "Elevated default probability requiring careful review",
        "color": "red"
    }
}

@dataclass
class FeatureContribution:
    """Phase 4D Explainability - Single feature's contribution to prediction"""
    feature_name: str
    human_name: str
    shap_value: float
    feature_value: Any
    impact: str  # "positive" or "negative"
    magnitude: str  # "low", "medium", "high"
    explanation: str


@dataclass
class ExplanationResult:
    """Phase 4D Explainability - Complete explanation package"""
    top_positive_features: List[FeatureContribution]
    top_negative_features: List[FeatureContribution]
    risk_band: str
    risk_band_description: str
    what_helped: List[str]
    what_hurt: List[str]
    how_to_improve: List[str]
    disclaimer: str


class ExplainabilityService:
    """
    Phase 4D Explainability - Service for generating natural language explanations
    from SHAP values and model predictions
    """
    
    def __init__(self):
        self.feature_mapping = FEATURE_NAME_MAPPING
        self.risk_bands = RISK_BANDS
        # Phase 4D Explainability - Compliance disclaimer
        self.disclaimer = (
            "This assessment is advisory and does not constitute financial advice. "
            "Final lending decisions should consider additional factors and comply with "
            "applicable regulations."
        )
    
    def get_risk_band(self, probability: float) -> Tuple[str, str]:
        """
        Phase 4D Explainability - Determine risk band from probability
        
        Args:
            probability: Default probability (0.0 to 1.0)
            
        Returns:
            Tuple of (band_name, band_description)
        """
        if probability < 0.3:
            band = self.risk_bands["low"]
            return "low", band["description"]
        elif probability < 0.6:
            band = self.risk_bands["medium"]
            return "medium", band["description"]
        else:
            band = self.risk_bands["high"]
            return "high", band["description"]
    
    def categorize_shap_magnitude(self, shap_value: float, all_shap_values: np.ndarray) -> str:
        """
        Phase 4D Explainability - Convert SHAP value to qualitative magnitude
        
        Args:
            shap_value: Individual SHAP value
            all_shap_values: All SHAP values for context
            
        Returns:
            "low", "medium", or "high"
        """
        abs_value = abs(shap_value)
        abs_values = np.abs(all_shap_values)
        
        percentile_75 = np.percentile(abs_values, 75)
        percentile_50 = np.percentile(abs_values, 50)
        
        if abs_value >= percentile_75:
            return "high"
        elif abs_value >= percentile_50:
            return "medium"
        else:
            return "low"
    
    def generate_feature_explanation(
        self, 
        feature_name: str, 
        feature_value: Any, 
        shap_value: float,
        impact: str
    ) -> str:
        """
        Phase 4D Explainability - Generate natural language explanation for a feature
        
        Args:
            feature_name: Raw feature name
            feature_value: Feature's actual value
            shap_value: SHAP contribution
            impact: "positive" or "negative"
            
        Returns:
            Human-readable explanation string
        """
        human_name = self.feature_mapping.get(feature_name, feature_name)
        
        # Phase 4D Explainability - Feature-specific explanation templates
        if feature_name == "credit_score":
            if impact == "positive":
                if feature_value >= 750:
                    return f"Excellent credit score ({feature_value}) demonstrates strong repayment history"
                elif feature_value >= 700:
                    return f"Good credit score ({feature_value}) indicates reliable financial behavior"
                else:
                    return f"Credit score ({feature_value}) shows acceptable credit history"
            else:
                if feature_value < 600:
                    return f"Low credit score ({feature_value}) raises concerns about repayment ability"
                else:
                    return f"Credit score ({feature_value}) below ideal threshold increases risk"
        
        elif feature_name == "annual_income":
            if impact == "positive":
                return f"Strong annual income (${feature_value:,.0f}) supports loan repayment capacity"
            else:
                return f"Annual income (${feature_value:,.0f}) may limit repayment flexibility"
        
        elif feature_name == "monthly_debt":
            if impact == "negative":
                return f"Monthly debt obligations (${feature_value:,.0f}) add financial strain"
            else:
                return f"Manageable monthly debt (${feature_value:,.0f}) indicates good debt control"
        
        elif feature_name == "loan_amount":
            if impact == "negative":
                return f"Large loan amount (${feature_value:,.0f}) increases default risk exposure"
            else:
                return f"Modest loan amount (${feature_value:,.0f}) reduces overall risk"
        
        elif feature_name == "employment_length_years":
            if impact == "positive":
                return f"Stable employment ({feature_value} years) demonstrates job security"
            else:
                return f"Limited employment history ({feature_value} years) raises stability concerns"
        
        elif feature_name == "delinquencies_2y":
            if feature_value > 0:
                return f"{feature_value} recent delinquencies indicate payment difficulties"
            else:
                return "No recent delinquencies show consistent payment behavior"
        
        elif feature_name == "inquiries_6m":
            if feature_value > 3:
                return f"{feature_value} recent credit inquiries suggest financial stress"
            else:
                return f"Few credit inquiries ({feature_value}) indicate stable credit usage"
        
        elif feature_name == "number_of_open_accounts":
            if impact == "positive":
                return f"Healthy number of accounts ({feature_value}) shows credit experience"
            else:
                return f"High number of accounts ({feature_value}) may indicate overextension"
        
        # Phase 4D Explainability - Generic fallback
        return f"{human_name} contributes {'positively' if impact == 'positive' else 'negatively'} to risk assessment"
    
    def generate_improvement_suggestions(
        self, 
        negative_features: List[FeatureContribution],
        risk_band: str
    ) -> List[str]:
        """
        Phase 4D Explainability - Generate actionable improvement suggestions
        
        Args:
            negative_features: Features that hurt the score
            risk_band: Current risk band
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Phase 4D Explainability - Feature-specific improvement advice
        for contrib in negative_features:
            if contrib.feature_name == "credit_score":
                suggestions.append(
                    "Improve credit score by making on-time payments and reducing credit utilization"
                )
            elif contrib.feature_name == "monthly_debt":
                suggestions.append(
                    "Reduce monthly debt obligations to improve debt-to-income ratio"
                )
            elif contrib.feature_name == "delinquencies_2y":
                suggestions.append(
                    "Maintain consistent payment history to reduce delinquency impact over time"
                )
            elif contrib.feature_name == "inquiries_6m":
                suggestions.append(
                    "Limit new credit applications to reduce hard inquiry impact"
                )
            elif contrib.feature_name == "employment_length_years":
                suggestions.append(
                    "Build employment stability to strengthen overall financial profile"
                )
            elif contrib.feature_name == "loan_amount":
                suggestions.append(
                    "Consider requesting a smaller loan amount to reduce risk exposure"
                )
        
        # Phase 4D Explainability - Generic advice if no specific suggestions
        if not suggestions:
            if risk_band == "medium":
                suggestions.append(
                    "Continue maintaining current financial behaviors to strengthen profile"
                )
            elif risk_band == "high":
                suggestions.append(
                    "Focus on building emergency savings and reducing debt burden"
                )
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def explain_prediction(
        self,
        shap_values: np.ndarray,
        feature_names: List[str],
        feature_values: Dict[str, Any],
        prediction_probability: float
    ) -> ExplanationResult:
        """
        Phase 4D Explainability - Generate complete explanation from SHAP values
        
        Args:
            shap_values: SHAP contribution values for each feature
            feature_names: Ordered list of feature names
            feature_values: Dictionary of feature values
            prediction_probability: Model's predicted default probability
            
        Returns:
            ExplanationResult with all explanation components
        """
        # Phase 4D Explainability - Determine risk band
        risk_band, risk_description = self.get_risk_band(prediction_probability)
        
        # Phase 4D Explainability - Sort features by absolute SHAP value
        sorted_indices = np.argsort(np.abs(shap_values))[::-1]
        
        positive_contributions = []
        negative_contributions = []
        
        # Phase 4D Explainability - Categorize contributions
        for idx in sorted_indices:
            feature_name = feature_names[idx]
            shap_val = shap_values[idx]
            feature_val = feature_values.get(feature_name, "N/A")
            
            impact = "positive" if shap_val < 0 else "negative"  # Negative SHAP = lower risk = positive
            magnitude = self.categorize_shap_magnitude(shap_val, shap_values)
            explanation = self.generate_feature_explanation(
                feature_name, feature_val, shap_val, impact
            )
            
            contrib = FeatureContribution(
                feature_name=feature_name,
                human_name=self.feature_mapping.get(feature_name, feature_name),
                shap_value=float(shap_val),
                feature_value=feature_val,
                impact=impact,
                magnitude=magnitude,
                explanation=explanation
            )
            
            if impact == "positive":
                positive_contributions.append(contrib)
            else:
                negative_contributions.append(contrib)
        
        # Phase 4D Explainability - Limit to top 3 per category
        top_positive = positive_contributions[:3]
        top_negative = negative_contributions[:3]
        
        # Phase 4D Explainability - Generate natural language sections
        what_helped = [c.explanation for c in top_positive]
        what_hurt = [c.explanation for c in top_negative]
        how_to_improve = self.generate_improvement_suggestions(top_negative, risk_band)
        
        return ExplanationResult(
            top_positive_features=top_positive,
            top_negative_features=top_negative,
            risk_band=risk_band,
            risk_band_description=risk_description,
            what_helped=what_helped if what_helped else ["Overall financial profile is stable"],
            what_hurt=what_hurt if what_hurt else ["No significant risk factors identified"],
            how_to_improve=how_to_improve if how_to_improve else ["Maintain current financial practices"],
            disclaimer=self.disclaimer
        )


# Phase 4D Explainability - Singleton instance
_explainability_service = None

def get_explainability_service() -> ExplainabilityService:
    """Phase 4D Explainability - Get or create explainability service instance"""
    global _explainability_service
    if _explainability_service is None:
        _explainability_service = ExplainabilityService()
    return _explainability_service
