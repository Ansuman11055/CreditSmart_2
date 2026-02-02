"""Data preprocessing pipeline for credit risk prediction.

This module handles data preprocessing including:
- Loading raw data
- Validation against feature schema
- Handling missing values
- Feature engineering
- Scaling and encoding

Uses sklearn Pipelines for deterministic, reusable transformations.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import logging
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

from src.core.feature_schema import (
    FEATURE_NAMES,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET,
    SCHEMA_VERSION,
)
from src.core.validation import validate_training_data, ValidationError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Preprocessor for credit risk prediction data.
    
    Handles validation, cleaning, and transformation of raw data
    according to the feature schema. Uses sklearn pipelines for
    reproducible transformations.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize preprocessor.
        
        Args:
            data_dir: Base directory for data files
        """
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.models_dir = Path("models")
        
        # Create directories if they don't exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Preprocessing pipeline (fitted during training)
        self.preprocessing_pipeline = None
        self.feature_columns = None  # Track feature order after transformation
        
        logger.info(f"DataPreprocessor initialized with schema version {SCHEMA_VERSION}")
    
    def load_and_validate(self, filename: str) -> pd.DataFrame:
        """Load raw data and validate against feature schema.
        
        Args:
            filename: Name of CSV file in raw data directory
            
        Returns:
            Validated DataFrame
            
        Raises:
            ValidationError: If data fails validation
            FileNotFoundError: If file doesn't exist
        """
        filepath = self.raw_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Raw data file not found: {filepath}")
        
        logger.info(f"Loading raw data from {filepath}")
        df = pd.read_csv(filepath)
        
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
        
        # Strict validation before processing
        logger.info("Validating data against feature schema...")
        try:
            validate_training_data(df)
            logger.info("✓ Validation passed")
        except ValidationError as e:
            logger.error(f"✗ Validation failed: {e}")
            raise
        
        return df
    
    def preprocess(
        self, df: pd.DataFrame, fit: bool = True, save_output: bool = True
    ) -> Tuple[pd.DataFrame, np.ndarray, dict]:
        """Preprocess validated data using sklearn pipelines.
        
        Args:
            df: Validated DataFrame
            fit: Whether to fit the pipeline (True for training, False for inference)
            save_output: Whether to save processed data and pipeline to disk
            
        Returns:
            Tuple of (processed features DataFrame, target array, metadata)
        """
        logger.info("Starting preprocessing pipeline...")
        
        # Select only schema-defined features + target
        # NO hardcoded column names - using feature schema!
        df = df[FEATURE_NAMES + [TARGET]].copy()
        
        # Feature engineering before pipeline
        df = self._engineer_features(df)
        
        # Update feature lists to include engineered features
        numeric_features = NUMERIC_FEATURES.copy()
        if "debt_to_income_ratio" in df.columns:
            numeric_features.append("debt_to_income_ratio")
        
        categorical_features = CATEGORICAL_FEATURES.copy()
        
        # Separate features and target
        X = df.drop(columns=[TARGET])
        y = df[TARGET].values
        
        if fit:
            # Build and fit preprocessing pipeline during training
            logger.info("Fitting preprocessing pipeline...")
            self.preprocessing_pipeline = self._build_pipeline(
                numeric_features, categorical_features
            )
            X_transformed = self.preprocessing_pipeline.fit_transform(X)
            
            # Store feature names after transformation
            self.feature_columns = self._get_feature_names_after_transform(
                self.preprocessing_pipeline, numeric_features, categorical_features
            )
            
            logger.info(f"Pipeline fitted. Output features: {len(self.feature_columns)}")
            
            # Save pipeline if requested
            if save_output:
                self._save_pipeline()
        else:
            # Use pre-fitted pipeline during inference
            if self.preprocessing_pipeline is None:
                raise ValueError(
                    "Preprocessing pipeline not fitted. Set fit=True or load a fitted pipeline."
                )
            logger.info("Applying pre-fitted preprocessing pipeline...")
            X_transformed = self.preprocessing_pipeline.transform(X)
        
        # Convert to DataFrame with feature names
        X_processed = pd.DataFrame(
            X_transformed,
            columns=self.feature_columns,
            index=X.index
        )
        
        metadata = {
            "schema_version": SCHEMA_VERSION,
            "n_records": len(df),
            "n_input_features": len(FEATURE_NAMES),
            "n_output_features": len(self.feature_columns),
            "numeric_features": numeric_features,
            "categorical_features": categorical_features,
            "pipeline_fitted": fit,
        }
        
        # Log preprocessing summary
        logger.info(
            f"Preprocessing complete: {len(X_processed)} records, "
            f"{len(X_processed.columns)} features"
        )
        
        if save_output and fit:
            output_path = self.processed_dir / "processed_data.csv"
            output_df = X_processed.copy()
            output_df[TARGET] = y
            output_df.to_csv(output_path, index=False)
            logger.info(f"Saved processed data to {output_path}")
        
        return X_processed, y, metadata
    
    def _build_pipeline(
        self, numeric_features: list, categorical_features: list
    ) -> Pipeline:
        """Build sklearn preprocessing pipeline.
        
        Args:
            numeric_features: List of numeric feature names
            categorical_features: List of categorical feature names
            
        Returns:
            Fitted preprocessing pipeline
        """
        # Numeric preprocessing: impute with median, then scale
        numeric_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])
        
        # Categorical preprocessing: impute with most frequent, then one-hot encode
        categorical_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])
        
        # Combine numeric and categorical pipelines
        preprocessor = ColumnTransformer(
            transformers=[
                ("numeric", numeric_pipeline, numeric_features),
                ("categorical", categorical_pipeline, categorical_features)
            ],
            remainder="drop"  # Drop any columns not specified
        )
        
        return preprocessor
    
    def _get_feature_names_after_transform(
        self, pipeline: ColumnTransformer, numeric_features: list, categorical_features: list
    ) -> list:
        """Get feature names after transformation.
        
        Args:
            pipeline: Fitted ColumnTransformer
            numeric_features: Original numeric feature names
            categorical_features: Original categorical feature names
            
        Returns:
            List of feature names after transformation
        """
        feature_names = []
        
        # Numeric features keep their original names
        feature_names.extend(numeric_features)
        
        # Categorical features become one-hot encoded
        for i, (name, transformer, features) in enumerate(pipeline.transformers_):
            if name == "categorical":
                # Get the OneHotEncoder from the pipeline
                encoder = transformer.named_steps["encoder"]
                
                # Get feature names from encoder
                if hasattr(encoder, "get_feature_names_out"):
                    # sklearn >= 1.0
                    encoded_names = encoder.get_feature_names_out(features)
                else:
                    # Fallback for older sklearn
                    encoded_names = []
                    for j, feature in enumerate(features):
                        categories = encoder.categories_[j]
                        encoded_names.extend([f"{feature}_{cat}" for cat in categories])
                
                feature_names.extend(encoded_names)
        
        return feature_names
    
    def _save_pipeline(self) -> None:
        """Save fitted preprocessing pipeline to disk."""
        if self.preprocessing_pipeline is None:
            logger.warning("No pipeline to save - pipeline is None")
            return
        
        # Save preprocessing artifacts separately from models
        pipeline_path = self.models_dir / "preprocessor.joblib"
        
        # Create preprocessing artifact with all necessary components
        preprocessing_artifact = {
            "pipeline": self.preprocessing_pipeline,
            "feature_columns": self.feature_columns,
            "schema_version": SCHEMA_VERSION,
        }
        
        joblib.dump(preprocessing_artifact, pipeline_path)
        
        logger.info(f"✓ Successfully saved preprocessing pipeline to {pipeline_path}")
        logger.info(f"✓ Pipeline includes {len(self.feature_columns)} output features")
        logger.info(f"✓ Schema version: {SCHEMA_VERSION}")
    
    def load_pipeline(self) -> None:
        """Load fitted preprocessing pipeline from disk."""
        pipeline_path = self.models_dir / "preprocessor.joblib"
        
        if not pipeline_path.exists():
            raise FileNotFoundError(
                f"Preprocessing pipeline not found: {pipeline_path}\n"
                f"Please train the model first to generate preprocessing artifacts."
            )
        
        logger.info(f"Loading preprocessing pipeline from {pipeline_path}...")
        preprocessing_artifact = joblib.load(pipeline_path)
        
        # Extract components from artifact
        self.preprocessing_pipeline = preprocessing_artifact["pipeline"]
        self.feature_columns = preprocessing_artifact["feature_columns"]
        artifact_schema_version = preprocessing_artifact.get("schema_version", "unknown")
        
        logger.info(f"✓ Successfully loaded preprocessing pipeline")
        logger.info(f"✓ Pipeline has {len(self.feature_columns)} output features")
        logger.info(f"✓ Artifact schema version: {artifact_schema_version}")
        
        # Warn if schema versions don't match
        if artifact_schema_version != SCHEMA_VERSION:
            logger.warning(
                f"Schema version mismatch: artifact={artifact_schema_version}, current={SCHEMA_VERSION}"
            )
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer derived features.
        
        Args:
            df: DataFrame with base features
            
        Returns:
            DataFrame with additional engineered features
        """
        # Calculate debt-to-income ratio if not present
        if "annual_income" in df.columns and "monthly_debt" in df.columns:
            monthly_income = df["annual_income"] / 12
            df["debt_to_income_ratio"] = (df["monthly_debt"] / monthly_income.replace(0, np.nan)) * 100
            df["debt_to_income_ratio"] = df["debt_to_income_ratio"].fillna(0).clip(0, 100)
            logger.info("Engineered feature: debt_to_income_ratio")
        
        return df


def preprocess_training_data(
    raw_filename: str = "raw.csv", data_dir: str = "data"
) -> Tuple[pd.DataFrame, np.ndarray, dict, DataPreprocessor]:
    """Convenience function to preprocess training data.
    
    Args:
        raw_filename: Name of raw CSV file
        data_dir: Base data directory
        
    Returns:
        Tuple of (processed features DataFrame, target array, metadata, fitted preprocessor)
        
    Raises:
        ValidationError: If validation fails
    """
    preprocessor = DataPreprocessor(data_dir=data_dir)
    
    # Load and validate (strict validation enforced)
    df = preprocessor.load_and_validate(raw_filename)
    
    # Preprocess and fit pipeline
    X_processed, y, metadata = preprocessor.preprocess(df, fit=True, save_output=True)
    
    return X_processed, y, metadata, preprocessor


def preprocess_inference_data(
    df: pd.DataFrame, preprocessor: Optional[DataPreprocessor] = None
) -> pd.DataFrame:
    """Preprocess inference data using pre-fitted pipeline.
    
    Args:
        df: Raw inference DataFrame
        preprocessor: Fitted DataPreprocessor instance (will load from disk if None)
        
    Returns:
        Processed features DataFrame
        
    Raises:
        ValidationError: If validation fails
    """
    if preprocessor is None:
        preprocessor = DataPreprocessor()
        preprocessor.load_pipeline()
    
    # Add dummy target column for preprocessing (will be dropped)
    df_with_target = df.copy()
    if TARGET not in df_with_target.columns:
        df_with_target[TARGET] = 0  # Dummy value
    
    # Preprocess using fitted pipeline
    X_processed, _, _ = preprocessor.preprocess(
        df_with_target, fit=False, save_output=False
    )
    
    return X_processed


if __name__ == "__main__":
    # Example usage
    try:
        X, y, metadata, preprocessor = preprocess_training_data()
        print(f"✓ Preprocessing successful!")
        print(f"  Records: {metadata['n_records']}")
        print(f"  Input features: {metadata['n_input_features']}")
        print(f"  Output features: {metadata['n_output_features']}")
        print(f"  Schema version: {metadata['schema_version']}")
        print(f"  X shape: {X.shape}")
        print(f"  y shape: {y.shape}")
    except ValidationError as e:
        print(f"✗ Preprocessing failed: {e}")
    except FileNotFoundError as e:
        print(f"✗ File error: {e}")
