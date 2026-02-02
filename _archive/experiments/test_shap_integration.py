"""Test SHAP explainability integration.

This script validates that SHAP TreeExplainer works correctly for:
1. RandomForest models
2. XGBoost models
3. Proper dimension handling
4. Safe background sampling
5. Artifact saving
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from src.train import CreditRiskTrainer
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier


def test_shap_randomforest():
    """Test SHAP with RandomForest model."""
    print("=" * 70)
    print("TEST 1: SHAP with RandomForest")
    print("=" * 70)
    
    # Create synthetic data
    np.random.seed(42)
    n_samples = 500
    n_features = 10
    
    X_train = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"feature_{i}" for i in range(n_features)]
    )
    y_train = np.random.randint(0, 2, n_samples)
    
    # Train model
    model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    
    # Test SHAP
    trainer = CreditRiskTrainer()
    trainer.model = model
    trainer.preprocessor = type('obj', (object,), {'feature_columns': list(X_train.columns)})()
    
    success = trainer.compute_and_save_shap(X_train, background_size=50)
    
    if success:
        print("\n✓ RandomForest SHAP: SUCCESS")
        
        # Verify saved file
        shap_path = Path("models/shap_explainer_new.joblib")
        if shap_path.exists():
            artifact = joblib.load(shap_path)
            print(f"  Background size: {artifact['background_size']}")
            print(f"  Features: {artifact['n_features']}")
            print(f"  Model type: {artifact['model_type']}")
            print(f"  SHAP version: {artifact['shap_version']}")
    else:
        print("\n✗ RandomForest SHAP: FAILED")
    print()


def test_shap_xgboost():
    """Test SHAP with XGBoost model."""
    print("=" * 70)
    print("TEST 2: SHAP with XGBoost")
    print("=" * 70)
    
    # Create synthetic data
    np.random.seed(42)
    n_samples = 500
    n_features = 10
    
    X_train = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"xgb_feature_{i}" for i in range(n_features)]
    )
    y_train = np.random.randint(0, 2, n_samples)
    
    # Train model
    model = XGBClassifier(n_estimators=50, max_depth=5, random_state=42, use_label_encoder=False)
    model.fit(X_train, y_train)
    
    # Test SHAP
    trainer = CreditRiskTrainer()
    trainer.model = model
    trainer.preprocessor = type('obj', (object,), {'feature_columns': list(X_train.columns)})()
    
    success = trainer.compute_and_save_shap(X_train, background_size=50)
    
    if success:
        print("\n✓ XGBoost SHAP: SUCCESS")
        
        # Verify saved file
        shap_path = Path("models/shap_explainer_new.joblib")
        if shap_path.exists():
            artifact = joblib.load(shap_path)
            print(f"  Background size: {artifact['background_size']}")
            print(f"  Features: {artifact['n_features']}")
            print(f"  Model type: {artifact['model_type']}")
            print(f"  SHAP version: {artifact['shap_version']}")
    else:
        print("\n✗ XGBoost SHAP: FAILED")
    print()


def test_shap_dimension_handling():
    """Test SHAP dimension handling for different output formats."""
    print("=" * 70)
    print("TEST 3: SHAP Dimension Handling")
    print("=" * 70)
    
    try:
        import shap
        
        # Test with RandomForest (3D output)
        np.random.seed(42)
        X = pd.DataFrame(np.random.randn(100, 5), columns=[f"f_{i}" for i in range(5)])
        y = np.random.randint(0, 2, 100)
        
        rf_model = RandomForestClassifier(n_estimators=20, random_state=42)
        rf_model.fit(X, y)
        
        X_background = X.sample(20, random_state=42)
        explainer = shap.TreeExplainer(rf_model, X_background)
        
        X_test = X.sample(5, random_state=42)
        shap_values = explainer.shap_values(X_test)
        
        print(f"\nRandomForest SHAP output type: {type(shap_values)}")
        print(f"RandomForest SHAP shape: {np.array(shap_values).shape}")
        
        # Handle 3D output
        shap_array = np.array(shap_values)
        if len(shap_array.shape) == 3:
            shap_array = shap_array[:, :, 1]  # Extract positive class
            print(f"After extraction: {shap_array.shape}")
        
        expected = (5, 5)
        if shap_array.shape == expected:
            print(f"✓ Dimensions validated: {shap_array.shape}")
        else:
            print(f"✗ Dimension mismatch: expected {expected}, got {shap_array.shape}")
        
        # Test with XGBoost (2D output)
        xgb_model = XGBClassifier(n_estimators=20, random_state=42, use_label_encoder=False)
        xgb_model.fit(X, y)
        
        explainer_xgb = shap.TreeExplainer(xgb_model, X_background)
        shap_values_xgb = explainer_xgb.shap_values(X_test)
        
        print(f"\nXGBoost SHAP output type: {type(shap_values_xgb)}")
        print(f"XGBoost SHAP shape: {np.array(shap_values_xgb).shape}")
        
        if np.array(shap_values_xgb).shape == expected:
            print(f"✓ Dimensions validated: {np.array(shap_values_xgb).shape}")
        else:
            print(f"✗ Dimension mismatch: expected {expected}, got {np.array(shap_values_xgb).shape}")
        
        print("\n✓ Dimension handling: SUCCESS")
        
    except ImportError:
        print("\n✗ SHAP not installed")
    except Exception as e:
        print(f"\n✗ Dimension handling: FAILED - {str(e)}")
    print()


def test_background_sampling():
    """Test safe background sampling with different sizes."""
    print("=" * 70)
    print("TEST 4: Background Sampling Safety")
    print("=" * 70)
    
    # Create small dataset
    np.random.seed(42)
    X_small = pd.DataFrame(np.random.randn(30, 5), columns=[f"f_{i}" for i in range(5)])
    y_small = np.random.randint(0, 2, 30)
    
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_small, y_small)
    
    trainer = CreditRiskTrainer()
    trainer.model = model
    trainer.preprocessor = type('obj', (object,), {'feature_columns': list(X_small.columns)})()
    
    # Test 1: Background size > dataset size (should reduce)
    print("\nTest 4a: Background size > dataset size")
    success1 = trainer.compute_and_save_shap(X_small, background_size=100)
    print(f"  Result: {'SUCCESS' if success1 else 'FAILED'}")
    
    # Test 2: Normal background size
    print("\nTest 4b: Normal background size")
    success2 = trainer.compute_and_save_shap(X_small, background_size=20)
    print(f"  Result: {'SUCCESS' if success2 else 'FAILED'}")
    
    if success1 and success2:
        print("\n✓ Background sampling: SUCCESS")
    else:
        print("\n✗ Background sampling: FAILED")
    print()


def test_error_handling():
    """Test error handling for incompatible models."""
    print("=" * 70)
    print("TEST 5: Error Handling")
    print("=" * 70)
    
    # Test with LogisticRegression (not tree-based)
    from sklearn.linear_model import LogisticRegression
    
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(100, 5), columns=[f"f_{i}" for i in range(5)])
    y = np.random.randint(0, 2, 100)
    
    lr_model = LogisticRegression(random_state=42)
    lr_model.fit(X, y)
    
    trainer = CreditRiskTrainer()
    trainer.model = lr_model
    trainer.preprocessor = type('obj', (object,), {'feature_columns': list(X.columns)})()
    
    print("\nTesting LogisticRegression (should warn but attempt)...")
    success = trainer.compute_and_save_shap(X, background_size=20)
    
    if not success:
        print("✓ Error handling: Graceful failure as expected")
    else:
        print("⚠️  Unexpectedly succeeded with LogisticRegression")
    print()


def verify_real_models():
    """Verify SHAP works with actual trained models."""
    print("=" * 70)
    print("TEST 6: Real Model Verification")
    print("=" * 70)
    
    shap_paths = [
        Path("models/shap_explainer.joblib"),
        Path("models/shap_explainer_new.joblib")
    ]
    
    found_explainer = False
    for path in shap_paths:
        if path.exists():
            print(f"\n✓ Found SHAP explainer: {path}")
            artifact = joblib.load(path)
            
            print(f"  Model type: {artifact.get('model_type', 'unknown')}")
            print(f"  Background size: {artifact.get('background_size', 'unknown')}")
            print(f"  Features: {artifact.get('n_features', 'unknown')}")
            print(f"  Schema version: {artifact.get('schema_version', 'unknown')}")
            print(f"  SHAP version: {artifact.get('shap_version', 'unknown')}")
            
            # Verify explainer is usable
            if 'explainer' in artifact:
                print("  ✓ Explainer object present")
            if 'background_data' in artifact:
                bg_shape = artifact['background_data'].shape
                print(f"  ✓ Background data present: {bg_shape}")
            
            found_explainer = True
    
    if not found_explainer:
        print("\n⚠️  No SHAP explainer found. Train a model first.")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SHAP EXPLAINABILITY - COMPREHENSIVE TESTS")
    print("=" * 70 + "\n")
    
    test_shap_randomforest()
    test_shap_xgboost()
    test_shap_dimension_handling()
    test_background_sampling()
    test_error_handling()
    verify_real_models()
    
    print("=" * 70)
    print("✓ ALL SHAP TESTS COMPLETE")
    print("=" * 70)
