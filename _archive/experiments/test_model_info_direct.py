"""Test /model-info endpoint directly (without HTTP server).

Tests the model_info endpoint function directly.
"""

import sys
from pathlib import Path
import asyncio

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.api.v1.model_info import get_model_info

print("\n" + "=" * 70)
print("MODEL INFO ENDPOINT FUNCTION TEST")
print("=" * 70)

async def test_get_model_info_function():
    """Test get_model_info() function directly."""
    print("\n" + "=" * 70)
    print("TEST: get_model_info() Function")
    print("=" * 70)
    
    try:
        # Call function directly (await since it's async)
        result = await get_model_info()
        
        print("\n✓ Function executed successfully")
        print("\nResponse Data:")
        print(f"  Model type: {result.get('model_type', 'N/A')}")
        print(f"  Model name: {result.get('model_name', 'N/A')}")
        print(f"  Training timestamp: {result.get('training_timestamp', 'N/A')}")
        print(f"  Feature count: {result.get('feature_count', 0)}")
        print(f"  Schema version: {result.get('schema_version', 'N/A')}")
        print(f"  API version: {result.get('api_version', 'N/A')}")
        print(f"  Engine: {result.get('engine', 'N/A')}")
        print(f"  Is loaded: {result.get('is_loaded', False)}")
        
        # Check evaluation metrics
        metrics = result.get('evaluation_metrics', {})
        if metrics:
            print("\n  Evaluation Metrics:")
            print(f"    ROC-AUC: {metrics.get('roc_auc', 0):.4f}")
            print(f"    PR-AUC: {metrics.get('pr_auc', 0):.4f}")
            print(f"    Recall: {metrics.get('recall', 0):.4f}")
            print(f"    Precision: {metrics.get('precision', 0):.4f}")
            print(f"    F1-Score: {metrics.get('f1_score', 0):.4f}")
            print(f"    Accuracy: {metrics.get('accuracy', 0):.4f}")
        
        # Verify required fields
        required = ['model_type', 'model_name', 'training_timestamp', 
                   'feature_count', 'schema_version', 'is_loaded', 'engine', 'api_version']
        missing = [f for f in required if f not in result]
        
        if missing:
            print(f"\n✗ Missing required fields: {missing}")
            return False
        
        # Verify no sensitive data
        sensitive = ['training_data', 'X_train', 'y_train', 'model_weights', 
                    'feature_names', 'coef_', 'feature_importances_', 'tree_']
        found_sensitive = [f for f in sensitive if f in result]
        
        if found_sensitive:
            print(f"\n✗ SECURITY ISSUE: Sensitive data exposed: {found_sensitive}")
            return False
        
        print("\n✓ All required fields present")
        print("✓ No sensitive data exposed")
        
        # Check response structure
        expected_types = {
            'model_type': str,
            'model_name': str,
            'training_timestamp': str,
            'feature_count': int,
            'schema_version': str,
            'api_version': str,
            'is_loaded': bool,
            'engine': str,
            'evaluation_metrics': dict,
        }
        
        type_errors = []
        for field, expected_type in expected_types.items():
            if field in result and not isinstance(result[field], expected_type):
                type_errors.append(f"{field} (expected {expected_type.__name__}, got {type(result[field]).__name__})")
        
        if type_errors:
            print(f"\n✗ Type errors: {type_errors}")
            return False
        
        print("✓ All field types correct")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Function failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    results = []
    
    # Run test (use asyncio.run for async function)
    passed = asyncio.run(test_get_model_info_function())
    results.append(("Model Info Function", passed))
    
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
        print("\n🎉 Model info endpoint function is production-ready!")
        print("\nTo test the HTTP endpoint, start the server:")
        print("  uvicorn app.main:app --reload")
        print("\nThen call:")
        print("  curl http://localhost:8000/api/v1/model-info")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        sys.exit(1)
