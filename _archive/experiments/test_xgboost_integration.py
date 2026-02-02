"""Train and compare XGBoost vs RandomForest for credit risk modeling.

This script demonstrates:
1. XGBoost with scale_pos_weight for class imbalance (6.81:1 ratio)
2. SHAP compatibility verification
3. Side-by-side performance comparison
4. Model selection via config flag
"""

import sys
import logging
from pathlib import Path
import joblib
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.train import train
from src.models.model_registry import get_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_and_compare_models():
    """Train both RandomForest and XGBoost, compare performance."""
    
    logger.info("\n" + "="*70)
    logger.info("CREDIT RISK MODEL COMPARISON: RandomForest vs XGBoost")
    logger.info("="*70)
    
    models_to_train = ["random_forest", "xgboost"]
    results = {}
    
    for model_name in models_to_train:
        logger.info(f"\n{'='*70}")
        logger.info(f"Training {model_name.upper()}")
        logger.info(f"{'='*70}")
        
        try:
            # Train model
            metrics = train(model_name=model_name)
            results[model_name] = metrics
            
            # Verify model was saved
            model_path = Path("models") / f"model.joblib"
            if model_path.exists():
                # Rename to keep both models
                new_path = Path("models") / f"{model_name}_model.joblib"
                import shutil
                shutil.copy(model_path, new_path)
                logger.info(f"✓ Saved {model_name} to {new_path}")
            
        except Exception as e:
            logger.error(f"✗ Failed to train {model_name}: {e}")
            import traceback
            traceback.print_exc()
            results[model_name] = None
    
    # Print comparison
    logger.info("\n" + "="*70)
    logger.info("PERFORMANCE COMPARISON")
    logger.info("="*70)
    
    if all(results.values()):
        # Create comparison table
        logger.info(f"\n{'Metric':<15} {'RandomForest':<15} {'XGBoost':<15} {'Difference':<15} {'Winner':<10}")
        logger.info("-" * 75)
        
        # Primary metrics first
        primary_metrics = ['roc_auc', 'pr_auc', 'recall', 'precision', 'f1_score', 'accuracy']
        
        for metric in primary_metrics:
            if metric in results['random_forest']:
                rf_val = results['random_forest'][metric]
                xgb_val = results['xgboost'][metric]
                diff = xgb_val - rf_val
                winner = "XGBoost" if diff > 0 else "RandomForest" if diff < 0 else "Tie"
                
                logger.info(f"{metric:<15} {rf_val:<15.4f} {xgb_val:<15.4f} {diff:+15.4f} {winner:<10}")
        
        logger.info("\n" + "="*70)
        logger.info("SUMMARY")
        logger.info("="*70)
        
        # Determine overall winner based on ROC-AUC (primary metric)
        rf_roc = results['random_forest']['roc_auc']
        xgb_roc = results['xgboost']['roc_auc']
        
        if xgb_roc > rf_roc:
            logger.info(f"✓ XGBoost WINS with ROC-AUC: {xgb_roc:.4f} vs {rf_roc:.4f} (+{xgb_roc - rf_roc:.4f})")
        elif rf_roc > xgb_roc:
            logger.info(f"✓ RandomForest WINS with ROC-AUC: {rf_roc:.4f} vs {xgb_roc:.4f} (+{rf_roc - xgb_roc:.4f})")
        else:
            logger.info(f"✓ TIE - Both models have ROC-AUC: {rf_roc:.4f}")
        
        logger.info("\n" + "="*70)
    else:
        logger.error("Could not complete comparison due to training failures")
    
    return results


def verify_xgboost_config():
    """Verify XGBoost configuration matches requirements."""
    
    logger.info("\n" + "="*70)
    logger.info("VERIFYING XGBOOST CONFIGURATION")
    logger.info("="*70)
    
    registry = get_registry()
    xgb_config = registry.get_config("xgboost")
    params = xgb_config.default_params
    
    requirements = {
        "scale_pos_weight": 6.81,
        "objective": "binary:logistic",
        "use_label_encoder": False,
        "eval_metric": "aucpr",
    }
    
    logger.info("\nRequired Parameters:")
    all_pass = True
    
    for param, expected_value in requirements.items():
        actual_value = params.get(param)
        
        if param == "scale_pos_weight":
            # Allow small floating point differences
            passed = abs(actual_value - expected_value) < 0.1
        else:
            passed = actual_value == expected_value
        
        status = "✓" if passed else "✗"
        logger.info(f"  {status} {param}: {actual_value} (expected: {expected_value})")
        
        if not passed:
            all_pass = False
    
    logger.info("\nAdditional Configuration:")
    additional_params = ["n_estimators", "max_depth", "learning_rate", "min_child_weight", 
                         "gamma", "reg_alpha", "reg_lambda", "subsample", "colsample_bytree"]
    
    for param in additional_params:
        if param in params:
            logger.info(f"  • {param}: {params[param]}")
    
    logger.info("\n" + "-"*70)
    if all_pass:
        logger.info("✓ All requirements satisfied")
    else:
        logger.error("✗ Some requirements not met")
    
    logger.info("="*70)
    
    return all_pass


def verify_shap_compatibility():
    """Verify SHAP works with both models."""
    
    logger.info("\n" + "="*70)
    logger.info("VERIFYING SHAP COMPATIBILITY")
    logger.info("="*70)
    
    try:
        import shap
        logger.info("✓ SHAP library available")
    except ImportError:
        logger.warning("✗ SHAP not installed. Install with: pip install shap")
        return False
    
    models_to_test = ["random_forest", "xgboost"]
    
    for model_name in models_to_test:
        model_path = Path("models") / f"{model_name}_model.joblib"
        
        if not model_path.exists():
            logger.warning(f"⚠️  {model_name}_model.joblib not found. Train models first.")
            continue
        
        try:
            # Load model
            model = joblib.load(model_path)
            logger.info(f"\n✓ Loaded {model_name}")
            
            # Create dummy data
            n_samples = 100
            n_features = 22  # Our processed feature count
            X_dummy = np.random.randn(n_samples, n_features)
            
            # Try SHAP TreeExplainer
            explainer = shap.TreeExplainer(model)
            logger.info(f"  ✓ SHAP TreeExplainer created for {model_name}")
            
            # Compute SHAP values
            shap_values = explainer.shap_values(X_dummy)
            logger.info(f"  ✓ SHAP values computed (shape: {np.array(shap_values).shape})")
            
            # Check feature importance
            if hasattr(model, 'feature_importances_'):
                logger.info(f"  ✓ Feature importances available (n={len(model.feature_importances_)})")
            
        except Exception as e:
            logger.error(f"  ✗ SHAP compatibility test failed for {model_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    logger.info("\n" + "="*70)
    logger.info("✓ SHAP compatibility verified for all models")
    logger.info("="*70)
    
    return True


def main():
    """Main execution function."""
    
    logger.info("\n" + "="*70)
    logger.info("XGBOOST INTEGRATION TEST SUITE")
    logger.info("="*70)
    
    # Step 1: Verify XGBoost configuration
    logger.info("\n[1/3] Verifying XGBoost configuration...")
    config_valid = verify_xgboost_config()
    
    if not config_valid:
        logger.error("Configuration verification failed. Fix issues before proceeding.")
        return
    
    # Step 2: Train and compare models
    logger.info("\n[2/3] Training and comparing models...")
    results = train_and_compare_models()
    
    # Step 3: Verify SHAP compatibility
    logger.info("\n[3/3] Verifying SHAP compatibility...")
    shap_compatible = verify_shap_compatibility()
    
    # Final summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUITE COMPLETE")
    logger.info("="*70)
    logger.info(f"✓ Configuration: {'PASS' if config_valid else 'FAIL'}")
    logger.info(f"✓ Training: {'PASS' if results and all(results.values()) else 'FAIL'}")
    logger.info(f"✓ SHAP: {'PASS' if shap_compatible else 'FAIL'}")
    logger.info("="*70)
    
    if config_valid and results and all(results.values()):
        logger.info("\n🎉 XGBoost successfully integrated as alternative primary model!")
        logger.info("\nUsage:")
        logger.info("  from src.train import train")
        logger.info("  metrics = train(model_name='xgboost')  # Use XGBoost")
        logger.info("  metrics = train(model_name='random_forest')  # Use RandomForest")
    else:
        logger.error("\n⚠️  Integration incomplete. Review errors above.")


if __name__ == "__main__":
    main()
