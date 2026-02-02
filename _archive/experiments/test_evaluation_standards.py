"""Test script to demonstrate industry credit risk evaluation standards.

This script shows how the evaluation logic handles different recall scenarios:
1. Good recall (>= 0.5)
2. Acceptable recall (0.3 - 0.5)
3. Critical recall (< 0.3) with warnings
"""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    classification_report,
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def evaluate_with_industry_standards(y_true, y_pred, y_pred_proba, scenario_name):
    """Evaluate predictions using industry credit risk standards.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_pred_proba: Predicted probabilities
        scenario_name: Name of the scenario for logging
    """
    # Calculate metrics (industry credit risk standards)
    metrics = {
        "roc_auc": roc_auc_score(y_true, y_pred_proba),
        "pr_auc": average_precision_score(y_true, y_pred_proba),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
        "accuracy": accuracy_score(y_true, y_pred),
    }
    
    # Log metrics (industry credit risk evaluation standards)
    logger.info(f"\n{'='*70}")
    logger.info(f"{scenario_name}")
    logger.info(f"{'='*70}")
    logger.info("\n📊 PRIMARY METRIC (Industry Standard for Credit Risk):")
    logger.info(f"   ROC-AUC:  {metrics['roc_auc']:.4f}  ← Discrimination ability across all thresholds")
    
    logger.info("\n📈 SECONDARY METRICS (Critical for Imbalanced Data):")
    logger.info(f"   PR-AUC:   {metrics['pr_auc']:.4f}  ← Precision-Recall trade-off (robust to class imbalance)")
    
    # Recall with threshold warning
    recall_value = metrics['recall']
    recall_status = "⚠️  WARNING: CRITICALLY LOW" if recall_value < 0.3 else "✓ Acceptable" if recall_value < 0.5 else "✓ Good"
    logger.info(f"   Recall:   {recall_value:.4f}  ← Default detection rate at 0.5 threshold  [{recall_status}]")
    
    if recall_value < 0.3:
        logger.warning("\n" + "!"*70)
        logger.warning("⚠️  CRITICAL: Recall below 0.30 threshold!")
        logger.warning(f"   Current recall: {recall_value:.1%} of defaults are being detected")
        logger.warning("   Risk: Missing {:.1%} of actual defaults may result in significant losses".format(1 - recall_value))
        logger.warning("   Recommendation: Adjust decision threshold or retrain with cost-sensitive learning")
        logger.warning("!"*70 + "\n")
    
    logger.info("\n📉 SUPPORTING METRICS:")
    logger.info(f"   Precision: {metrics['precision']:.4f}  ← Positive predictive value")
    logger.info(f"   F1 Score:  {metrics['f1_score']:.4f}  ← Harmonic mean of precision & recall")
    logger.info(f"   Accuracy:  {metrics['accuracy']:.4f}  (⚠️  Not recommended for imbalanced credit data)")
    
    return metrics


def main():
    """Run evaluation scenarios with different recall values."""
    
    # Generate synthetic imbalanced data (similar to real credit data)
    np.random.seed(42)
    n_samples = 1000
    n_defaults = 128  # ~12.8% default rate (similar to our real data)
    
    # True labels
    y_true = np.array([0] * (n_samples - n_defaults) + [1] * n_defaults)
    np.random.shuffle(y_true)
    
    # Scenario 1: Good recall (0.55)
    logger.info("\n\n" + "="*70)
    logger.info("SCENARIO 1: GOOD MODEL (Similar to our production model)")
    logger.info("="*70)
    y_pred_1 = y_true.copy()
    # Make model miss 45% of defaults
    default_indices = np.where(y_true == 1)[0]
    miss_indices = np.random.choice(default_indices, size=int(0.45 * len(default_indices)), replace=False)
    y_pred_1[miss_indices] = 0
    y_pred_proba_1 = np.random.beta(2, 5, n_samples)  # Realistic probability distribution
    
    evaluate_with_industry_standards(y_true, y_pred_1, y_pred_proba_1, "Good Model Evaluation")
    
    # Scenario 2: Acceptable recall (0.35)
    logger.info("\n\n" + "="*70)
    logger.info("SCENARIO 2: ACCEPTABLE MODEL (Marginal performance)")
    logger.info("="*70)
    y_pred_2 = y_true.copy()
    # Make model miss 65% of defaults
    miss_indices = np.random.choice(default_indices, size=int(0.65 * len(default_indices)), replace=False)
    y_pred_2[miss_indices] = 0
    y_pred_proba_2 = np.random.beta(1.5, 5, n_samples)
    
    evaluate_with_industry_standards(y_true, y_pred_2, y_pred_proba_2, "Acceptable Model Evaluation")
    
    # Scenario 3: Critical recall (0.15) - triggers warning
    logger.info("\n\n" + "="*70)
    logger.info("SCENARIO 3: POOR MODEL (Critically low recall - WARNING EXPECTED)")
    logger.info("="*70)
    y_pred_3 = y_true.copy()
    # Make model miss 85% of defaults
    miss_indices = np.random.choice(default_indices, size=int(0.85 * len(default_indices)), replace=False)
    y_pred_3[miss_indices] = 0
    y_pred_proba_3 = np.random.beta(1, 5, n_samples)
    
    evaluate_with_industry_standards(y_true, y_pred_3, y_pred_proba_3, "Poor Model Evaluation (Critical Recall)")
    
    logger.info("\n\n" + "="*70)
    logger.info("✓ Demonstration Complete!")
    logger.info("="*70)
    logger.info("\nKey Takeaways:")
    logger.info("  1. ROC-AUC is the PRIMARY metric for credit risk (industry standard)")
    logger.info("  2. PR-AUC provides robust evaluation for imbalanced data")
    logger.info("  3. Recall < 0.3 triggers CRITICAL warnings (missing too many defaults)")
    logger.info("  4. Accuracy is de-emphasized (can be misleading with class imbalance)")
    logger.info("="*70)


if __name__ == "__main__":
    main()
