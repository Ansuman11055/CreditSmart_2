"""Trust & Explainability Layer for ML predictions.

Phase 4A: SHAP-based feature importance with human-readable explanations.

This module provides interpretable explanations for credit risk predictions
by computing SHAP (SHapley Additive exPlanations) values and converting them
into clear, actionable insights.

Features:
- Safe SHAP explainer loading with fallback
- Single-prediction SHAP value computation
- Top risk contributors (positive impact)
- Top protective factors (negative impact)
- Normalized percentage-based contributions
- Clean feature name mapping (no encoded columns)
"""

import numpy as np
import joblib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import structlog

from app.schemas.request import CreditRiskRequest

logger = structlog.get_logger(__name__)


class ExplainabilityEngine:
    """SHAP-based explainability engine for credit risk predictions.
    
    This engine loads a pre-trained SHAP explainer and provides
    human-readable explanations for individual predictions.
    """
    
    def __init__(self, model_dir: str = "models"):
        """Initialize explainability engine.
        
        Args:
            model_dir: Directory containing SHAP artifacts
        """
        self.model_dir = Path(model_dir)
        self.explainer = None
        self.background_data = None
        self.feature_names = None
        self.is_available = False
        
        # Feature name mapping (encoded -> human-readable)
        self.feature_name_map = {
            "annual_income": "Annual Income",
            "monthly_debt": "Monthly Debt",
            "credit_score": "Credit Score",
            "loan_amount": "Loan Amount",
            "loan_term_months": "Loan Term",
            "employment_length_years": "Employment Length",
            "number_of_open_accounts": "Open Accounts",
            "delinquencies_2y": "Recent Delinquencies",
            "inquiries_6m": "Credit Inquiries",
            "debt_to_income_ratio": "Debt-to-Income Ratio",
            # One-hot encoded features
            "home_ownership_MORTGAGE": "Home Ownership: Mortgage",
            "home_ownership_OWN": "Home Ownership: Own",
            "home_ownership_RENT": "Home Ownership: Rent",
            "home_ownership_OTHER": "Home Ownership: Other",
            "purpose_car": "Purpose: Car Purchase",
            "purpose_credit_card": "Purpose: Credit Card",
            "purpose_debt_consolidation": "Purpose: Debt Consolidation",
            "purpose_home_improvement": "Purpose: Home Improvement",
            "purpose_major_purchase": "Purpose: Major Purchase",
            "purpose_medical": "Purpose: Medical",
            "purpose_moving": "Purpose: Moving",
            "purpose_other": "Purpose: Other",
            "purpose_small_business": "Purpose: Small Business",
            "purpose_vacation": "Purpose: Vacation",
        }
        
        self._load_shap_artifacts()
    
    def _load_shap_artifacts(self) -> None:
        """Load SHAP explainer and background data safely."""
        try:
            explainer_path = self.model_dir / "shap_explainer.joblib"
            background_path = self.model_dir / "shap_background.npy"
            
            if not explainer_path.exists():
                logger.warning(
                    "shap_explainer_not_found",
                    path=str(explainer_path),
                    message="SHAP explainer not available. Explanations will be limited."
                )
                return
            
            # Load SHAP explainer
            logger.info("loading_shap_explainer", path=str(explainer_path))
            self.explainer = joblib.load(explainer_path)
            
            # Load background data if available
            if background_path.exists():
                logger.info("loading_shap_background", path=str(background_path))
                self.background_data = np.load(background_path)
            
            self.is_available = True
            logger.info(
                "shap_explainer_loaded",
                explainer_type=type(self.explainer).__name__,
                has_background=self.background_data is not None
            )
            
        except Exception as e:
            logger.error(
                "shap_explainer_load_failed",
                error=str(e),
                exception_type=type(e).__name__,
                message="SHAP explanations will not be available"
            )
            self.is_available = False
    
    def _get_human_readable_name(self, feature_name: str) -> str:
        """Convert encoded feature name to human-readable format.
        
        Args:
            feature_name: Raw feature name (may be one-hot encoded)
            
        Returns:
            Human-readable feature name
        """
        return self.feature_name_map.get(feature_name, feature_name.replace("_", " ").title())
    
    def _prepare_input_for_shap(self, request: CreditRiskRequest) -> np.ndarray:
        """Convert request to feature array for SHAP computation.
        
        This must match the exact preprocessing used during training.
        
        Args:
            request: Credit risk request
            
        Returns:
            NumPy array ready for SHAP computation
        """
        from app.ml.model import get_model
        
        # Use the same model preprocessing pipeline
        model = get_model()
        if not model.is_loaded:
            raise RuntimeError("Model not loaded. Cannot prepare SHAP input.")
        
        # Get the ML inference engine which has the preprocessor
        if hasattr(model, 'ml_engine') and model.ml_engine is not None:
            preprocessor = model.ml_engine.preprocessor
            feature_names = model.ml_engine.feature_names
            
            # Convert request to DataFrame (same as training)
            import pandas as pd
            input_dict = request.model_dump()
            input_df = pd.DataFrame([input_dict])
            
            # Apply preprocessing
            features_processed = preprocessor.transform(input_df)
            
            # Store feature names for explanation
            self.feature_names = feature_names
            
            return features_processed
        else:
            raise RuntimeError("ML engine not available. Cannot compute SHAP values.")
    
    def explain_prediction(
        self,
        request: CreditRiskRequest,
        prediction_probability: float,
        top_n: int = 5
    ) -> Dict[str, Any]:
        """Generate SHAP-based explanation for a single prediction.
        
        Args:
            request: Credit risk request (same as prediction input)
            prediction_probability: Predicted probability from model
            top_n: Number of top features to return (default: 5)
            
        Returns:
            Dictionary with prediction and explanations:
            {
                "prediction": {
                    "probability": float,
                    "risk_label": "LOW | MEDIUM | HIGH"
                },
                "explanations": {
                    "top_risk_factors": [...],
                    "top_protective_factors": [...]
                },
                "model_confidence": "HIGH | MEDIUM | LOW"
            }
        """
        if not self.is_available:
            logger.warning("shap_not_available", message="Returning basic explanation")
            return self._fallback_explanation(request, prediction_probability)
        
        try:
            # Prepare input for SHAP
            features = self._prepare_input_for_shap(request)
            
            # Compute SHAP values
            logger.debug("computing_shap_values", features_shape=features.shape)
            shap_values = self.explainer.shap_values(features)
            
            # Handle different SHAP output formats
            if isinstance(shap_values, list):
                # Binary classification: use positive class (index 1)
                shap_values_array = shap_values[1][0]
            else:
                shap_values_array = shap_values[0]
            
            # Get base value (expected value)
            if hasattr(self.explainer, 'expected_value'):
                if isinstance(self.explainer.expected_value, (list, np.ndarray)):
                    base_value = self.explainer.expected_value[1]
                else:
                    base_value = self.explainer.expected_value
            else:
                base_value = 0.5
            
            # Compute feature contributions with names
            contributions = []
            for idx, shap_val in enumerate(shap_values_array):
                if self.feature_names and idx < len(self.feature_names):
                    feature_name = self.feature_names[idx]
                    human_name = self._get_human_readable_name(feature_name)
                    contributions.append({
                        "feature": human_name,
                        "raw_feature": feature_name,
                        "impact": float(shap_val),
                        "abs_impact": abs(float(shap_val))
                    })
            
            # Sort by absolute impact
            contributions.sort(key=lambda x: x["abs_impact"], reverse=True)
            
            # Separate positive (risk-increasing) and negative (protective)
            risk_factors = [c for c in contributions if c["impact"] > 0][:top_n]
            protective_factors = [c for c in contributions if c["impact"] < 0][:top_n]
            
            # Normalize to percentages (relative to total absolute impact)
            total_impact = sum(c["abs_impact"] for c in contributions)
            
            for factor in risk_factors:
                factor["impact_percentage"] = (factor["abs_impact"] / total_impact * 100) if total_impact > 0 else 0
                factor["direction"] = "increase"
                del factor["abs_impact"]
                del factor["raw_feature"]
            
            for factor in protective_factors:
                factor["impact_percentage"] = (factor["abs_impact"] / total_impact * 100) if total_impact > 0 else 0
                factor["direction"] = "decrease"
                # Keep impact negative for protective factors
                del factor["abs_impact"]
                del factor["raw_feature"]
            
            # Determine risk label
            if prediction_probability < 0.3:
                risk_label = "LOW"
            elif prediction_probability < 0.7:
                risk_label = "MEDIUM"
            else:
                risk_label = "HIGH"
            
            # Determine model confidence based on SHAP value spread
            shap_std = np.std([c["impact"] for c in contributions])
            if shap_std > 0.1:
                confidence = "HIGH"
            elif shap_std > 0.05:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"
            
            logger.info(
                "shap_explanation_computed",
                risk_factors_count=len(risk_factors),
                protective_factors_count=len(protective_factors),
                confidence=confidence
            )
            
            return {
                "prediction": {
                    "probability": round(prediction_probability, 4),
                    "risk_label": risk_label
                },
                "explanations": {
                    "top_risk_factors": risk_factors,
                    "top_protective_factors": protective_factors
                },
                "model_confidence": confidence,
                "base_value": round(float(base_value), 4)
            }
            
        except Exception as e:
            logger.error(
                "shap_computation_failed",
                error=str(e),
                exception_type=type(e).__name__
            )
            return self._fallback_explanation(request, prediction_probability)
    
    def _fallback_explanation(
        self,
        request: CreditRiskRequest,
        prediction_probability: float
    ) -> Dict[str, Any]:
        """Generate rule-based explanation when SHAP is unavailable.
        
        Args:
            request: Credit risk request
            prediction_probability: Predicted probability
            
        Returns:
            Basic explanation based on heuristics
        """
        # Determine risk label
        if prediction_probability < 0.3:
            risk_label = "LOW"
        elif prediction_probability < 0.7:
            risk_label = "MEDIUM"
        else:
            risk_label = "HIGH"
        
        # Simple heuristic factors
        risk_factors = []
        protective_factors = []
        
        # Credit score analysis
        if request.credit_score < 650:
            risk_factors.append({
                "feature": "Credit Score",
                "impact": 0.15,
                "impact_percentage": 25.0,
                "direction": "increase"
            })
        elif request.credit_score > 750:
            protective_factors.append({
                "feature": "Credit Score",
                "impact": -0.15,
                "impact_percentage": 25.0,
                "direction": "decrease"
            })
        
        # DTI analysis
        dti = request.compute_dti()
        if dti > 0.40:
            risk_factors.append({
                "feature": "Debt-to-Income Ratio",
                "impact": 0.12,
                "impact_percentage": 20.0,
                "direction": "increase"
            })
        elif dti < 0.25:
            protective_factors.append({
                "feature": "Debt-to-Income Ratio",
                "impact": -0.12,
                "impact_percentage": 20.0,
                "direction": "decrease"
            })
        
        # Delinquencies
        if request.delinquencies_2y > 0:
            risk_factors.append({
                "feature": "Recent Delinquencies",
                "impact": 0.10,
                "impact_percentage": 18.0,
                "direction": "increase"
            })
        
        # Employment stability
        if request.employment_length_years > 5:
            protective_factors.append({
                "feature": "Employment Length",
                "impact": -0.08,
                "impact_percentage": 15.0,
                "direction": "decrease"
            })
        
        return {
            "prediction": {
                "probability": round(prediction_probability, 4),
                "risk_label": risk_label
            },
            "explanations": {
                "top_risk_factors": risk_factors[:5],
                "top_protective_factors": protective_factors[:5]
            },
            "model_confidence": "MEDIUM",
            "base_value": 0.5,
            "note": "SHAP explainer unavailable. Using heuristic explanations."
        }


# Global singleton instance
_explainability_engine: Optional[ExplainabilityEngine] = None


def get_explainability_engine() -> ExplainabilityEngine:
    """Get global explainability engine instance.
    
    Returns:
        Singleton ExplainabilityEngine instance
    """
    global _explainability_engine
    
    if _explainability_engine is None:
        _explainability_engine = ExplainabilityEngine()
    
    return _explainability_engine
