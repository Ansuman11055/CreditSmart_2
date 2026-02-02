"""Test script for the new /api/v1/system/info endpoint."""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from app.main import app

# Create test client
client = TestClient(app)


def test_system_info_endpoint():
    """Test the /api/v1/system/info endpoint."""
    print("=" * 70)
    print("Testing /api/v1/system/info Endpoint")
    print("=" * 70)
    
    response = client.get("/api/v1/system/info")
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n✓ Response Structure:")
        print(json.dumps(data, indent=2))
        
        # Validate key fields
        print("\n✓ Key Fields Validation:")
        assert "service_name" in data, "Missing service_name"
        print(f"  Service Name: {data['service_name']}")
        
        assert "api_version" in data, "Missing api_version"
        print(f"  API Version: {data['api_version']}")
        
        assert "model" in data, "Missing model section"
        model = data["model"]
        print(f"  Model Name: {model.get('model_name')}")
        print(f"  Model Type: {model.get('model_type')}")
        print(f"  Model Version: {model.get('model_version')}")
        print(f"  Training Timestamp: {model.get('training_timestamp')}")
        print(f"  Engine: {model.get('engine')}")
        print(f"  Loaded: {model.get('is_loaded')}")
        
        assert "artifacts" in data, "Missing artifacts section"
        artifacts = data["artifacts"]
        print(f"\n  Artifacts:")
        print(f"    model.joblib: {artifacts.get('model_file_present')}")
        print(f"    preprocessor.joblib: {artifacts.get('preprocessor_present')}")
        print(f"    SHAP explainer: {artifacts.get('shap_explainer_present')}")
        
        assert "startup" in data, "Missing startup section"
        startup = data["startup"]
        print(f"\n  Startup Status:")
        print(f"    Healthy: {startup.get('healthy')}")
        print(f"    Degraded: {startup.get('degraded')}")
        print(f"    Errors: {len(startup.get('errors', []))}")
        
        print("\n✓ ALL VALIDATIONS PASSED")
        return True
    else:
        print(f"\n✗ Unexpected status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def test_health_endpoint():
    """Test that health endpoint still works."""
    print("\n" + "=" * 70)
    print("Testing /api/v1/health Endpoint (Backward Compatibility)")
    print("=" * 70)
    
    response = client.get("/api/v1/health")
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Service Status: {data.get('service_status')}")
        print(f"Model Loaded: {data.get('model_loaded')}")
        print("\n✓ Health endpoint working")
        return True
    else:
        print(f"\n✗ Health endpoint failed")
        return False


def main():
    """Run all endpoint tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "SYSTEM INFO ENDPOINT TESTING" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    results = {
        "system_info": test_system_info_endpoint(),
        "health": test_health_endpoint(),
    }
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name:20} {status}")
    
    print("=" * 70 + "\n")
    
    if all(results.values()):
        print("✓ ALL ENDPOINT TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
