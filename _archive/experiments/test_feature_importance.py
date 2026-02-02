"""Test feature importance diagnostics.

This script demonstrates the feature importance analysis that shows:
1. Top 15 features by importance
2. Feature dominance warnings (>40%)
3. Missing or dropped features detection
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from src.train import CreditRiskTrainer

def test_feature_importance_normal():
    """Test with normal feature distribution (no dominance)."""
    print("=" * 70)
    print("TEST 1: Normal Feature Distribution (No Dominance)")
    print("=" * 70)
    
    # Create synthetic data
    np.random.seed(42)
    n_samples = 1000
    n_features = 10
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"feature_{i}" for i in range(n_features)]
    )
    y = np.random.randint(0, 2, n_samples)
    
    # Train RandomForest
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Create trainer and analyze
    trainer = CreditRiskTrainer()
    trainer.model = model
    trainer.analyze_feature_importance(X, top_n=10, dominance_threshold=0.40)
    print()


def test_feature_dominance():
    """Test with dominant feature (>40%)."""
    print("=" * 70)
    print("TEST 2: Feature Dominance (Single Feature >40%)")
    print("=" * 70)
    
    # Create synthetic data with one highly predictive feature
    np.random.seed(42)
    n_samples = 1000
    
    # Feature 0 is highly correlated with target
    feature_0 = np.random.randn(n_samples)
    y = (feature_0 > 0).astype(int)
    
    # Other features are noise
    other_features = np.random.randn(n_samples, 9)
    
    X = pd.DataFrame(
        np.column_stack([feature_0, other_features]),
        columns=[f"feature_{i}" for i in range(10)]
    )
    
    # Train RandomForest
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Create trainer and analyze
    trainer = CreditRiskTrainer()
    trainer.model = model
    trainer.analyze_feature_importance(X, top_n=10, dominance_threshold=0.40)
    print()


def test_xgboost_importance():
    """Test with XGBoost model."""
    print("=" * 70)
    print("TEST 3: XGBoost Feature Importance")
    print("=" * 70)
    
    # Create synthetic data
    np.random.seed(42)
    n_samples = 1000
    n_features = 15
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"xgb_feature_{i}" for i in range(n_features)]
    )
    y = np.random.randint(0, 2, n_samples)
    
    # Train XGBoost
    model = XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False)
    model.fit(X, y)
    
    # Create trainer and analyze
    trainer = CreditRiskTrainer()
    trainer.model = model
    trainer.analyze_feature_importance(X, top_n=15, dominance_threshold=0.40)
    print()


def test_feature_mismatch():
    """Test with feature count mismatch (simulates dropped features)."""
    print("=" * 70)
    print("TEST 4: Feature Count Mismatch (Dropped Features)")
    print("=" * 70)
    
    # Create synthetic data with more features than model sees
    np.random.seed(42)
    n_samples = 1000
    
    # Train with 10 features
    X_train = pd.DataFrame(
        np.random.randn(n_samples, 10),
        columns=[f"feature_{i}" for i in range(10)]
    )
    y = np.random.randint(0, 2, n_samples)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y)
    
    # But pass 12 feature names (simulating dropped features)
    X_test = pd.DataFrame(
        np.random.randn(n_samples, 12),
        columns=[f"feature_{i}" for i in range(12)]
    )
    
    # Create trainer and analyze
    trainer = CreditRiskTrainer()
    trainer.model = model
    trainer.analyze_feature_importance(X_test, top_n=10, dominance_threshold=0.40)
    print()


def compare_models():
    """Compare feature importance between RandomForest and XGBoost."""
    print("=" * 70)
    print("TEST 5: Compare RandomForest vs XGBoost Feature Importance")
    print("=" * 70)
    
    # Create synthetic data
    np.random.seed(42)
    n_samples = 2000
    n_features = 20
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"feature_{i:02d}" for i in range(n_features)]
    )
    # Create non-linear target
    y = ((X['feature_00'] > 0) & (X['feature_05'] > 0)).astype(int)
    y = y | ((X['feature_10'] < -1) | (X['feature_15'] < -1)).astype(int)
    
    print("\n--- RandomForest ---")
    rf_model = RandomForestClassifier(n_estimators=200, max_depth=5, random_state=42)
    rf_model.fit(X, y)
    
    trainer_rf = CreditRiskTrainer()
    trainer_rf.model = rf_model
    trainer_rf.analyze_feature_importance(X, top_n=10, dominance_threshold=0.40)
    
    print("\n--- XGBoost ---")
    xgb_model = XGBClassifier(n_estimators=200, max_depth=5, random_state=42, use_label_encoder=False)
    xgb_model.fit(X, y)
    
    trainer_xgb = CreditRiskTrainer()
    trainer_xgb.model = xgb_model
    trainer_xgb.analyze_feature_importance(X, top_n=10, dominance_threshold=0.40)
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("FEATURE IMPORTANCE DIAGNOSTICS - COMPREHENSIVE TESTS")
    print("=" * 70 + "\n")
    
    test_feature_importance_normal()
    test_feature_dominance()
    test_xgboost_importance()
    test_feature_mismatch()
    compare_models()
    
    print("=" * 70)
    print("✓ ALL TESTS COMPLETE")
    print("=" * 70)
