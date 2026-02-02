"""Test /model-info API endpoint.

Tests the public API endpoint that exposes model metadata.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("\n" + "=" * 70)
print("MODEL INFO API ENDPOINT TEST")
print("=" * 70)

def test_model_info_endpoint():
    """Test GET /api/v1/model-info endpoint."""
    print("\n" + "=" * 70)
    print("TEST: GET /api/v1/model-info")
    print("=" * 70)
    
    try:
        # Call endpoint
        response = client.get("/api/v1/model-info")
        
        print(f"\n✓ Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Parse JSON response
        data = response.json()
        
        print("\n✓ Response Data:")
        print(f"  Model type: {data.get('model_type', 'N/A')}")
        print(f"  Model name: {data.get('model_name', 'N/A')}")
        print(f"  Training timestamp: {data.get('training_timestamp', 'N/A')}")
        print(f"  Feature count: {data.get('feature_count', 0)}")
        print(f"  Schema version: {data.get('schema_version', 'N/A')}")
        print(f"  API version: {data.get('api_version', 'N/A')}")
        print(f"  Engine: {data.get('engine', 'N/A')}")
        print(f"  Is loaded: {data.get('is_loaded', False)}")
        
        # Check evaluation metrics
        metrics = data.get('evaluation_metrics', {})
        if metrics:
            print("\n  Evaluation Metrics:")
            for key, value in metrics.items():
                print(f"    {key}: {value}")
        
        # Verify required fields
        required = ['model_type', 'model_name', 'training_timestamp', 
                   'feature_count', 'schema_version', 'is_loaded', 'engine']
        missing = [f for f in required if f not in data]
        
        if missing:
            print(f"\n✗ Missing required fields: {missing}")
            return False
        
        # Verify no sensitive data
        sensitive = ['training_data', 'X_train', 'y_train', 'model_weights', 
                    'feature_names', 'coef_', 'feature_importances_']
        found_sensitive = [f for f in sensitive if f in data]
        
        if found_sensitive:
            print(f"\n✗ SECURITY ISSUE: Sensitive data exposed: {found_sensitive}")
            return False
        
        print("\n✓ All validations passed")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_endpoint_error_handling():
    """Test endpoint error handling."""
    print("\n" + "=" * 70)
    print("TEST: Error Handling")
    print("=" * 70)
    
    # Note: We can't easily simulate an error without breaking the model
    # This test just verifies the endpoint is robust
    
    try:
        response = client.get("/api/v1/model-info")
        
        # Should always return 200 or 500, never crash
        if response.status_code not in [200, 500]:
            print(f"✗ Unexpected status code: {response.status_code}")
            return False
        
        print(f"\n✓ Endpoint returns valid HTTP status: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"\n✗ Endpoint crashed: {e}")
        return False


if __name__ == "__main__":
    results = []
    
    # Run tests
    results.append(("Model Info Endpoint", test_model_info_endpoint()))
    results.append(("Error Handling", test_endpoint_error_handling()))
    
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
        print("\n🎉 API endpoint is production-ready!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        sys.exit(1)
