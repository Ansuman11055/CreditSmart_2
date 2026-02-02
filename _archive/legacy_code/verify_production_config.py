#!/usr/bin/env python3
"""
Production Model Verification Script

Validates that the deployed RandomForest model meets all production constraints
for credit risk modeling.
"""
import joblib
import sys

def verify_production_config():
    """Verify production model configuration."""
    
    print("="*70)
    print("PRODUCTION-GRADE RANDOMFOREST VERIFICATION")
    print("="*70)
    
    # Load model
    try:
        model_data = joblib.load('models/model.joblib')
        model = model_data['model']
    except Exception as e:
        print(f"\nERROR: Failed to load model: {e}")
        return False
    
    # Display configuration
    print("\nConfiguration:")
    print(f"  n_estimators: {model.n_estimators} (target: 300-600)")
    print(f"  max_depth: {model.max_depth} (target: 8-12)")
    print(f"  min_samples_split: {model.min_samples_split}")
    print(f"  min_samples_leaf: {model.min_samples_leaf} (target: 200-500)")
    print(f"  max_features: {model.max_features} (target: sqrt)")
    print(f"  random_state: {model.random_state}")
    print(f"  n_jobs: {model.n_jobs}")
    print(f"  class_weight: {model.class_weight}")
    print(f"  bootstrap: {model.bootstrap}")
    print(f"  oob_score: {model.oob_score}")
    
    # Validate constraints
    print("\nConstraint Validation:")
    checks = [
        ("n_estimators in [300, 600]", 300 <= model.n_estimators <= 600),
        ("max_depth in [8, 12]", 8 <= model.max_depth <= 12),
        ("min_samples_leaf in [200, 500]", 200 <= model.min_samples_leaf <= 500),
        ("max_features == 'sqrt'", model.max_features == "sqrt"),
        ("random_state == 42", model.random_state == 42),
        ("n_jobs == -1", model.n_jobs == -1),
        ("class_weight == 'balanced'", model.class_weight == "balanced"),
        ("bootstrap == True", model.bootstrap == True),
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"  [{symbol}] {check_name}: {status}")
        if not result:
            all_passed = False
    
    # Display metrics
    print("\nPerformance Metrics:")
    metrics = model_data['metrics']
    print(f"  ROC AUC:   {metrics['roc_auc']:.4f} (primary metric)")
    print(f"  PR AUC:    {metrics['pr_auc']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f} (sensitivity)")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  F1 Score:  {metrics['f1_score']:.4f}")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    
    # Model metadata
    print("\nModel Metadata:")
    print(f"  Model name: {model_data['model_name']}")
    print(f"  Model class: {model_data['model_class']}")
    print(f"  Features: {model_data['n_features']}")
    print(f"  Schema version: {model_data['schema_version']}")
    print(f"  Random state: {model_data['random_state']}")
    
    # Final status
    print("\n" + "="*70)
    if all_passed:
        print("STATUS: PRODUCTION READY")
        print("All constraints satisfied. Model meets production requirements.")
    else:
        print("STATUS: VALIDATION FAILED")
        print("Some constraints not satisfied. Review configuration.")
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    success = verify_production_config()
    sys.exit(0 if success else 1)
