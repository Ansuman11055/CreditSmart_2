"""Feature schema definition for credit risk prediction model.

This module defines the single source of truth for all input features
used in the ML pipeline. It ensures consistency across preprocessing,
training, and inference.

Version: 1.0.0
"""

from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass


class FeatureType(str, Enum):
    """Feature type classification."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    BINARY = "binary"


class DataType(str, Enum):
    """Data type specification."""
    INTEGER = "int"
    FLOAT = "float"
    STRING = "str"
    BOOLEAN = "bool"


@dataclass
class FeatureDefinition:
    """Definition of a single feature.
    
    Attributes:
        name: Feature name (must match column name in raw data)
        feature_type: Type of feature (numeric, categorical, binary)
        data_type: Python data type
        required: Whether feature is required (missing values not allowed)
        description: Human-readable description
        valid_values: For categorical features, list of allowed values
        min_value: For numeric features, minimum allowed value
        max_value: For numeric features, maximum allowed value
    """
    name: str
    feature_type: FeatureType
    data_type: DataType
    required: bool = True
    description: str = ""
    valid_values: List[Any] = None
    min_value: float = None
    max_value: float = None
    
    def __post_init__(self):
        """Validate feature definition."""
        if self.feature_type == FeatureType.CATEGORICAL and not self.valid_values:
            raise ValueError(f"Categorical feature '{self.name}' must specify valid_values")


class FeatureSchema:
    """Complete feature schema for credit risk prediction.
    
    This class defines all features used in the model, serving as the
    single source of truth for feature names, types, and constraints.
    """
    
    # Schema version for tracking changes
    VERSION = "1.0.0"
    
    # Target variable
    TARGET = "default"
    
    # Feature definitions
    FEATURES = [
        # Income and debt features
        FeatureDefinition(
            name="annual_income",
            feature_type=FeatureType.NUMERIC,
            data_type=DataType.FLOAT,
            required=True,
            description="Annual income in USD",
            min_value=0,
            max_value=10_000_000
        ),
        FeatureDefinition(
            name="monthly_debt",
            feature_type=FeatureType.NUMERIC,
            data_type=DataType.FLOAT,
            required=True,
            description="Total monthly debt payments in USD",
            min_value=0,
            max_value=100_000
        ),
        
        # Credit score features
        FeatureDefinition(
            name="credit_score",
            feature_type=FeatureType.NUMERIC,
            data_type=DataType.INTEGER,
            required=True,
            description="FICO credit score (300-850)",
            min_value=300,
            max_value=850
        ),
        
        # Loan features
        FeatureDefinition(
            name="loan_amount",
            feature_type=FeatureType.NUMERIC,
            data_type=DataType.FLOAT,
            required=True,
            description="Requested loan amount in USD",
            min_value=0,
            max_value=1_000_000
        ),
        FeatureDefinition(
            name="loan_term_months",
            feature_type=FeatureType.NUMERIC,
            data_type=DataType.INTEGER,
            required=True,
            description="Loan term in months",
            min_value=6,
            max_value=360
        ),
        
        # Employment features
        FeatureDefinition(
            name="employment_length_years",
            feature_type=FeatureType.NUMERIC,
            data_type=DataType.FLOAT,
            required=True,
            description="Years of employment at current job",
            min_value=0,
            max_value=50
        ),
        
        # Categorical features
        FeatureDefinition(
            name="home_ownership",
            feature_type=FeatureType.CATEGORICAL,
            data_type=DataType.STRING,
            required=True,
            description="Home ownership status",
            valid_values=["RENT", "OWN", "MORTGAGE", "OTHER"]
        ),
        FeatureDefinition(
            name="purpose",
            feature_type=FeatureType.CATEGORICAL,
            data_type=DataType.STRING,
            required=True,
            description="Loan purpose category",
            valid_values=[
                "debt_consolidation",
                "home_improvement",
                "major_purchase",
                "medical",
                "business",
                "car",
                "vacation",
                "wedding",
                "moving",
                "other"
            ]
        ),
        
        # Credit history features
        FeatureDefinition(
            name="number_of_open_accounts",
            feature_type=FeatureType.NUMERIC,
            data_type=DataType.INTEGER,
            required=False,
            description="Number of open credit accounts",
            min_value=0,
            max_value=100
        ),
        FeatureDefinition(
            name="delinquencies_2y",
            feature_type=FeatureType.NUMERIC,
            data_type=DataType.INTEGER,
            required=False,
            description="Number of 30+ day delinquencies in past 2 years",
            min_value=0,
            max_value=50
        ),
        FeatureDefinition(
            name="inquiries_6m",
            feature_type=FeatureType.NUMERIC,
            data_type=DataType.INTEGER,
            required=False,
            description="Number of credit inquiries in last 6 months",
            min_value=0,
            max_value=20
        ),
    ]
    
    @classmethod
    def get_feature_names(cls) -> List[str]:
        """Get list of all feature names.
        
        Returns:
            List of feature names in order
        """
        return [f.name for f in cls.FEATURES]
    
    @classmethod
    def get_numeric_features(cls) -> List[str]:
        """Get list of numeric feature names.
        
        Returns:
            List of numeric feature names
        """
        return [f.name for f in cls.FEATURES if f.feature_type == FeatureType.NUMERIC]
    
    @classmethod
    def get_categorical_features(cls) -> List[str]:
        """Get list of categorical feature names.
        
        Returns:
            List of categorical feature names
        """
        return [f.name for f in cls.FEATURES if f.feature_type == FeatureType.CATEGORICAL]
    
    @classmethod
    def get_binary_features(cls) -> List[str]:
        """Get list of binary feature names.
        
        Returns:
            List of binary feature names
        """
        return [f.name for f in cls.FEATURES if f.feature_type == FeatureType.BINARY]
    
    @classmethod
    def get_required_features(cls) -> List[str]:
        """Get list of required feature names.
        
        Returns:
            List of required feature names
        """
        return [f.name for f in cls.FEATURES if f.required]
    
    @classmethod
    def get_optional_features(cls) -> List[str]:
        """Get list of optional feature names.
        
        Returns:
            List of optional feature names
        """
        return [f.name for f in cls.FEATURES if not f.required]
    
    @classmethod
    def get_feature_by_name(cls, name: str) -> FeatureDefinition:
        """Get feature definition by name.
        
        Args:
            name: Feature name
            
        Returns:
            FeatureDefinition object
            
        Raises:
            ValueError: If feature not found
        """
        for feature in cls.FEATURES:
            if feature.name == name:
                return feature
        raise ValueError(f"Feature '{name}' not found in schema")
    
    @classmethod
    def validate_feature_value(cls, name: str, value: Any) -> bool:
        """Validate a feature value against schema constraints.
        
        Args:
            name: Feature name
            value: Feature value to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            feature = cls.get_feature_by_name(name)
            
            # Check for None/missing values
            if value is None or (isinstance(value, float) and value != value):  # NaN check
                return not feature.required
            
            # Validate numeric constraints
            if feature.feature_type == FeatureType.NUMERIC:
                if feature.min_value is not None and value < feature.min_value:
                    return False
                if feature.max_value is not None and value > feature.max_value:
                    return False
            
            # Validate categorical constraints
            if feature.feature_type == FeatureType.CATEGORICAL:
                if feature.valid_values and value not in feature.valid_values:
                    return False
            
            return True
            
        except ValueError:
            return False
    
    @classmethod
    def get_schema_info(cls) -> Dict[str, Any]:
        """Get comprehensive schema information.
        
        Returns:
            Dictionary with schema metadata
        """
        return {
            "version": cls.VERSION,
            "target": cls.TARGET,
            "total_features": len(cls.FEATURES),
            "numeric_features": len(cls.get_numeric_features()),
            "categorical_features": len(cls.get_categorical_features()),
            "binary_features": len(cls.get_binary_features()),
            "required_features": len(cls.get_required_features()),
            "optional_features": len(cls.get_optional_features()),
            "feature_names": cls.get_feature_names(),
        }


# Convenience exports for easy importing
FEATURE_NAMES = FeatureSchema.get_feature_names()
NUMERIC_FEATURES = FeatureSchema.get_numeric_features()
CATEGORICAL_FEATURES = FeatureSchema.get_categorical_features()
BINARY_FEATURES = FeatureSchema.get_binary_features()
REQUIRED_FEATURES = FeatureSchema.get_required_features()
OPTIONAL_FEATURES = FeatureSchema.get_optional_features()
TARGET = FeatureSchema.TARGET
SCHEMA_VERSION = FeatureSchema.VERSION
