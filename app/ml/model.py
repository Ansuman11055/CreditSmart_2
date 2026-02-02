"""ML model wrapper for credit risk prediction.

This module provides a unified interface for credit risk models,
whether rule-based, statistical, or deep learning.
"""

import logging
from typing import Optional
from app.schemas.request import CreditRiskRequest
from app.schemas.response import CreditRiskResponse
from app.ml.inference import CreditRiskInferenceEngine
from app.ml.ml_inference import MLInferenceEngine, ModelNotFoundError

logger = logging.getLogger(__name__)


class CreditRiskModel:
    """Unified model interface for credit risk prediction.
    
    This class wraps the underlying inference engine and provides
    a stable API for prediction endpoints. It allows swapping between
    different model implementations without changing downstream code.
    """

    def __init__(self, model_path: Optional[str] = None, use_ml_model: bool = True):
        """Initialize the credit risk model.
        
        Args:
            model_path: Optional path to trained model artifacts directory.
                       If None, uses "models" directory.
            use_ml_model: If True, attempts to load trained ML model.
                         If False or loading fails, falls back to rule-based engine.
        """
        self.model_path = model_path or "models"
        self.use_ml_model = use_ml_model
        self.ml_engine = None
        self.rule_engine = None
        self.is_loaded = False
        
        # Try to load ML model if requested
        if use_ml_model:
            try:
                logger.info(f"Attempting to load ML model from {self.model_path}")
                self.ml_engine = MLInferenceEngine(model_dir=self.model_path)
                self.is_loaded = True
                logger.info("✓ ML model loaded successfully")
            except ModelNotFoundError as e:
                logger.warning(f"ML model not found: {e}")
                logger.info("Falling back to rule-based engine")
                self.use_ml_model = False
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
                logger.info("Falling back to rule-based engine")
                self.use_ml_model = False
        
        # Initialize rule-based engine as fallback
        if not self.use_ml_model:
            logger.info("Initializing rule-based inference engine")
            self.rule_engine = CreditRiskInferenceEngine()
            self.is_loaded = True

    def predict(self, request: CreditRiskRequest) -> CreditRiskResponse:
        """Generate credit risk prediction.
        
        This method delegates to either the ML model or rule-based engine
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

        # Use ML model if available
        if self.use_ml_model and self.ml_engine is not None:
            try:
                # Get prediction and probability from ML model
                import time
                model_start = time.time()
                prediction, probability = self.ml_engine.predict(request)
                model_time = time.time() - model_start
                
                # Log model inference details
                logger.info(
                    "ml_inference_complete",
                    model_type="ml",
                    prediction=prediction,
                    probability=f"{probability:.4f}",
                    inference_time_ms=f"{model_time * 1000:.2f}",
                    credit_score=request.credit_score,
                    loan_amount=request.loan_amount,
                )
                
                # Convert to CreditRiskResponse format using factory method
                # risk_score is the probability of default (0.0 to 1.0)
                risk_score = probability
                
                # Build explanation
                explanation = (
                    f"ML model prediction: {'Default' if prediction == 1 else 'No Default'} "
                    f"with {probability:.1%} confidence. "
                    f"Risk score: {probability:.4f} (0=safe, 1=risky). "
                )
                
                # Add context based on key factors
                factors = []
                if request.credit_score < 650:
                    factors.append("low credit score")
                if request.compute_dti() > 0.40:
                    factors.append("high debt-to-income ratio")
                if request.delinquencies_2y > 0:
                    factors.append("recent delinquencies")
                
                if factors:
                    explanation += f"Key concerns: {', '.join(factors)}."
                
                # Use factory method to create response with automatic field derivation
                return CreditRiskResponse.from_risk_score(
                    risk_score=round(risk_score, 4),
                    model_version="ml_v1.0.0",
                    explanation=explanation,
                    key_factors={
                        "prediction": prediction,
                        "probability": round(probability, 4),
                        "credit_score": request.credit_score,
                        "dti": round(request.compute_dti(), 3),
                    }
                )
                
            except Exception as e:
                logger.error(f"ML prediction failed: {e}, falling back to rule-based engine")
                # Fall back to rule-based engine on error
                if self.rule_engine is None:
                    self.rule_engine = CreditRiskInferenceEngine()
                return self.rule_engine.predict(request)
        
        # Use rule-based engine (fallback)
        return self.rule_engine.predict(request)

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
            Dictionary with model metadata (safe for public exposure)
        """
        if self.use_ml_model and self.ml_engine is not None:
            # Get metadata from ML engine
            ml_info = self.ml_engine.get_model_info()
            return {
                "model_type": ml_info.get("model_type", "unknown"),
                "model_name": ml_info.get("model_name", "unknown"),
                "training_timestamp": ml_info.get("training_timestamp", "unknown"),
                "feature_count": ml_info.get("feature_count", 0),
                "schema_version": ml_info.get("schema_version", "unknown"),
                "evaluation_metrics": ml_info.get("evaluation_metrics", {}),
                "is_loaded": ml_info.get("is_loaded", False),
                "engine": "ml",
                "model_version": "ml_v1.0.0",  # Add model_version field
            }
        else:
            # Rule-based engine metadata
            return {
                "model_type": "rule_based",
                "model_name": "deterministic_engine",
                "training_timestamp": "N/A",
                "feature_count": 6,
                "schema_version": "N/A",
                "evaluation_metrics": {},
                "is_loaded": self.is_loaded,
                "engine": "rule_based",
                "model_version": "rule_v1.0.0",  # Add model_version field
            }


# Global model instance (singleton pattern for API)
# This allows the model to be loaded once and reused across requests
_model_instance: Optional[CreditRiskModel] = None


def set_model_instance(model: CreditRiskModel) -> None:
    """Set global model instance (called during startup).
    
    Args:
        model: Model instance to set as global
    """
    global _model_instance
    _model_instance = model
    model_loaded = model.is_loaded if model else False
    logger.info(f"Model instance set, model_loaded={model_loaded}")


def get_model() -> CreditRiskModel:
    """Get global model instance (singleton pattern).
    
    Returns:
        CreditRiskModel: Global model instance
        
    Raises:
        RuntimeError: If model is not loaded and startup safety didn't run
        
    Note:
        Model should be preloaded during startup via startup_safety module.
        Lazy loading is NOT used in production for predictable behavior.
    """
    global _model_instance
    
    if _model_instance is None:
        # This should never happen in production if startup checks ran
        logger.error(
            "Model accessed before startup initialization. "
            "This indicates a configuration error.",
            extra={"event": "model_not_initialized"}
        )
        raise RuntimeError(
            "Model not initialized. Application may not have started correctly. "
            "Please check health endpoint for diagnostics."
        )
    
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


def _reset_model_instance() -> None:
    """Reset the global model instance to None.
    
    FOR TESTING ONLY. This function is used by test fixtures to ensure
    clean state between test sessions.
    
    Warning:
        Never call this in production code! It will break all predictions.
    """
    global _model_instance
    _model_instance = None
