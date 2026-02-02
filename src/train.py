"""Model training pipeline for credit risk prediction.

This module handles:
- Loading and preprocessing training data
- Training the credit risk model
- Saving model and preprocessing artifacts separately
- Evaluation and metrics
- Model metadata tracking
"""

import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from datetime import datetime
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    classification_report,
)

from src.preprocess import DataPreprocessor
from src.core.feature_schema import SCHEMA_VERSION
from src.models.model_registry import get_registry, list_available_models

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def set_random_seeds(seed: int = 42) -> None:
    """Set random seeds for reproducibility.
    
    Args:
        seed: Random seed value
    """
    np.random.seed(seed)
    # Set Python's random seed
    import random
    random.seed(seed)
    # Set environment variable for hash seed
    import os
    os.environ['PYTHONHASHSEED'] = str(seed)


class CreditRiskTrainer:
    """Trainer for credit risk prediction model."""
    
    def __init__(
        self,
        data_dir: str = "data",
        models_dir: str = "models",
        random_state: int = 42,
        model_name: str = "random_forest",
    ):
        """Initialize trainer.
        
        Args:
            data_dir: Directory containing training data
            models_dir: Directory to save models and artifacts
            random_state: Random seed for reproducibility
            model_name: Name of model from registry (default: 'random_forest')
        """
        self.data_dir = Path(data_dir)
        self.models_dir = Path(models_dir)
        self.random_state = random_state
        self.model_name = model_name
        
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Get model registry
        self.registry = get_registry()
        
        # Validate model name
        if model_name not in self.registry.list_models():
            available = ", ".join(self.registry.list_models())
            raise ValueError(
                f"Model '{model_name}' not found. Available: {available}"
            )
        
        self.preprocessor = None
        self.model = None
        self.model_config = None
        self.feature_names = None
        
        logger.info(f"CreditRiskTrainer initialized")
        logger.info(f"  Data directory: {self.data_dir}")
        logger.info(f"  Models directory: {self.models_dir}")
        logger.info(f"  Random state: {self.random_state}")
        logger.info(f"  Model: {self.model_name}")
    
    def load_and_preprocess_data(
        self, filename: str = "raw.csv", validation_split: float = 0.2
    ) -> Tuple[pd.DataFrame, np.ndarray, pd.DataFrame, np.ndarray, pd.DataFrame, np.ndarray]:
        """Load raw data and preprocess with train/validation/test split.
        
        Args:
            filename: Name of CSV file in data/raw directory
            validation_split: Fraction of training data to use for validation
            
        Returns:
            Tuple of (X_train, y_train, X_val, y_val, X_test, y_test)
        """
        # Set random seeds for deterministic behavior
        set_random_seeds(self.random_state)
        logger.info("="*70)
        logger.info("STEP 1: Loading and Preprocessing Data")
        logger.info("="*70)
        
        # Initialize preprocessor
        self.preprocessor = DataPreprocessor(data_dir=str(self.data_dir))
        
        # Load and validate raw data
        df = self.preprocessor.load_and_validate(filename)
        logger.info(f"✓ Loaded {len(df)} records from {filename}")
        
        # Log class distribution before preprocessing
        target_col = 'default'
        if target_col in df.columns:
            n_positive = df[target_col].sum()
            n_negative = len(df) - n_positive
            imbalance_ratio = n_negative / n_positive if n_positive > 0 else float('inf')
            logger.info(f"\nClass Distribution (before split):")
            logger.info(f"  Negative class (no default): {n_negative:,} ({n_negative/len(df)*100:.2f}%)")
            logger.info(f"  Positive class (default):    {n_positive:,} ({n_positive/len(df)*100:.2f}%)")
            logger.info(f"  Imbalance ratio: {imbalance_ratio:.2f}:1")
            if imbalance_ratio > 10:
                logger.warning(f"⚠ High class imbalance detected (ratio {imbalance_ratio:.1f}:1)")
                logger.warning(f"  Using class_weight='balanced' to handle imbalance")
        
        # Preprocess data (fit pipeline on training data)
        logger.info("Fitting preprocessing pipeline on training data...")
        X, y, metadata = self.preprocessor.preprocess(
            df, fit=True, save_output=True
        )
        
        logger.info(f"✓ Preprocessing complete")
        logger.info(f"  Input features: {metadata['n_input_features']}")
        logger.info(f"  Output features: {metadata['n_output_features']}")
        logger.info(f"  Schema version: {metadata['schema_version']}")
        
        # First split: train+val / test (80/20)
        logger.info(f"\nSplitting data (deterministic with random_state={self.random_state})...")
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state, stratify=y
        )
        
        # Second split: train / val from temp set
        val_size = validation_split / (1 - 0.2)  # Adjust validation size relative to temp set
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_size, random_state=self.random_state, stratify=y_temp
        )
        
        logger.info(f"✓ Split complete (train/val/test) - Stratified by target")
        logger.info(f"\nSplit Sizes:")
        logger.info(f"  Training set:   {len(X_train):,} samples ({len(X_train)/len(X)*100:.1f}%)")
        logger.info(f"  Validation set: {len(X_val):,} samples ({len(X_val)/len(X)*100:.1f}%)")
        logger.info(f"  Test set:       {len(X_test):,} samples ({len(X_test)/len(X)*100:.1f}%)")
        logger.info(f"\nClass Distribution After Split:")
        logger.info(f"  Training:   {y_train.sum():,} defaults ({y_train.sum()/len(y_train)*100:.2f}%), {len(y_train)-y_train.sum():,} no-default ({(1-y_train.sum()/len(y_train))*100:.2f}%)")
        logger.info(f"  Validation: {y_val.sum():,} defaults ({y_val.sum()/len(y_val)*100:.2f}%), {len(y_val)-y_val.sum():,} no-default ({(1-y_val.sum()/len(y_val))*100:.2f}%)")
        logger.info(f"  Test:       {y_test.sum():,} defaults ({y_test.sum()/len(y_test)*100:.2f}%), {len(y_test)-y_test.sum():,} no-default ({(1-y_test.sum()/len(y_test))*100:.2f}%)")
        
        return X_train, y_train, X_val, y_val, X_test, y_test
    
    def train_model(
        self,
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        model_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Train credit risk model.
        
        Args:
            X_train: Training features
            y_train: Training labels
            model_params: Model hyperparameters (uses registry defaults if None)
        """
        logger.info("\\n" + "="*70)
        logger.info("STEP 2: Training Model")
        logger.info("="*70)
        
        # Get model configuration from registry
        self.model_config = self.registry.get_config(self.model_name)
        
        # Merge custom params with defaults
        params = self.model_config.default_params.copy()
        if model_params:
            params.update(model_params)
        
        # Ensure random_state is set
        if "random_state" in params:
            params["random_state"] = self.random_state
        
        logger.info(f"Model: {self.model_config.name} ({self.model_config.model_class.__name__})")
        logger.info(f"Description: {self.model_config.description}")
        logger.info(f"Parameters: {params}")
        
        # Create and train model from registry
        self.model = self.registry.get_model(self.model_name, params)
        logger.info("\\nTraining model...")
        self.model.fit(X_train, y_train)
        
        logger.info(f"✓ Training complete")
        if hasattr(self.model, "n_estimators"):
            logger.info(f"  Trees/Estimators: {self.model.n_estimators}")
        if hasattr(self.model, "n_features_in_"):
            logger.info(f"  Features used: {self.model.n_features_in_}")
        
        # Analyze feature importance
        self.analyze_feature_importance(X_train)
    
    def analyze_feature_importance(
        self,
        X_train: pd.DataFrame,
        top_n: int = 15,
        dominance_threshold: float = 0.40,
    ) -> None:
        """Analyze and log feature importance from trained model.
        
        Args:
            X_train: Training features (used to get feature names)
            top_n: Number of top features to display
            dominance_threshold: Threshold for feature dominance warning
        """
        if self.model is None:
            logger.warning("No model trained yet. Skipping feature importance analysis.")
            return
        
        # Extract feature importance based on model type
        feature_importance = None
        
        if hasattr(self.model, "feature_importances_"):
            # RandomForest, XGBoost, and other tree-based models
            feature_importance = self.model.feature_importances_
        elif hasattr(self.model, "coef_"):
            # Logistic Regression (use absolute values)
            feature_importance = np.abs(self.model.coef_[0])
        else:
            logger.warning(
                f"Model type '{type(self.model).__name__}' does not support feature importance extraction. "
                f"Skipping analysis."
            )
            return
        
        # Get feature names
        if isinstance(X_train, pd.DataFrame):
            feature_names = X_train.columns.tolist()
        else:
            feature_names = [f"feature_{i}" for i in range(len(feature_importance))]
        
        # Verify feature count matches
        if len(feature_names) != len(feature_importance):
            logger.warning(
                f"Feature count mismatch: {len(feature_names)} names vs {len(feature_importance)} importance values. "
                f"This may indicate dropped or missing features."
            )
            # Truncate or pad to match
            if len(feature_names) > len(feature_importance):
                dropped_features = feature_names[len(feature_importance):]
                logger.warning(f"Dropped features: {', '.join(dropped_features)}")
                feature_names = feature_names[:len(feature_importance)]
            else:
                # More importance values than names (shouldn't happen)
                feature_names.extend([f"unknown_{i}" for i in range(len(feature_importance) - len(feature_names))])
        
        # Create importance dataframe
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': feature_importance,
        }).sort_values('importance', ascending=False)
        
        # Normalize to percentages
        total_importance = importance_df['importance'].sum()
        if total_importance > 0:
            importance_df['importance_pct'] = (importance_df['importance'] / total_importance) * 100
        else:
            logger.warning("Total feature importance is zero. This is unusual.")
            importance_df['importance_pct'] = 0
        
        # Log feature importance
        logger.info("\n" + "="*70)
        logger.info("FEATURE IMPORTANCE DIAGNOSTICS")
        logger.info("="*70)
        logger.info(f"Model: {type(self.model).__name__}")
        logger.info(f"Total features: {len(feature_names)}")
        logger.info(f"Displaying top {min(top_n, len(importance_df))} features:\n")
        
        # Display top N features
        for idx, row in importance_df.head(top_n).iterrows():
            importance_val = row['importance']
            importance_pct = row['importance_pct']
            feature_name = row['feature']
            
            # Create visual bar
            bar_length = int(importance_pct / 2)  # Scale to ~50 chars max
            bar = "█" * bar_length
            
            logger.info(f"  {idx+1:2d}. {feature_name:30s} {importance_pct:6.2f}% {bar}")
        
        # Check for feature dominance
        max_importance = importance_df['importance_pct'].iloc[0]
        max_feature = importance_df['feature'].iloc[0]
        
        if max_importance > (dominance_threshold * 100):
            logger.warning("\n" + "!"*70)
            logger.warning(f"⚠️  FEATURE DOMINANCE DETECTED!")
            logger.warning(f"   Feature '{max_feature}' accounts for {max_importance:.1f}% of total importance")
            logger.warning(f"   Threshold: {dominance_threshold*100:.0f}%")
            logger.warning("   Risk: Model may be overly reliant on single feature")
            logger.warning("   Recommendation: Investigate feature engineering or collection process")
            logger.warning("!"*70 + "\n")
        else:
            logger.info(f"\n✓ Feature diversity: No single feature dominates (max: {max_importance:.1f}% < {dominance_threshold*100:.0f}%)")
        
        # Check for very low importance features
        low_importance = importance_df[importance_df['importance_pct'] < 0.1]
        if len(low_importance) > 0:
            logger.info(f"\nℹ️  Note: {len(low_importance)} features have <0.1% importance (may be candidates for removal)")
        
        # Log cumulative importance
        top_5_cumulative = importance_df.head(5)['importance_pct'].sum()
        top_10_cumulative = importance_df.head(10)['importance_pct'].sum()
        logger.info(f"\nCumulative importance:")
        logger.info(f"  Top 5 features:  {top_5_cumulative:.1f}%")
        logger.info(f"  Top 10 features: {top_10_cumulative:.1f}%")
        logger.info("="*70)
    
    def compute_and_save_shap(
        self,
        X_train: pd.DataFrame,
        X_sample: pd.DataFrame = None,
        background_size: int = 100,
    ) -> bool:
        """Compute and save SHAP explainer for model interpretability.
        
        Args:
            X_train: Training features (for background sample)
            X_sample: Sample data to validate SHAP values (if None, uses random sample from X_train)
            background_size: Number of samples for SHAP background
            
        Returns:
            True if SHAP saved successfully, False otherwise
        """
        logger.info("\n" + "="*70)
        logger.info("SHAP EXPLAINABILITY")
        logger.info("="*70)
        
        if self.model is None:
            logger.warning("⚠️  No model trained yet. Skipping SHAP computation.")
            return False
        
        # Check if SHAP is available
        try:
            import shap
            logger.info(f"Model: {type(self.model).__name__}")
        except ImportError:
            logger.warning("⚠️  SHAP not installed. Skipping explainability.")
            logger.info("   Install with: pip install shap")
            return False
        
        # Check model compatibility with TreeExplainer
        model_type = type(self.model).__name__
        compatible_models = ['RandomForestClassifier', 'XGBClassifier', 'GradientBoostingClassifier', 'ExtraTreesClassifier']
        
        if model_type not in compatible_models:
            logger.warning(
                f"⚠️  Model '{model_type}' may not be compatible with SHAP TreeExplainer. "
                f"Compatible models: {', '.join(compatible_models)}"
            )
            logger.info("   Attempting with TreeExplainer anyway...")
        
        try:
            # Create background sample safely
            if background_size > len(X_train):
                background_size = len(X_train)
                logger.warning(f"⚠️  Background size reduced to {background_size} (full training set size)")
            
            # Sample background data
            np.random.seed(self.random_state)
            background_indices = np.random.choice(len(X_train), size=background_size, replace=False)
            X_background = X_train.iloc[background_indices]
            
            logger.info(f"Background sample: {background_size} instances")
            logger.info(f"Background shape: {X_background.shape}")
            
            # Create TreeExplainer
            logger.info("\nCreating SHAP TreeExplainer...")
            explainer = shap.TreeExplainer(self.model, X_background)
            logger.info("✓ TreeExplainer created successfully")
            
            # Validate with sample data
            if X_sample is None:
                # Use a small random sample from training data
                sample_size = min(10, len(X_train))
                sample_indices = np.random.choice(len(X_train), size=sample_size, replace=False)
                X_sample = X_train.iloc[sample_indices]
            
            logger.info(f"\nValidating SHAP values with {len(X_sample)} samples...")
            shap_values = explainer.shap_values(X_sample)
            
            # Handle different SHAP output formats
            if isinstance(shap_values, list):
                # Binary classification with list output [neg_class, pos_class]
                shap_values_array = np.array(shap_values[1]) if len(shap_values) == 2 else np.array(shap_values[0])
                logger.info(f"SHAP output format: list with {len(shap_values)} classes")
            else:
                shap_values_array = np.array(shap_values)
                logger.info("SHAP output format: single array")
            
            # Handle 3D output (samples, features, classes) - extract positive class
            if len(shap_values_array.shape) == 3:
                logger.info(f"SHAP 3D output detected: {shap_values_array.shape}")
                # For binary classification, use positive class (index 1)
                shap_values_array = shap_values_array[:, :, 1]
                logger.info(f"Extracted positive class SHAP values: {shap_values_array.shape}")
            
            # Validate dimensions
            expected_shape = (len(X_sample), X_sample.shape[1])
            actual_shape = shap_values_array.shape
            
            if actual_shape == expected_shape:
                logger.info(f"✓ SHAP values validated: {actual_shape}")
                logger.info(f"  Samples: {actual_shape[0]}")
                logger.info(f"  Features: {actual_shape[1]}")
            else:
                logger.warning(
                    f"⚠️  SHAP dimension mismatch: expected {expected_shape}, got {actual_shape}"
                )
                # Continue anyway, might still be usable
            
            # Save SHAP artifacts
            shap_path = self.models_dir / "shap_explainer.joblib"
            if shap_path.exists():
                logger.warning(f"SHAP explainer already exists at {shap_path}")
                logger.warning("Saving to shap_explainer_new.joblib to avoid overwriting")
                shap_path = self.models_dir / "shap_explainer_new.joblib"
            
            shap_artifact = {
                "explainer": explainer,
                "background_data": X_background,
                "background_size": background_size,
                "model_type": model_type,
                "feature_names": list(X_train.columns),
                "n_features": X_train.shape[1],
                "schema_version": SCHEMA_VERSION,
                "shap_version": shap.__version__,
            }
            
            joblib.dump(shap_artifact, shap_path)
            logger.info(f"\n✓ SHAP artifacts saved to {shap_path}")
            logger.info(f"  Explainer: TreeExplainer")
            logger.info(f"  Background: {background_size} samples")
            logger.info(f"  Features: {X_train.shape[1]}")
            logger.info(f"  SHAP version: {shap.__version__}")
            logger.info("="*70)
            
            return True
            
        except Exception as e:
            logger.error(f"\n✗ SHAP computation failed: {str(e)}")
            logger.error(f"  Model type: {model_type}")
            logger.error(f"  Error type: {type(e).__name__}")
            logger.info("  Continuing without SHAP explainability...")
            logger.info("="*70)
            return False
    
    def generate_validation_summary(
        self,
        test_metrics: Dict[str, float],
        y_train: np.ndarray,
    ) -> None:
        """Generate consolidated model validation summary for documentation.
        
        Creates a formatted summary suitable for copy-pasting into reports,
        including model performance, business interpretation, and recommendations.
        
        Args:
            test_metrics: Dictionary of test set metrics
            y_train: Training labels (for class imbalance calculation)
        """
        logger.info("\n" + "="*70)
        logger.info("MODEL VALIDATION SUMMARY")
        logger.info("="*70)
        
        # Calculate class imbalance
        n_positive = y_train.sum()
        n_negative = len(y_train) - n_positive
        imbalance_ratio = n_negative / n_positive if n_positive > 0 else float('inf')
        positive_pct = (n_positive / len(y_train)) * 100
        
        # Model information
        logger.info("\n[MODEL INFORMATION]")
        logger.info(f"  Model Type:           {type(self.model).__name__}")
        logger.info(f"  Model Name:           {self.model_name}")
        logger.info(f"  Training Samples:     {len(y_train):,}")
        logger.info(f"  Features:             {self.model.n_features_in_}")
        logger.info(f"  Random State:         {self.random_state}")
        
        # Class distribution
        logger.info("\n[CLASS DISTRIBUTION]")
        logger.info(f"  Default Rate:         {positive_pct:.2f}% ({n_positive:,}/{len(y_train):,})")
        logger.info(f"  No-Default Rate:      {100-positive_pct:.2f}% ({n_negative:,}/{len(y_train):,})")
        logger.info(f"  Imbalance Ratio:      {imbalance_ratio:.2f}:1 (negative:positive)")
        
        # Performance metrics
        roc_auc = test_metrics.get('roc_auc', 0)
        pr_auc = test_metrics.get('pr_auc', 0)
        recall = test_metrics.get('recall', 0)
        precision = test_metrics.get('precision', 0)
        f1_score = test_metrics.get('f1_score', 0)
        threshold = test_metrics.get('threshold', 0.5)
        
        logger.info("\n[PERFORMANCE METRICS]")
        logger.info(f"  ROC-AUC:              {roc_auc:.4f}  (Primary: discrimination ability)")
        logger.info(f"  PR-AUC:               {pr_auc:.4f}  (Imbalanced data robustness)")
        logger.info(f"  Recall:               {recall:.4f}  ({recall*100:.1f}% of defaults detected)")
        logger.info(f"  Precision:            {precision:.4f}  ({precision*100:.1f}% accuracy when predicting default)")
        logger.info(f"  F1-Score:             {f1_score:.4f}  (Harmonic mean of precision/recall)")
        logger.info(f"  Optimal Threshold:    {threshold:.2f}   (vs. default 0.50)")
        
        # Business interpretation
        logger.info("\n[BUSINESS INTERPRETATION]")
        
        # ROC-AUC interpretation
        if roc_auc >= 0.80:
            roc_assessment = "Excellent discrimination - Model strongly separates defaults from non-defaults"
        elif roc_auc >= 0.70:
            roc_assessment = "Good discrimination - Acceptable for production use"
        elif roc_auc >= 0.60:
            roc_assessment = "Fair discrimination - Suitable for preliminary screening, needs improvement"
        else:
            roc_assessment = "Poor discrimination - Model requires significant improvement"
        logger.info(f"  ROC-AUC Assessment:   {roc_assessment}")
        
        # Recall interpretation (critical for credit risk)
        if recall >= 0.70:
            recall_assessment = "Strong default detection - Catches majority of risky applicants"
            recall_risk = "Low risk of missed defaults"
        elif recall >= 0.50:
            recall_assessment = "Moderate default detection - Balanced approach"
            recall_risk = "Moderate risk of missed defaults"
        elif recall >= 0.35:
            recall_assessment = "Acceptable default detection - Meets minimum threshold"
            recall_risk = "Higher risk of missed defaults, monitor closely"
        else:
            recall_assessment = "LOW default detection - Critical improvement needed"
            recall_risk = "HIGH RISK: Significant defaults being missed"
        logger.info(f"  Recall Assessment:    {recall_assessment}")
        logger.info(f"  Risk Level:           {recall_risk}")
        
        # Precision interpretation
        if precision >= 0.50:
            precision_assessment = "Good precision - Low false alarm rate"
        elif precision >= 0.30:
            precision_assessment = "Moderate precision - Acceptable false alarm rate"
        elif precision >= 0.15:
            precision_assessment = "Fair precision - Higher false alarms expected"
        else:
            precision_assessment = "Low precision - Many false alarms, may reject good applicants"
        logger.info(f"  Precision Assessment: {precision_assessment}")
        
        # Overall model recommendation
        logger.info("\n[RECOMMENDATION]")
        
        if roc_auc >= 0.70 and recall >= 0.50:
            recommendation = "✓ MODEL READY FOR PRODUCTION"
            details = "Model demonstrates strong performance on key metrics. Suitable for deployment with ongoing monitoring."
        elif roc_auc >= 0.60 and recall >= 0.35:
            recommendation = "⚠️  MODEL ACCEPTABLE WITH CAUTION"
            details = "Model meets minimum standards but requires close monitoring. Consider additional feature engineering or data collection."
        elif roc_auc < 0.60 or recall < 0.35:
            recommendation = "✗ MODEL NEEDS IMPROVEMENT"
            if roc_auc < 0.60:
                details = "ROC-AUC below acceptable threshold (0.60). Model lacks discrimination ability. Recommend: feature engineering, algorithm changes, or data quality review."
            else:
                details = "Recall below minimum threshold (0.35). Too many defaults being missed. Recommend: adjust threshold, use cost-sensitive learning, or collect more default examples."
        else:
            recommendation = "⚠️  REVIEW REQUIRED"
            details = "Model shows mixed results. Conduct thorough business impact analysis before deployment."
        
        logger.info(f"  Status:               {recommendation}")
        logger.info(f"  Details:              {details}")
        
        # Financial impact estimate (rough)
        logger.info("\n[EXPECTED OPERATIONAL IMPACT]")
        defaults_detected = int(recall * n_positive)
        defaults_missed = n_positive - defaults_detected
        false_alarms = int((1/precision - 1) * defaults_detected) if precision > 0 else 0
        
        logger.info(f"  Per 1000 Applicants:")
        logger.info(f"    - Expected defaults:        {int(positive_pct * 10)} applicants")
        logger.info(f"    - Defaults detected:        ~{int(recall * positive_pct * 10)} applicants ({recall*100:.0f}% catch rate)")
        logger.info(f"    - Defaults missed:          ~{int((1-recall) * positive_pct * 10)} applicants (potential losses)")
        logger.info(f"    - False rejections:         ~{int(false_alarms * 10 / n_positive)} good applicants (opportunity cost)")
        
        # Key takeaways
        logger.info("\n[KEY TAKEAWAYS]")
        logger.info(f"  1. Model achieves {roc_auc:.1%} discrimination accuracy (ROC-AUC)")
        logger.info(f"  2. Detects {recall:.1%} of actual defaults (Recall)")
        logger.info(f"  3. {precision:.1%} of predicted defaults are true positives (Precision)")
        logger.info(f"  4. Optimized threshold {threshold:.2f} balances detection vs false alarms")
        logger.info(f"  5. Class imbalance ({imbalance_ratio:.1f}:1) addressed via balanced class weights")
        
        logger.info("\n" + "="*70)
        logger.info("END OF VALIDATION SUMMARY")
        logger.info("="*70)
    
    def optimize_threshold(
        self,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        min_recall: float = 0.35,
    ) -> Tuple[float, str]:
        """Find optimal probability threshold for classification.
        
        Strategy:
        1. Evaluate thresholds from 0.1 to 0.9 (step=0.01)
        2. Select threshold that maximizes F1-score
        3. If best threshold has recall < min_recall, select threshold that meets recall constraint
        
        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities for positive class
            min_recall: Minimum acceptable recall threshold
            
        Returns:
            Tuple of (optimal_threshold, justification_message)
        """
        thresholds = np.arange(0.1, 0.91, 0.01)  # 0.1 to 0.9 inclusive
        best_f1 = 0
        best_threshold = 0.5
        best_recall = 0
        
        # Store all threshold results for recall constraint
        threshold_results = []
        
        for threshold in thresholds:
            y_pred = (y_pred_proba >= threshold).astype(int)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            precision = precision_score(y_true, y_pred, zero_division=0)
            
            threshold_results.append({
                'threshold': threshold,
                'f1': f1,
                'recall': recall,
                'precision': precision,
            })
            
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold
                best_recall = recall
        
        # Check if best F1 threshold meets recall constraint
        if best_recall >= min_recall:
            justification = (
                f"Threshold {best_threshold:.2f} maximizes F1-score ({best_f1:.4f}) "
                f"while maintaining acceptable recall ({best_recall:.1%} >= {min_recall:.1%}). "
                f"Business impact: Optimizes balance between detecting defaults and minimizing false alarms."
            )
            return best_threshold, justification
        else:
            # Find threshold that meets recall constraint with highest F1
            valid_thresholds = [r for r in threshold_results if r['recall'] >= min_recall]
            
            if valid_thresholds:
                # Among valid thresholds, select one with highest F1
                best_valid = max(valid_thresholds, key=lambda x: x['f1'])
                threshold = best_valid['threshold']
                justification = (
                    f"Threshold {threshold:.2f} ensures minimum recall constraint ({best_valid['recall']:.1%} >= {min_recall:.1%}) "
                    f"with F1-score {best_valid['f1']:.4f}. "
                    f"Business impact: Prioritizes default detection to minimize credit losses, "
                    f"even at cost of higher false positive rate (precision: {best_valid['precision']:.1%})."
                )
                return threshold, justification
            else:
                # No threshold meets recall constraint, use lowest threshold
                lowest_result = threshold_results[0]  # threshold = 0.1
                logger.warning(
                    f"⚠️  No threshold achieves recall >= {min_recall:.1%}. "
                    f"Using minimum threshold {lowest_result['threshold']:.2f} "
                    f"(recall: {lowest_result['recall']:.1%})"
                )
                justification = (
                    f"Threshold {lowest_result['threshold']:.2f} maximizes recall ({lowest_result['recall']:.1%}) "
                    f"but fails to meet {min_recall:.1%} constraint. "
                    f"Business impact: Model may have insufficient predictive power for reliable default detection."
                )
                return lowest_result['threshold'], justification
    
    def evaluate_model(
        self,
        X_test: pd.DataFrame,
        y_test: np.ndarray,
        dataset_name: str = "Test",
    ) -> Dict[str, float]:
        """Evaluate model on a dataset.
        
        Args:
            X_test: Features
            y_test: Labels
            dataset_name: Name of dataset for logging (e.g., 'Test', 'Validation')
            
        Returns:
            Dictionary of metrics
        """
        logger.info("\\n" + "="*70)
        logger.info("STEP 3: Evaluating Model")
        logger.info("="*70)
        
        # Get predicted probabilities (unchanged)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Optimize threshold instead of using fixed 0.5
        optimal_threshold, justification = self.optimize_threshold(y_test, y_pred_proba, min_recall=0.35)
        
        # Apply optimal threshold to get predictions
        y_pred = (y_pred_proba >= optimal_threshold).astype(int)
        
        # Log threshold optimization results
        logger.info("\\n" + "-"*70)
        logger.info("THRESHOLD OPTIMIZATION")
        logger.info("-"*70)
        logger.info(f"Optimal Threshold: {optimal_threshold:.2f} (evaluated range: 0.1 to 0.9)")
        logger.info(f"Justification: {justification}")
        logger.info("-"*70)
        
        # Calculate metrics (industry credit risk standards)
        metrics = {
            "roc_auc": roc_auc_score(y_test, y_pred_proba),
            "pr_auc": average_precision_score(y_test, y_pred_proba),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "f1_score": f1_score(y_test, y_pred, zero_division=0),
            "accuracy": accuracy_score(y_test, y_pred),
            "threshold": optimal_threshold,  # Store optimal threshold
        }
        
        # Log metrics (industry credit risk evaluation standards)
        logger.info(f"\n{dataset_name} Set Performance:")
        logger.info("="*70)
        logger.info("\\n📊 PRIMARY METRIC (Industry Standard for Credit Risk):")
        logger.info(f"   ROC-AUC:  {metrics['roc_auc']:.4f}  ← Discrimination ability across all thresholds")
        
        logger.info("\\n📈 SECONDARY METRICS (Critical for Imbalanced Data):")
        logger.info(f"   PR-AUC:   {metrics['pr_auc']:.4f}  ← Precision-Recall trade-off (robust to class imbalance)")
        
        # Recall with threshold warning
        recall_value = metrics['recall']
        recall_status = "⚠️  WARNING: CRITICALLY LOW" if recall_value < 0.3 else "✓ Acceptable" if recall_value < 0.5 else "✓ Good"
        logger.info(f"   Recall:   {recall_value:.4f}  ← Default detection rate at {optimal_threshold:.2f} threshold  [{recall_status}]")
        
        if recall_value < 0.3:
            logger.warning("\\n" + "!"*70)
            logger.warning("⚠️  CRITICAL: Recall below 0.30 threshold!")
            logger.warning(f"   Current recall: {recall_value:.1%} of defaults are being detected")
            logger.warning("   Risk: Missing {:.1%} of actual defaults may result in significant losses".format(1 - recall_value))
            logger.warning("   Recommendation: Adjust decision threshold or retrain with cost-sensitive learning")
            logger.warning("!"*70 + "\\n")
        
        logger.info("\\n📉 SUPPORTING METRICS:")
        logger.info(f"   Precision: {metrics['precision']:.4f}  ← Positive predictive value")
        logger.info(f"   F1 Score:  {metrics['f1_score']:.4f}  ← Harmonic mean of precision & recall")
        logger.info(f"   Accuracy:  {metrics['accuracy']:.4f}  (⚠️  Not recommended for imbalanced credit data)")
        
        # Detailed classification report
        logger.info("\\n" + "-"*70)
        logger.info("Detailed Classification Report:")
        logger.info("-"*70)
        logger.info("\\n" + classification_report(y_test, y_pred, target_names=["No Default", "Default"]))
        
        return metrics
    
    def save_artifacts(
        self,
        metrics: Dict[str, float] = None,
        X_train: pd.DataFrame = None,
        compute_shap: bool = True,
    ) -> None:
        """Save model and artifacts.
        
        Preprocessing artifacts are saved separately in models/preprocessor.joblib.
        Model is saved in models/model.joblib.
        
        Args:
            metrics: Optional evaluation metrics to include
            X_train: Training features (required for SHAP)
            compute_shap: Whether to compute and save SHAP explainer
        """
        logger.info("\\n" + "="*70)
        logger.info("STEP 4: Saving Artifacts")
        logger.info("="*70)
        
        if self.model is None:
            raise ValueError("No model to save. Train model first.")
                # Compute and save SHAP explainer (if requested and X_train provided)
        if compute_shap and X_train is not None:
            shap_success = self.compute_and_save_shap(X_train, background_size=100)
            if not shap_success:
                logger.info("Note: Model saved without SHAP explainer")
        elif compute_shap and X_train is None:
            logger.warning("⚠️  X_train not provided. Skipping SHAP computation.")
            logger.info("  To enable SHAP: pass X_train to save_artifacts()")
                # Check if model already exists
        model_path = self.models_dir / "model.joblib"
        if model_path.exists():
            logger.warning(f"Model already exists at {model_path}")
            logger.warning("Saving to model_new.joblib to avoid overwriting")
            model_path = self.models_dir / "model_new.joblib"
        
        # Create comprehensive metadata
        training_timestamp = datetime.utcnow().isoformat() + "Z"
        
        metadata = {
            "model_type": type(self.model).__name__,
            "model_name": self.model_name,
            "training_timestamp": training_timestamp,
            "feature_count": self.model.n_features_in_,
            "schema_version": SCHEMA_VERSION,
            "random_state": self.random_state,
            "evaluation_metrics": {
                "roc_auc": metrics.get("roc_auc", 0.0) if metrics else 0.0,
                "pr_auc": metrics.get("pr_auc", 0.0) if metrics else 0.0,
                "recall": metrics.get("recall", 0.0) if metrics else 0.0,
                "precision": metrics.get("precision", 0.0) if metrics else 0.0,
                "f1_score": metrics.get("f1_score", 0.0) if metrics else 0.0,
                "accuracy": metrics.get("accuracy", 0.0) if metrics else 0.0,
            },
            "feature_names": self.preprocessor.feature_columns,
        }
        
        # Save model artifact with metadata
        model_artifact = {
            "model": self.model,
            "metadata": metadata,
            # Legacy fields for backwards compatibility
            "model_name": self.model_name,
            "model_class": type(self.model).__name__,
            "schema_version": SCHEMA_VERSION,
            "random_state": self.random_state,
            "metrics": metrics or {},
            "n_features": self.model.n_features_in_,
            "feature_names": self.preprocessor.feature_columns,
        }
        
        joblib.dump(model_artifact, model_path)
        logger.info(f"✓ Successfully saved model to {model_path}")
        logger.info(f"  Model name: {self.model_name}")
        logger.info(f"  Model type: {type(self.model).__name__}")
        logger.info(f"  Features: {self.model.n_features_in_}")
        logger.info(f"  Schema version: {SCHEMA_VERSION}")
        logger.info(f"  Training timestamp: {training_timestamp}")
        logger.info(f"  ROC-AUC: {metadata['evaluation_metrics']['roc_auc']:.4f}")
        logger.info(f"  Recall: {metadata['evaluation_metrics']['recall']:.4f}")
        
        # Preprocessing pipeline is already saved by preprocessor.preprocess()
        preprocessor_path = self.models_dir / "preprocessor.joblib"
        if preprocessor_path.exists():
            logger.info(f"✓ Preprocessing artifacts already saved at {preprocessor_path}")
        else:
            logger.warning(f"Preprocessing artifacts not found at {preprocessor_path}")
        
        logger.info("\\n" + "="*70)
        logger.info("✓ Training Pipeline Complete!")
        logger.info("="*70)
    
    def train_pipeline(
        self,
        raw_filename: str = "raw.csv",
        model_params: Dict[str, Any] = None,
    ) -> Dict[str, float]:
        """Execute complete training pipeline.
        
        Args:
            raw_filename: Name of raw CSV file
            model_params: Model hyperparameters
            
        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("\\n" + "="*70)
        logger.info("CREDIT RISK MODEL TRAINING PIPELINE")
        logger.info("="*70)
        logger.info(f"Schema version: {SCHEMA_VERSION}")
        logger.info(f"Random state: {self.random_state}")
        logger.info("\\n")
        
        # Load and preprocess
        X_train, y_train, X_val, y_val, X_test, y_test = self.load_and_preprocess_data(raw_filename)
        
        # Train
        self.train_model(X_train, y_train, model_params)
        
        # Evaluate on validation set
        logger.info("\\n" + "="*70)
        logger.info("VALIDATION SET EVALUATION")
        logger.info("="*70)
        val_metrics = self.evaluate_model(X_val, y_val, dataset_name="Validation")
        
        # Evaluate on test set
        logger.info("\\n" + "="*70)
        logger.info("TEST SET EVALUATION")
        logger.info("="*70)
        test_metrics = self.evaluate_model(X_test, y_test, dataset_name="Test")
        
        # Log comparison (industry credit risk standards)
        logger.info("\n" + "="*70)
        logger.info("VALIDATION vs TEST COMPARISON (Industry Credit Risk Standards)")
        logger.info("="*70)
        logger.info("\n📊 Primary Metric:")
        logger.info(f"   {'ROC-AUC':<12} Val: {val_metrics['roc_auc']:.4f}  Test: {test_metrics['roc_auc']:.4f}  Δ {test_metrics['roc_auc'] - val_metrics['roc_auc']:+.4f}")
        
        logger.info("\n📈 Critical Metrics for Imbalanced Data:")
        logger.info(f"   {'PR-AUC':<12} Val: {val_metrics['pr_auc']:.4f}  Test: {test_metrics['pr_auc']:.4f}  Δ {test_metrics['pr_auc'] - val_metrics['pr_auc']:+.4f}")
        logger.info(f"   {'Recall':<12} Val: {val_metrics['recall']:.4f}  Test: {test_metrics['recall']:.4f}  Δ {test_metrics['recall'] - val_metrics['recall']:+.4f}")
        
        logger.info("\n📉 Supporting Metrics:")
        logger.info(f"   {'Precision':<12} Val: {val_metrics['precision']:.4f}  Test: {test_metrics['precision']:.4f}  Δ {test_metrics['precision'] - val_metrics['precision']:+.4f}")
        logger.info(f"   {'F1-Score':<12} Val: {val_metrics['f1_score']:.4f}  Test: {test_metrics['f1_score']:.4f}  Δ {test_metrics['f1_score'] - val_metrics['f1_score']:+.4f}")
        logger.info(f"   {'Accuracy':<12} Val: {val_metrics['accuracy']:.4f}  Test: {test_metrics['accuracy']:.4f}  Δ {test_metrics['accuracy'] - val_metrics['accuracy']:+.4f}  (⚠️  Not primary metric)")
        
        # Overfitting check
        roc_diff = abs(test_metrics['roc_auc'] - val_metrics['roc_auc'])
        if roc_diff > 0.05:
            logger.warning(f"\n⚠️  Significant ROC-AUC gap detected ({roc_diff:.4f}): Possible overfitting")
        else:
            logger.info(f"\n✓ Model generalization: ROC-AUC gap within acceptable range ({roc_diff:.4f} < 0.05)")
        
        # Generate consolidated validation summary
        self.generate_validation_summary(test_metrics, y_train)
        
        # Save (use test metrics for artifact metadata, pass X_train for SHAP)
        self.save_artifacts(test_metrics, X_train=X_train, compute_shap=True)
        
        return test_metrics


def train(
    raw_filename: str = "raw.csv",
    data_dir: str = "data",
    models_dir: str = "models",
    random_state: int = 42,
    model_name: str = "random_forest",
) -> Dict[str, float]:
    """Convenience function to train model.
    
    Args:
        raw_filename: Name of raw CSV file in data/raw directory
        data_dir: Base data directory
        models_dir: Directory to save models
        random_state: Random seed
        model_name: Name of model from registry (default: 'random_forest')
        
    Returns:
        Dictionary of evaluation metrics
    """
    # List available models
    available_models = list_available_models()
    logger.info(f"Available models: {', '.join(available_models)}")
    
    trainer = CreditRiskTrainer(
        data_dir=data_dir,
        models_dir=models_dir,
        random_state=random_state,
        model_name=model_name,
    )
    
    metrics = trainer.train_pipeline(raw_filename)
    
    return metrics


if __name__ == "__main__":
    # Train model
    try:
        metrics = train()
        print("\\n" + "="*70)
        print("✓ Training complete! Metrics:")
        for metric_name, value in metrics.items():
            print(f"  {metric_name}: {value:.4f}")
        print("="*70)
    except FileNotFoundError as e:
        print(f"\\n✗ Training failed: {e}")
        print("\\nPlease ensure training data exists in data/raw/raw.csv")
    except Exception as e:
        print(f"\\n✗ Training failed: {e}")
        import traceback
        traceback.print_exc()
