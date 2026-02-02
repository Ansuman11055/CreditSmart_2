"""
Model Registry for CreditSmart ML System
========================================

Provides a centralized registry for managing multiple ML models with their
configurations, hyperparameters, and metadata.

This abstraction layer allows easy switching between different model types
and supports model comparison experiments.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Type, Optional
import logging

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a single ML model.
    
    Attributes:
        name: Human-readable model name
        model_class: sklearn-compatible model class
        default_params: Default hyperparameters for the model
        supports_probability: Whether model supports probability predictions
        description: Brief description of the model
        use_cases: Recommended use cases for this model
    """
    name: str
    model_class: Type
    default_params: Dict[str, Any]
    supports_probability: bool = True
    description: str = ""
    use_cases: str = ""
    
    def create_model(self, custom_params: Optional[Dict[str, Any]] = None) -> Any:
        """Create a model instance with specified parameters.
        
        Args:
            custom_params: Optional custom parameters to override defaults
            
        Returns:
            Instantiated model object
        """
        params = self.default_params.copy()
        if custom_params:
            params.update(custom_params)
        
        logger.info(f"Creating {self.name} with parameters: {params}")
        return self.model_class(**params)
    
    def get_info(self) -> Dict[str, Any]:
        """Get model configuration information.
        
        Returns:
            Dictionary with model metadata
        """
        return {
            "name": self.name,
            "model_class": self.model_class.__name__,
            "supports_probability": self.supports_probability,
            "default_params": self.default_params,
            "description": self.description,
            "use_cases": self.use_cases,
        }


class ModelRegistry:
    """Registry for managing multiple ML models.
    
    Provides centralized access to model configurations and supports
    easy model selection for training and comparison experiments.
    """
    
    def __init__(self):
        """Initialize model registry with available models."""
        self._models: Dict[str, ModelConfig] = {}
        self._register_default_models()
    
    def _register_default_models(self) -> None:
        """Register default models with their configurations."""
        
        # Logistic Regression - Fast baseline
        self.register_model(ModelConfig(
            name="logistic_regression",
            model_class=LogisticRegression,
            default_params={
                "max_iter": 1000,
                "random_state": 42,
                "solver": "lbfgs",
                "class_weight": "balanced",
                "n_jobs": -1,
            },
            supports_probability=True,
            description="Linear model for binary classification with L2 regularization",
            use_cases="Fast baseline, interpretable coefficients, works well with scaled features"
        ))
        
        # Random Forest - Production-grade configuration for credit risk
        # 
        # DESIGN RATIONALE FOR FINANCIAL RISK MODELS:
        # ============================================
        # 1. Shallow Trees (max_depth: 8-12)
        #    - Prevents overfitting on noisy financial data
        #    - Reduces model complexity for regulatory compliance
        #    - Improves interpretability for risk committees
        #    - Captures main patterns without memorizing outliers
        #
        # 2. Large Leaf Sizes (min_samples_leaf: 200-500)
        #    - Ensures statistical significance in leaf predictions
        #    - Reduces variance in probability estimates
        #    - Prevents decisions based on small sample sizes
        #    - Critical for reliable risk assessment at scale
        #
        # 3. More Estimators (n_estimators: 300-600)
        #    - Compensates for shallow trees with more diversity
        #    - Improves stability of probability estimates
        #    - Reduces prediction variance through averaging
        #    - Better calibration for risk scoring
        #
        # 4. sqrt Feature Sampling (max_features: "sqrt")
        #    - Decorrelates trees for better ensemble diversity
        #    - Standard practice for classification tasks
        #    - Prevents feature dominance in splits
        #
        # 5. Balanced Class Weights
        #    - Handles ~7:1 imbalance in default rates
        #    - Ensures minority class (defaults) is not ignored
        #    - Adjusts loss function to penalize FN errors more
        #
        self.register_model(ModelConfig(
            name="random_forest",
            model_class=RandomForestClassifier,
            default_params={
                "n_estimators": 400,        # Production: 300-600 range, 400 for speed/performance balance
                "max_depth": 10,            # Shallow trees: 8-12 range prevents overfitting
                "min_samples_split": 500,   # Require 500 samples before splitting (2*min_samples_leaf)
                "min_samples_leaf": 250,    # Large leaves: 200-500 range for statistical significance
                "max_features": "sqrt",     # Standard for classification: decorrelates trees
                "random_state": 42,         # Reproducibility for auditing and validation
                "n_jobs": -1,               # Parallel processing: use all CPU cores
                "class_weight": "balanced", # Handle 6.81:1 imbalance in default rates
                "bootstrap": True,          # Enable bagging for variance reduction
                "oob_score": False,         # Disable OOB to save computation (using separate validation set)
                "warm_start": False,        # Fresh training each time for reproducibility
                "verbose": 0,               # Clean logs (set to 1-3 for debugging)
            },
            supports_probability=True,
            description="Production-grade ensemble optimized for credit risk modeling with shallow trees and large leaves",
            use_cases="Credit risk scoring, default prediction, regulatory-compliant models, interpretable ensemble"
        ))
        
        # XGBoost - High performance gradient boosting
        # Only register if xgboost is available
        try:
            import xgboost as xgb
            
            # =====================================================================
            # XGBoost Configuration for Structured Financial Data (Credit Risk)
            # =====================================================================
            #
            # WHY BOOSTING OUTPERFORMS BAGGING FOR CREDIT RISK:
            # -------------------------------------------------
            # 1. SEQUENTIAL ERROR CORRECTION (Boosting's Key Advantage):
            #    - Each tree learns from mistakes of previous trees
            #    - Focuses on hard-to-classify cases (borderline defaults)
            #    - RandomForest treats all samples equally (parallel, independent trees)
            #    - Credit risk has subtle patterns → boosting captures these iteratively
            #
            # 2. BIAS-VARIANCE TRADE-OFF:
            #    - Boosting reduces BIAS (underfitting) through sequential learning
            #    - Bagging reduces VARIANCE (overfitting) through averaging
            #    - Financial data has high signal-to-noise → reducing bias is critical
            #    - Structured tabular features → boosting exploits feature interactions better
            #
            # 3. FEATURE IMPORTANCE & INTERACTIONS:
            #    - Boosting naturally handles complex feature interactions
            #    - Each tree splits on features that improve previous predictions
            #    - Credit risk = non-linear combinations (income × debt, score × history)
            #    - RandomForest averages independent trees → misses sequential patterns
            #
            # 4. EFFICIENCY FOR STRUCTURED DATA:
            #    - Boosting achieves higher accuracy with fewer, shallower trees
            #    - Financial data = low-dimensional, structured → perfect for boosting
            #    - Regulatory preference: shallow trees = interpretable decision rules
            #
            # 5. RARE EVENT DETECTION (Defaults = 12.81%):
            #    - Boosting up-weights misclassified defaults in each round
            #    - Progressively focuses on minority class (adaptive weighting)
            #    - Better recall for rare events than bagging's uniform sampling
            #
            # OPTIMAL HYPERPARAMETERS FOR FINANCIAL DATA:
            # -------------------------------------------
            
            self.register_model(ModelConfig(
                name="xgboost",
                model_class=xgb.XGBClassifier,
                default_params={
                    # n_estimators: 300-500 range optimal for structured financial data
                    # - 300 trees balance accuracy vs training time
                    # - Each tree corrects errors from previous 299 trees (sequential learning)
                    # - More trees than this risks overfitting on credit data
                    "n_estimators": 300,
                    
                    # max_depth: 4-6 range prevents overfitting on tabular data
                    # - Shallow trees = interpretable rules (regulatory compliance)
                    # - Depth 6 = 2^6 = 64 leaf nodes maximum per tree
                    # - Financial data has strong main effects → shallow splits sufficient
                    # - Deep trees memorize noise in credit history (bad generalization)
                    "max_depth": 6,
                    
                    # learning_rate: 0.05-0.1 range (shrinkage parameter)
                    # - 0.05 = conservative learning (each tree contributes 5% to final prediction)
                    # - Lower rate = more trees needed but better generalization
                    # - Prevents any single tree from dominating (ensemble robustness)
                    # - Credit risk = noisy labels → slower learning reduces overfitting
                    "learning_rate": 0.05,
                    
                    # subsample: 0.8 = stochastic gradient boosting
                    # - Each tree trained on 80% random sample (prevents overfitting)
                    # - Introduces randomness similar to RandomForest but with boosting benefits
                    # - 80% sufficient for 30K training samples (24K per tree)
                    # - Improves generalization on unseen credit profiles
                    "subsample": 0.8,
                    
                    # colsample_bytree: 0.8 = feature sampling per tree
                    # - Each tree uses 80% of features (22 features → ~18 per tree)
                    # - Reduces feature correlation across trees (better ensemble diversity)
                    # - Prevents overreliance on dominant features (e.g., credit score)
                    # - Forces model to learn alternative credit risk signals
                    "colsample_bytree": 0.8,
                    
                    # eval_metric: "auc" = ROC-AUC (industry standard for credit risk)
                    # - Measures discrimination across ALL thresholds (not just 0.5)
                    # - Robust to class imbalance (unlike accuracy or logloss)
                    # - Regulatory requirement (Basel III, IFRS 9) for model validation
                    # - Directly optimizes ranking quality (who defaults vs who doesn't)
                    "eval_metric": "auc",
                    
                    # random_state: 42 = reproducibility (critical for financial models)
                    # - Deterministic results for model validation and auditing
                    # - Required for regulatory approval (SR 11-7 model risk management)
                    # - Enables A/B testing with consistent baseline
                    "random_state": 42,
                    
                    # Additional parameters for credit risk optimization
                    "min_child_weight": 50,  # Minimum samples per leaf (statistical significance)
                    "scale_pos_weight": 6.81,  # Class imbalance: 43596 negatives / 6404 positives
                    "objective": "binary:logistic",  # Binary classification with probabilities
                    "gamma": 0.1,  # Minimum loss reduction for split (regularization)
                    "reg_alpha": 0.1,  # L1 regularization (LASSO) for feature selection
                    "reg_lambda": 1.0,  # L2 regularization (Ridge) for coefficient shrinkage
                    "n_jobs": -1,  # Parallel processing (all CPU cores)
                    "use_label_encoder": False,  # Disable deprecated sklearn label encoder
                    "tree_method": "hist",  # Fast histogram-based algorithm
                    "verbosity": 0,  # Suppress training warnings
                },
                supports_probability=True,
                description="Gradient boosting optimized for structured financial data with sequential error correction",
                use_cases="Credit risk modeling: boosting outperforms bagging through iterative refinement of hard-to-classify defaults"
            ))
            logger.info("XGBoost registered successfully")
        except ImportError:
            logger.warning(
                "XGBoost not available. Install with: pip install xgboost\n"
                "Only Logistic Regression and Random Forest will be available."
            )
    
    def register_model(self, config: ModelConfig) -> None:
        """Register a new model configuration.
        
        Args:
            config: ModelConfig instance with model details
        """
        if config.name in self._models:
            logger.warning(f"Model '{config.name}' already registered. Overwriting.")
        
        self._models[config.name] = config
        logger.info(f"Registered model: {config.name}")
    
    def get_model(self, name: str, custom_params: Optional[Dict[str, Any]] = None) -> Any:
        """Get a model instance by name.
        
        Args:
            name: Model name (e.g., 'random_forest', 'logistic_regression')
            custom_params: Optional custom parameters to override defaults
            
        Returns:
            Instantiated model object
            
        Raises:
            ValueError: If model name not found in registry
        """
        if name not in self._models:
            available = ", ".join(self.list_models())
            raise ValueError(
                f"Model '{name}' not found in registry. "
                f"Available models: {available}"
            )
        
        config = self._models[name]
        return config.create_model(custom_params)
    
    def get_config(self, name: str) -> ModelConfig:
        """Get model configuration by name.
        
        Args:
            name: Model name
            
        Returns:
            ModelConfig instance
            
        Raises:
            ValueError: If model name not found
        """
        if name not in self._models:
            available = ", ".join(self.list_models())
            raise ValueError(
                f"Model '{name}' not found in registry. "
                f"Available models: {available}"
            )
        
        return self._models[name]
    
    def list_models(self) -> list:
        """Get list of registered model names.
        
        Returns:
            List of model names
        """
        return list(self._models.keys())
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration info for all registered models.
        
        Returns:
            Dictionary mapping model names to their info
        """
        return {
            name: config.get_info()
            for name, config in self._models.items()
        }
    
    def supports_probability(self, name: str) -> bool:
        """Check if a model supports probability predictions.
        
        Args:
            name: Model name
            
        Returns:
            True if model supports predict_proba, False otherwise
            
        Raises:
            ValueError: If model name not found
        """
        config = self.get_config(name)
        return config.supports_probability


# Global registry instance
_registry = None


def get_registry() -> ModelRegistry:
    """Get the global model registry instance.
    
    Returns:
        ModelRegistry singleton instance
    """
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def list_available_models() -> list:
    """Get list of available model names.
    
    Convenience function for quick access.
    
    Returns:
        List of registered model names
    """
    return get_registry().list_models()


def get_model(name: str, custom_params: Optional[Dict[str, Any]] = None) -> Any:
    """Get a model instance from the registry.
    
    Convenience function for quick access.
    
    Args:
        name: Model name
        custom_params: Optional custom parameters
        
    Returns:
        Instantiated model object
    """
    return get_registry().get_model(name, custom_params)


def print_model_info() -> None:
    """Print information about all registered models."""
    registry = get_registry()
    configs = registry.get_all_configs()
    
    print("\n" + "="*70)
    print("REGISTERED MODELS")
    print("="*70)
    
    for name, info in configs.items():
        print(f"\n{name.upper()}")
        print("-" * 70)
        print(f"  Class: {info['model_class']}")
        print(f"  Probability Support: {info['supports_probability']}")
        print(f"  Description: {info['description']}")
        print(f"  Use Cases: {info['use_cases']}")
        print(f"  Default Parameters:")
        for param, value in info['default_params'].items():
            print(f"    - {param}: {value}")
    
    print("\n" + "="*70)
    print(f"Total Models: {len(configs)}")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Example usage
    print_model_info()
    
    # Test model creation
    print("\nTesting model creation:")
    print("-" * 70)
    
    for model_name in list_available_models():
        try:
            model = get_model(model_name)
            print(f"✓ Created {model_name}: {type(model).__name__}")
        except Exception as e:
            print(f"✗ Failed to create {model_name}: {e}")
    
    print("-" * 70 + "\n")
