"""Input validation for credit risk prediction pipeline.

This module provides strict validation of input data against the feature schema.
All validation failures raise descriptive exceptions to prevent silent failures.
"""

from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np

from src.core.feature_schema import (
    FeatureSchema,
    FeatureType,
    DataType,
    FEATURE_NAMES,
    REQUIRED_FEATURES,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET,
)


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


class DataValidator:
    """Validator for credit risk prediction inputs.
    
    Performs strict validation of input data against the feature schema.
    Raises descriptive errors for any validation failures.
    """
    
    def __init__(self):
        """Initialize validator with feature schema."""
        self.schema = FeatureSchema
        
    def validate_dataframe(
        self,
        df: pd.DataFrame,
        require_target: bool = True,
        allow_extra_columns: bool = False,
    ) -> None:
        """Validate a pandas DataFrame against feature schema.
        
        Args:
            df: DataFrame to validate
            require_target: Whether to require target column (False for inference)
            allow_extra_columns: Whether to allow extra columns beyond schema
            
        Raises:
            ValidationError: If validation fails with descriptive message
        """
        if df.empty:
            raise ValidationError("DataFrame is empty. Cannot validate empty data.")
        
        # Check for required features
        self._check_required_columns(df, require_target)
        
        # Check for unexpected columns
        if not allow_extra_columns:
            self._check_extra_columns(df, require_target)
        
        # Validate data types for each column
        self._validate_column_types(df)
        
        # Validate value ranges and constraints
        self._validate_value_constraints(df)
        
        # Check for excessive missing values in optional features
        self._check_missing_values(df)
        
    def validate_dict(
        self,
        data: Dict[str, Any],
        require_target: bool = False,
    ) -> None:
        """Validate a dictionary (single record) against feature schema.
        
        Useful for API request validation during inference.
        
        Args:
            data: Dictionary with feature values
            require_target: Whether to require target value
            
        Raises:
            ValidationError: If validation fails with descriptive message
        """
        # Check required features
        missing_features = []
        for feature_name in REQUIRED_FEATURES:
            if feature_name not in data or data[feature_name] is None:
                missing_features.append(feature_name)
        
        if require_target and TARGET not in data:
            missing_features.append(TARGET)
        
        if missing_features:
            raise ValidationError(
                f"Missing required features: {', '.join(missing_features)}"
            )
        
        # Validate each feature present in data
        for feature_name, value in data.items():
            if feature_name == TARGET and not require_target:
                continue
                
            if feature_name not in FEATURE_NAMES and feature_name != TARGET:
                continue  # Skip unknown features (they'll be ignored)
            
            # Get feature definition
            if feature_name == TARGET:
                continue  # Skip target validation for now
            
            try:
                feature = self.schema.get_feature_by_name(feature_name)
            except ValueError:
                continue  # Skip unknown features
            
            # Validate type and constraints
            self._validate_single_value(feature_name, value, feature)
    
    def _check_required_columns(
        self, df: pd.DataFrame, require_target: bool
    ) -> None:
        """Check that all required columns are present.
        
        Args:
            df: DataFrame to check
            require_target: Whether target column is required
            
        Raises:
            ValidationError: If required columns are missing
        """
        required_cols = set(REQUIRED_FEATURES)
        if require_target:
            required_cols.add(TARGET)
        
        missing_cols = required_cols - set(df.columns)
        
        if missing_cols:
            raise ValidationError(
                f"Missing required columns: {', '.join(sorted(missing_cols))}. "
                f"Expected columns: {', '.join(sorted(required_cols))}"
            )
    
    def _check_extra_columns(
        self, df: pd.DataFrame, require_target: bool
    ) -> None:
        """Check for unexpected columns beyond schema.
        
        Args:
            df: DataFrame to check
            require_target: Whether target column is expected
            
        Raises:
            ValidationError: If extra columns are present
        """
        expected_cols = set(FEATURE_NAMES)
        if require_target:
            expected_cols.add(TARGET)
        
        extra_cols = set(df.columns) - expected_cols
        
        if extra_cols:
            raise ValidationError(
                f"Unexpected columns found: {', '.join(sorted(extra_cols))}. "
                f"Only schema-defined columns are allowed."
            )
    
    def _validate_column_types(self, df: pd.DataFrame) -> None:
        """Validate data types of all columns.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValidationError: If column types don't match schema
        """
        errors = []
        
        for feature_name in FEATURE_NAMES:
            if feature_name not in df.columns:
                continue  # Already checked in required columns
            
            feature = self.schema.get_feature_by_name(feature_name)
            col_data = df[feature_name]
            
            # Skip null values for type checking (handled separately)
            non_null_data = col_data.dropna()
            if len(non_null_data) == 0:
                continue
            
            # Check numeric features
            if feature.feature_type == FeatureType.NUMERIC:
                if not pd.api.types.is_numeric_dtype(col_data):
                    errors.append(
                        f"Column '{feature_name}' must be numeric, "
                        f"got dtype: {col_data.dtype}"
                    )
            
            # Check categorical features
            elif feature.feature_type == FeatureType.CATEGORICAL:
                if not (pd.api.types.is_string_dtype(col_data) or 
                        pd.api.types.is_object_dtype(col_data)):
                    errors.append(
                        f"Column '{feature_name}' must be string/object, "
                        f"got dtype: {col_data.dtype}"
                    )
        
        if errors:
            raise ValidationError(
                "Data type validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )
    
    def _validate_value_constraints(self, df: pd.DataFrame) -> None:
        """Validate value ranges and categorical constraints.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValidationError: If values violate constraints
        """
        errors = []
        
        for feature_name in FEATURE_NAMES:
            if feature_name not in df.columns:
                continue
            
            feature = self.schema.get_feature_by_name(feature_name)
            col_data = df[feature_name].dropna()
            
            if len(col_data) == 0:
                continue
            
            # Validate numeric constraints
            if feature.feature_type == FeatureType.NUMERIC:
                if feature.min_value is not None:
                    invalid_count = (col_data < feature.min_value).sum()
                    if invalid_count > 0:
                        min_val = col_data.min()
                        errors.append(
                            f"Column '{feature_name}': {invalid_count} values below "
                            f"minimum {feature.min_value} (min found: {min_val})"
                        )
                
                if feature.max_value is not None:
                    invalid_count = (col_data > feature.max_value).sum()
                    if invalid_count > 0:
                        max_val = col_data.max()
                        errors.append(
                            f"Column '{feature_name}': {invalid_count} values above "
                            f"maximum {feature.max_value} (max found: {max_val})"
                        )
            
            # Validate categorical constraints
            elif feature.feature_type == FeatureType.CATEGORICAL:
                if feature.valid_values:
                    invalid_values = set(col_data) - set(feature.valid_values)
                    if invalid_values:
                        errors.append(
                            f"Column '{feature_name}': Invalid values found: "
                            f"{', '.join(map(str, invalid_values))}. "
                            f"Valid values: {', '.join(feature.valid_values)}"
                        )
        
        if errors:
            raise ValidationError(
                "Value constraint validation failed:\n" + 
                "\n".join(f"  - {e}" for e in errors)
            )
    
    def _check_missing_values(self, df: pd.DataFrame) -> None:
        """Check for excessive missing values.
        
        Args:
            df: DataFrame to check
            
        Raises:
            ValidationError: If required features have missing values
        """
        errors = []
        
        for feature_name in REQUIRED_FEATURES:
            if feature_name not in df.columns:
                continue
            
            missing_count = df[feature_name].isna().sum()
            if missing_count > 0:
                missing_pct = (missing_count / len(df)) * 100
                errors.append(
                    f"Required feature '{feature_name}' has {missing_count} "
                    f"missing values ({missing_pct:.1f}%)"
                )
        
        if errors:
            raise ValidationError(
                "Missing value validation failed:\n" + 
                "\n".join(f"  - {e}" for e in errors)
            )
    
    def _validate_single_value(
        self, feature_name: str, value: Any, feature
    ) -> None:
        """Validate a single feature value.
        
        Args:
            feature_name: Name of the feature
            value: Value to validate
            feature: FeatureDefinition object
            
        Raises:
            ValidationError: If value is invalid
        """
        # Check for None/null
        if value is None or (isinstance(value, float) and np.isnan(value)):
            if feature.required:
                raise ValidationError(
                    f"Required feature '{feature_name}' has null/missing value"
                )
            return
        
        # Validate numeric constraints
        if feature.feature_type == FeatureType.NUMERIC:
            try:
                numeric_value = float(value)
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Feature '{feature_name}' must be numeric, got: {type(value).__name__}"
                )
            
            if feature.min_value is not None and numeric_value < feature.min_value:
                raise ValidationError(
                    f"Feature '{feature_name}' value {numeric_value} is below "
                    f"minimum {feature.min_value}"
                )
            
            if feature.max_value is not None and numeric_value > feature.max_value:
                raise ValidationError(
                    f"Feature '{feature_name}' value {numeric_value} exceeds "
                    f"maximum {feature.max_value}"
                )
        
        # Validate categorical constraints
        elif feature.feature_type == FeatureType.CATEGORICAL:
            if feature.valid_values and value not in feature.valid_values:
                raise ValidationError(
                    f"Feature '{feature_name}' has invalid value '{value}'. "
                    f"Valid values: {', '.join(feature.valid_values)}"
                )


def validate_training_data(df: pd.DataFrame) -> None:
    """Validate training data (requires target column).
    
    Args:
        df: Training DataFrame
        
    Raises:
        ValidationError: If validation fails
    """
    validator = DataValidator()
    validator.validate_dataframe(df, require_target=True, allow_extra_columns=False)


def validate_inference_data(df: pd.DataFrame) -> None:
    """Validate inference data (no target column required).
    
    Args:
        df: Inference DataFrame
        
    Raises:
        ValidationError: If validation fails
    """
    validator = DataValidator()
    validator.validate_dataframe(df, require_target=False, allow_extra_columns=True)


def validate_inference_dict(data: Dict[str, Any]) -> None:
    """Validate single inference record (dictionary).
    
    Args:
        data: Feature dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    validator = DataValidator()
    validator.validate_dict(data, require_target=False)


# Singleton validator instance for reuse
_validator_instance = None


def get_validator() -> DataValidator:
    """Get or create singleton validator instance.
    
    Returns:
        DataValidator instance
    """
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = DataValidator()
    return _validator_instance
