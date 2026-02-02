"""Test threshold optimization functionality.

This script demonstrates the threshold optimization feature that replaces
the fixed 0.5 cutoff with an optimized threshold based on F1-score and recall constraints.
"""

import numpy as np
from src.train import CreditRiskTrainer

def test_threshold_optimization():
    """Test the threshold optimization logic with synthetic data."""
    
    trainer = CreditRiskTrainer()
    
    # Test Case 1: Perfect separation (easy case)
    print("=" * 70)
    print("TEST CASE 1: Perfect Separation")
    print("=" * 70)
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y_pred_proba = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])
    
    threshold, justification = trainer.optimize_threshold(y_true, y_pred_proba, min_recall=0.35)
    print(f"Optimal Threshold: {threshold:.2f}")
    print(f"Justification: {justification}")
    print()
    
    # Test Case 2: Difficult case with overlap
    print("=" * 70)
    print("TEST CASE 2: Overlapping Distributions")
    print("=" * 70)
    y_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    y_pred_proba = np.array([0.3, 0.4, 0.5, 0.6, 0.7, 0.3, 0.4, 0.5, 0.6, 0.7])
    
    threshold, justification = trainer.optimize_threshold(y_true, y_pred_proba, min_recall=0.35)
    print(f"Optimal Threshold: {threshold:.2f}")
    print(f"Justification: {justification}")
    print()
    
    # Test Case 3: High recall requirement
    print("=" * 70)
    print("TEST CASE 3: High Recall Requirement (min_recall=0.80)")
    print("=" * 70)
    y_true = np.array([0] * 90 + [1] * 10)  # 10% positive class
    y_pred_proba = np.concatenate([
        np.random.uniform(0.2, 0.6, 90),  # Negative class
        np.random.uniform(0.4, 0.8, 10),  # Positive class
    ])
    
    threshold, justification = trainer.optimize_threshold(y_true, y_pred_proba, min_recall=0.80)
    print(f"Optimal Threshold: {threshold:.2f}")
    print(f"Justification: {justification}")
    print()
    
    # Test Case 4: Standard credit risk scenario
    print("=" * 70)
    print("TEST CASE 4: Realistic Credit Risk Scenario (87/13 split)")
    print("=" * 70)
    np.random.seed(42)
    y_true = np.array([0] * 87 + [1] * 13)  # Realistic 13% default rate
    y_pred_proba = np.concatenate([
        np.random.beta(2, 5, 87),  # Negative class (skewed low)
        np.random.beta(5, 2, 13),  # Positive class (skewed high)
    ])
    
    threshold, justification = trainer.optimize_threshold(y_true, y_pred_proba, min_recall=0.35)
    print(f"Optimal Threshold: {threshold:.2f}")
    print(f"Justification: {justification}")
    print()
    
    # Verify threshold is applied correctly
    print("=" * 70)
    print("VERIFICATION: Threshold Application")
    print("=" * 70)
    y_pred_05 = (y_pred_proba >= 0.5).astype(int)
    y_pred_opt = (y_pred_proba >= threshold).astype(int)
    
    from sklearn.metrics import f1_score, recall_score, precision_score
    
    f1_05 = f1_score(y_true, y_pred_05)
    recall_05 = recall_score(y_true, y_pred_05)
    precision_05 = precision_score(y_true, y_pred_05)
    
    f1_opt = f1_score(y_true, y_pred_opt)
    recall_opt = recall_score(y_true, y_pred_opt)
    precision_opt = precision_score(y_true, y_pred_opt)
    
    print(f"Fixed Threshold (0.50):")
    print(f"  F1={f1_05:.4f}, Recall={recall_05:.4f}, Precision={precision_05:.4f}")
    print()
    print(f"Optimized Threshold ({threshold:.2f}):")
    print(f"  F1={f1_opt:.4f}, Recall={recall_opt:.4f}, Precision={precision_opt:.4f}")
    print()
    print(f"Improvement:")
    print(f"  ΔF1={f1_opt-f1_05:+.4f}, ΔRecall={recall_opt-recall_05:+.4f}, ΔPrecision={precision_opt-precision_05:+.4f}")
    print()
    print("✓ Threshold optimization complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_threshold_optimization()
