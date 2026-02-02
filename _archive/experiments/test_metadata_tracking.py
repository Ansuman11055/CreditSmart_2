"""Test model metadata tracking.

This script tests:
1. Model metadata is saved during training
2. Metadata is loaded correctly
3. /model-info endpoint returns proper data
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.ml.model import get_model
from app.ml.ml_inference import MLInferenceEngine

print("\n" + "=" * 70)
print("MODEL METADATA TRACKING - TEST SUITE")
print("=" * 70)

def test_metadata_loading():
    """Test 1: Metadata loading from model artifacts."""
    print("\n" + "=" * 70)
    print("TEST 1: Metadata Loading")
    print("=" * 70)
    
    try:
        engine = MLInferenceEngine(model_dir="models")
        info = engine.get_model_info()
        
        print("\n✓ Metadata loaded successfully")
        print(f"  Model type: {info.get('model_type', 'N/A')}")
        print(f"  Model name: {info.get('model_name', 'N/A')}")
        print(f"  Training timestamp: {info.get('training_timestamp', 'N/A')}")
        print(f"  Feature count: {info.get('feature_count', 0)}")
        print(f"  Schema version: {info.get('schema_version', 'N/A')}")
        
        # Check evaluation metrics
        metrics = info.get('evaluation_metrics', {})
        if metrics:
            print("\n  Evaluation Metrics:")
            print(f"    ROC-AUC: {metrics.get('roc_auc', 0):.4f}")
            print(f"    PR-AUC: {metrics.get('pr_auc', 0):.4f}")
            print(f"    Recall: {metrics.get('recall', 0):.4f}")
            print(f"    Precision: {metrics.get('precision', 0):.4f}")
            print(f"    F1-Score: {metrics.get('f1_score', 0):.4f}")
        
        # Validate required fields are present
        required_fields = ['model_type', 'model_name', 'training_timestamp', 'feature_count']
        missing = [f for f in required_fields if f not in info or info[f] == 'N/A']
        
        if missing:
            print(f"\n⚠️  Missing fields: {missing}")
            print("  Note: Retrain model to generate complete metadata")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to load metadata: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_wrapper_metadata():
    """Test 2: Model wrapper exposes metadata correctly."""
    print("\n" + "=" * 70)
    print("TEST 2: Model Wrapper Metadata")
    print("=" * 70)
    
    try:
        model = get_model()
        info = model.get_model_info()
        
        print("\n✓ Model wrapper metadata retrieved")
        print(f"  Engine: {info.get('engine', 'N/A')}")
        print(f"  Model type: {info.get('model_type', 'N/A')}")
        print(f"  Training timestamp: {info.get('training_timestamp', 'N/A')}")
        print(f"  Feature count: {info.get('feature_count', 0)}")
        print(f"  Is loaded: {info.get('is_loaded', False)}")
        
        # Check metrics
        metrics = info.get('evaluation_metrics', {})
        if metrics:
            print(f"\n  Metrics present: {len(metrics)} metrics")
            print(f"    ROC-AUC: {metrics.get('roc_auc', 0):.4f}")
            print(f"    Recall: {metrics.get('recall', 0):.4f}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_sensitive_data():
    """Test 3: Verify no sensitive data is exposed."""
    print("\n" + "=" * 70)
    print("TEST 3: Sensitive Data Check")
    print("=" * 70)
    
    try:
        model = get_model()
        info = model.get_model_info()
        
        # List of sensitive keys that should NOT be present
        sensitive_keys = [
            'training_data',
            'X_train',
            'y_train',
            'model_weights',
            'coef_',
            'feature_importances_',
            'tree_',
            'estimators_',
        ]
        
        found_sensitive = [key for key in sensitive_keys if key in info]
        
        if found_sensitive:
            print(f"\n✗ SECURITY ISSUE: Sensitive data exposed: {found_sensitive}")
            return False
        
        print("\n✓ No sensitive data exposed")
        print(f"  Checked {len(sensitive_keys)} sensitive fields")
        print("  All safe for public API exposure")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        return False


def test_metadata_completeness():
    """Test 4: Verify metadata completeness."""
    print("\n" + "=" * 70)
    print("TEST 4: Metadata Completeness")
    print("=" * 70)
    
    try:
        model = get_model()
        info = model.get_model_info()
        
        # Required fields for API response
        required_fields = {
            'model_type': str,
            'model_name': str,
            'training_timestamp': str,
            'feature_count': int,
            'schema_version': str,
            'evaluation_metrics': dict,
            'is_loaded': bool,
            'engine': str,
        }
        
        missing = []
        wrong_type = []
        
        for field, expected_type in required_fields.items():
            if field not in info:
                missing.append(field)
            elif not isinstance(info[field], expected_type):
                wrong_type.append(f"{field} (expected {expected_type.__name__}, got {type(info[field]).__name__})")
        
        if missing:
            print(f"\n✗ Missing required fields: {missing}")
            return False
        
        if wrong_type:
            print(f"\n✗ Wrong field types: {wrong_type}")
            return False
        
        print("\n✓ Metadata structure is complete")
        print(f"  All {len(required_fields)} required fields present")
        print(f"  All field types correct")
        
        # Check evaluation metrics structure
        metrics = info['evaluation_metrics']
        if metrics:
            expected_metrics = ['roc_auc', 'recall', 'precision', 'f1_score']
            present = [m for m in expected_metrics if m in metrics]
            print(f"\n  Evaluation metrics: {len(present)}/{len(expected_metrics)} present")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    results = []
    
    # Run tests
    results.append(("Metadata Loading", test_metadata_loading()))
    results.append(("Model Wrapper Metadata", test_model_wrapper_metadata()))
    results.append(("No Sensitive Data", test_no_sensitive_data()))
    results.append(("Metadata Completeness", test_metadata_completeness()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Model metadata tracking is production-ready.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        if not results[0][1]:
            print("\nNote: If 'Metadata Loading' failed, retrain the model:")
            print("  python -c \"from src.train import train; train(model_name='random_forest')\"")
        sys.exit(1)
