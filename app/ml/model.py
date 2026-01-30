"""ML model wrapper for credit risk prediction.

This module provides a unified interface for credit risk models,
whether rule-based, statistical, or deep learning.
"""

from typing import Optional
from app.schemas.request import CreditRiskRequest
from app.schemas.response import CreditRiskResponse
from app.ml.inference import CreditRiskInferenceEngine


class CreditRiskModel:
    """Unified model interface for credit risk prediction.
    
    This class wraps the underlying inference engine and provides
    a stable API for prediction endpoints. It allows swapping between
    different model implementations without changing downstream code.
    """

    def __init__(self, model_path: Optional[str] = None):
        """Initialize the credit risk model.
        
        Args:
            model_path: Optional path to trained model artifacts.
                       If None, uses the deterministic rule-based engine.
        """
        # Currently using deterministic engine
        # Future: Load trained model from model_path if provided
        self.engine = CreditRiskInferenceEngine()
        self.model_path = model_path
        self.is_loaded = True

    def predict(self, request: CreditRiskRequest) -> CreditRiskResponse:
        """Generate credit risk prediction.
        
        This method delegates to the underlying inference engine
        while providing a consistent interface.
        
        Args:
            request: Validated credit risk request
            
        Returns:
            CreditRiskResponse with risk assessment
            
        Raises:
            RuntimeError: If model is not loaded
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Delegate to inference engine
        return self.engine.predict(request)

    def load(self, model_path: str) -> None:
        """Load model artifacts from disk.
        
        Args:
            model_path: Path to serialized model file
            
        Note:
            Currently a no-op for the deterministic engine.
            Future implementations will load trained models here.
        """
        # Placeholder for future model loading
        # e.g., self.engine = joblib.load(model_path)
        self.model_path = model_path
        self.is_loaded = True

    def get_model_info(self) -> dict:
        """Get information about the current model.
        
        Returns:
            Dictionary with model metadata
        """
        return {
            "model_type": "deterministic",
            "version": "v1.0.0",
            "model_path": self.model_path,
            "is_loaded": self.is_loaded,
            "features": [
                "credit_score",
                "debt_to_income",
                "employment_length",
                "delinquencies",
                "inquiries",
                "open_accounts",
            ],
        }


# Global model instance (singleton pattern for API)
# This allows the model to be loaded once and reused across requests
_model_instance: Optional[CreditRiskModel] = None


def get_model() -> CreditRiskModel:
    """Get or create the global model instance.
    
    This function implements lazy initialization and ensures
    only one model instance exists (singleton pattern).
    
    Returns:
        CreditRiskModel instance ready for predictions
    """
    global _model_instance
    if _model_instance is None:
        _model_instance = CreditRiskModel()
    return _model_instance


def reload_model(model_path: Optional[str] = None) -> CreditRiskModel:
    """Reload the global model instance.
    
    Use this function to hot-swap models without restarting the server.
    
    Args:
        model_path: Optional path to new model artifacts
        
    Returns:
        Newly loaded CreditRiskModel instance
    """
    global _model_instance
    _model_instance = CreditRiskModel(model_path=model_path)
    if model_path:
        _model_instance.load(model_path)
    return _model_instance
