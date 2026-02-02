"""Production-safe ML model inference for credit risk prediction.

This module provides strict schema validation and error handling for
loading and running trained ML models in production environments.
"""

import os
import logging
import math
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import joblib
import numpy as np

from app.schemas.request import CreditRiskRequest

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Raised when input data doesn't match expected schema."""
    pass


class ModelNotFoundError(Exception):
    """Raised when model artifacts are not found."""
    pass


class MLInferenceEngine:
    """Production-safe ML inference engine with strict schema validation.
    
    This engine loads trained ML models (RandomForest, XGBoost, etc.) and
    provides type-safe prediction with comprehensive validation.
    
    Features:
    - Strict input schema validation (column presence, data types)
    - Fail-fast error handling with descriptive messages
    - Logging of input shapes and feature names
    - Returns both binary prediction and probability
    - No silent column dropping
    """

    def __init__(self, model_dir: str = "models"):
        """Initialize ML inference engine.
        
        Args:
            model_dir: Directory containing model artifacts
            
        Raises:
            ModelNotFoundError: If model artifacts are not found
        """
        self.model_dir = Path(model_dir)
        self.model = None
        self.preprocessor = None
        self.feature_names = None
        self.schema_version = None
        self.metadata = None  # Store full model metadata
        self._is_loaded = False
        
        # Load model artifacts
        self._load_artifacts()
    
    def _load_artifacts(self) -> None:
        """Load model and preprocessor from disk.
        
        Raises:
            ModelNotFoundError: If required artifacts are missing
            RuntimeError: If artifacts are corrupted or incompatible
        """
        model_path = self.model_dir / "model.joblib"
        preprocessor_path = self.model_dir / "preprocessor.joblib"
        
        # Check file existence
        if not model_path.exists():
            raise ModelNotFoundError(
                f"Model file not found at {model_path}. "
                "Please train the model first using: python -m src.train"
            )
        
        if not preprocessor_path.exists():
            raise ModelNotFoundError(
                f"Preprocessor file not found at {preprocessor_path}. "
                "Please train the model first to generate preprocessing artifacts."
            )
        
        try:
            # Load model
            logger.info(f"Loading model from {model_path}")
            model_artifact = joblib.load(model_path)
            
            if isinstance(model_artifact, dict):
                self.model = model_artifact.get("model")
                self.feature_names = model_artifact.get("feature_names")
                self.schema_version = model_artifact.get("schema_version")
                model_name = model_artifact.get("model_name", "unknown")
                
                # Load metadata (new format with comprehensive tracking)
                self.metadata = model_artifact.get("metadata", {
                    "model_type": model_artifact.get("model_class", "unknown"),
                    "model_name": model_name,
                    "training_timestamp": "unknown",
                    "feature_count": len(self.feature_names) if self.feature_names else 0,
                    "schema_version": self.schema_version,
                    "evaluation_metrics": model_artifact.get("metrics", {}),
                })
                
                logger.info(f"✓ Loaded model: {model_name} (schema v{self.schema_version})")
            else:
                # Legacy format: direct model object
                self.model = model_artifact
                logger.warning("Loaded legacy model format (no metadata)")
            
            # Load preprocessor
            logger.info(f"Loading preprocessor from {preprocessor_path}")
            preprocessor_artifact = joblib.load(preprocessor_path)
            
            if isinstance(preprocessor_artifact, dict):
                self.preprocessor = preprocessor_artifact.get("pipeline")
                if self.feature_names is None:
                    self.feature_names = preprocessor_artifact.get("feature_names")
                if self.schema_version is None:
                    self.schema_version = preprocessor_artifact.get("schema_version")
                logger.info(f"✓ Loaded preprocessor with {len(self.feature_names)} features")
            else:
                # Legacy format: direct pipeline object
                self.preprocessor = preprocessor_artifact
                logger.warning("Loaded legacy preprocessor format (no metadata)")
            
            # Validate loaded artifacts
            if self.model is None:
                raise RuntimeError("Model artifact is None after loading")
            
            if self.preprocessor is None:
                raise RuntimeError("Preprocessor artifact is None after loading")
            
            if self.feature_names is None:
                raise RuntimeError(
                    "Feature names not found in artifacts. "
                    "Model was trained with old version. Please retrain."
                )
            
            logger.info(f"✓ Model artifacts loaded successfully")
            logger.info(f"  Features: {len(self.feature_names)}")
            logger.info(f"  Schema version: {self.schema_version}")
            logger.info(f"  Feature names: {', '.join(self.feature_names[:5])}...")
            
            self._is_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load model artifacts: {str(e)}")
            raise RuntimeError(
                f"Failed to load model artifacts: {str(e)}. "
                "Please check that the model was trained correctly."
            ) from e
    
    def _validate_input_schema(self, df: pd.DataFrame) -> None:
        """Validate input DataFrame against expected schema.
        
        Args:
            df: Input DataFrame to validate
            
        Raises:
            SchemaValidationError: If schema validation fails
        """
        # Check column presence
        input_columns = set(df.columns)
        expected_columns = set(self.feature_names[:11])  # Raw input features (before preprocessing)
        
        # For strict validation, we need the raw feature names plus engineered features
        # These are the 12 features before one-hot encoding (11 raw + 1 computed)
        raw_features = [
            'annual_income', 'monthly_debt', 'credit_score', 'loan_amount',
            'loan_term_months', 'employment_length_years', 'home_ownership',
            'purpose', 'number_of_open_accounts', 'delinquencies_2y', 'inquiries_6m',
            'debt_to_income_ratio'  # Computed feature
        ]
        expected_columns = set(raw_features)
        
        missing_columns = expected_columns - input_columns
        extra_columns = input_columns - expected_columns
        
        if missing_columns:
            raise SchemaValidationError(
                f"Missing required columns: {sorted(missing_columns)}. "
                f"Expected columns: {sorted(expected_columns)}"
            )
        
        if extra_columns:
            raise SchemaValidationError(
                f"Unexpected columns found: {sorted(extra_columns)}. "
                f"Expected columns: {sorted(expected_columns)}. "
                f"Extra columns are not allowed to prevent silent errors."
            )
        
        # Validate data types
        dtype_errors = []
        
        numeric_features = [
            'annual_income', 'monthly_debt', 'credit_score', 'loan_amount',
            'loan_term_months', 'employment_length_years', 
            'number_of_open_accounts', 'delinquencies_2y', 'inquiries_6m',
            'debt_to_income_ratio'  # Computed numeric feature
        ]
        
        categorical_features = ['home_ownership', 'purpose']
        
        for col in numeric_features:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    dtype_errors.append(
                        f"Column '{col}' must be numeric, got {df[col].dtype}"
                    )
        
        for col in categorical_features:
            if col in df.columns:
                if not (pd.api.types.is_string_dtype(df[col]) or 
                       pd.api.types.is_object_dtype(df[col])):
                    dtype_errors.append(
                        f"Column '{col}' must be string/object, got {df[col].dtype}"
                    )
        
        if dtype_errors:
            raise SchemaValidationError(
                f"Data type validation failed:\n" + "\n".join(dtype_errors)
            )
        
        logger.info("✓ Input schema validation passed")
    
    def _validate_prediction_outputs(self, prediction: int, probability: float) -> None:
        """Validate prediction outputs for NaN, inf, and edge cases.
        
        This is a critical sanity check for financial risk systems.
        
        Args:
            prediction: Binary prediction (0 or 1)
            probability: Probability of default (0.0 to 1.0)
            
        Raises:
            RuntimeError: If outputs contain NaN, inf, or invalid values
        """
        # Check for NaN values
        if math.isnan(prediction):
            logger.error("CRITICAL: prediction_sanity_check_failed - prediction is NaN")
            raise RuntimeError(
                "CRITICAL: Model returned NaN prediction. "
                "This indicates a serious model error. Please contact support."
            )
        
        if math.isnan(probability):
            logger.error("CRITICAL: prediction_sanity_check_failed - probability is NaN")
            raise RuntimeError(
                "CRITICAL: Model returned NaN probability. "
                "This indicates a serious model error. Please contact support."
            )
        
        # Check for infinite values
        if math.isinf(prediction):
            logger.error("CRITICAL: prediction_sanity_check_failed - prediction is infinite")
            raise RuntimeError(
                "CRITICAL: Model returned infinite prediction. "
                "This indicates a serious model error. Please contact support."
            )
        
        if math.isinf(probability):
            logger.error("CRITICAL: prediction_sanity_check_failed - probability is infinite")
            raise RuntimeError(
                "CRITICAL: Model returned infinite probability. "
                "This indicates a serious model error. Please contact support."
            )
        
        # Validate prediction is 0 or 1
        if prediction not in [0, 1]:
            logger.error(
                f"CRITICAL: prediction_sanity_check_failed - invalid prediction value: {prediction}"
            )
            raise RuntimeError(
                f"CRITICAL: Model returned invalid prediction: {prediction}. "
                "Expected 0 (no default) or 1 (default). Please contact support."
            )
        
        # Validate probability is in [0, 1]
        if not (0.0 <= probability <= 1.0):
            logger.error(
                f"CRITICAL: prediction_sanity_check_failed - probability out of range: {probability}"
            )
            raise RuntimeError(
                f"CRITICAL: Model returned invalid probability: {probability}. "
                "Expected value between 0.0 and 1.0. Please contact support."
            )
        
        # Warn about edge cases (extremely confident predictions)
        if probability == 0.0:
            logger.warning(
                f"Edge case: probability is exactly 0.0 for prediction {prediction}. "
                "Model is 100% confident of no default - rare in real scenarios"
            )
        
        if probability == 1.0:
            logger.warning(
                f"Edge case: probability is exactly 1.0 for prediction {prediction}. "
                "Model is 100% confident of default - rare in real scenarios"
            )
        
        # Log successful validation
        logger.debug(
            f"Prediction sanity check passed: prediction={prediction}, probability={probability:.4f}"
        )
    
    def predict(self, request: CreditRiskRequest) -> Tuple[int, float]:
        """Generate prediction from validated request.
        
        Args:
            request: Validated CreditRiskRequest with applicant features
            
        Returns:
            Tuple of (prediction, probability):
                - prediction: Binary prediction (0=no default, 1=default)
                - probability: Probability of default (0.0 to 1.0)
                
        Raises:
            SchemaValidationError: If input doesn't match expected schema
            RuntimeError: If model is not loaded or prediction fails
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Cannot make predictions.")
        
        # Convert request to DataFrame
        input_data = {
            'annual_income': request.annual_income,
            'monthly_debt': request.monthly_debt,
            'credit_score': request.credit_score,
            'loan_amount': request.loan_amount,
            'loan_term_months': request.loan_term_months,
            'employment_length_years': request.employment_length_years,
            'home_ownership': request.home_ownership,
            'purpose': request.purpose,
            'number_of_open_accounts': request.number_of_open_accounts,
            'delinquencies_2y': request.delinquencies_2y,
            'inquiries_6m': request.inquiries_6m,
            'debt_to_income_ratio': request.compute_dti(),  # Compute DTI from income and debt
        }
        
        df = pd.DataFrame([input_data])
        
        # Log input shape and features
        logger.info(f"Prediction request - Input shape: {df.shape}")
        logger.info(f"Prediction request - Input features: {list(df.columns)}")
        logger.info(f"Prediction request - Sample values: credit_score={request.credit_score}, "
                   f"loan_amount={request.loan_amount}, dti={request.monthly_debt / (request.annual_income / 12):.2f}")
        
        # Validate input schema
        self._validate_input_schema(df)
        
        try:
            # Apply preprocessing
            logger.info("Applying preprocessing pipeline...")
            X_processed = self.preprocessor.transform(df)
            
            if hasattr(X_processed, 'shape'):
                logger.info(f"✓ Preprocessing complete - Output shape: {X_processed.shape}")
            
            # Generate prediction
            logger.info("Generating model prediction...")
            
            # Binary prediction
            prediction = self.model.predict(X_processed)[0]
            prediction = int(prediction)  # Ensure integer type
            
            # Probability prediction
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X_processed)[0]
                # Get probability of positive class (default)
                probability = float(proba[1])
            else:
                # Fallback for models without predict_proba
                logger.warning("Model doesn't support predict_proba, using binary prediction")
                probability = float(prediction)
            
            # CRITICAL: Runtime sanity checks for financial risk system
            # Validate outputs before returning to prevent NaN/inf propagation
            try:
                self._validate_prediction_outputs(prediction, probability)
            except RuntimeError as validation_error:
                # Log critical error and re-raise with context
                logger.error(
                    f"Prediction validation failed: {validation_error}. "
                    f"Prediction={prediction}, Probability={probability}, "
                    f"Credit_score={request.credit_score}, Loan_amount={request.loan_amount}, "
                    f"DTI={request.compute_dti():.2f}"
                )
                raise validation_error
            
            logger.info(
                f"✓ Prediction complete - Result: {prediction}, "
                f"Probability: {probability:.4f}, Sanity checks: PASSED"
            )
            
            return prediction, probability
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}", exc_info=True)
            raise RuntimeError(
                f"Prediction failed during processing: {str(e)}"
            ) from e
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded model.
        
        Returns:
            Dictionary with model metadata (safe for public exposure)
        """
        if not self._is_loaded:
            return {
                "is_loaded": False,
                "error": "Model not loaded"
            }
        
        # Return safe metadata (no training data or sensitive internals)
        return {
            "is_loaded": True,
            "model_type": self.metadata.get("model_type", type(self.model).__name__) if self.metadata else type(self.model).__name__,
            "model_name": self.metadata.get("model_name", "unknown") if self.metadata else "unknown",
            "training_timestamp": self.metadata.get("training_timestamp", "unknown") if self.metadata else "unknown",
            "feature_count": self.metadata.get("feature_count", len(self.feature_names)) if self.metadata else len(self.feature_names) if self.feature_names else 0,
            "schema_version": self.metadata.get("schema_version", self.schema_version) if self.metadata else self.schema_version,
            "evaluation_metrics": self.metadata.get("evaluation_metrics", {}) if self.metadata else {},
            "model_dir": str(self.model_dir),
        }
