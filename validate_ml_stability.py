"""Quick validation script for ML inference stability enhancements."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.startup_safety import verify_model_artifacts, verify_model_metadata


def test_artifact_verification():
    """Test artifact verification function."""
    print("=" * 70)
    print("Testing Artifact Verification")
    print("=" * 70)
    
    artifacts_ok, missing_files = verify_model_artifacts("models")
    
    print(f"\n✓ Artifact Check Status: {'PASS' if artifacts_ok else 'FAIL'}")
    
    if missing_files:
        print(f"  Missing Files: {', '.join(missing_files)}")
    else:
        print("  All required artifacts present")
    
    return artifacts_ok


def test_metadata_verification():
    """Test metadata verification function."""
    print("\n" + "=" * 70)
    print("Testing Metadata Verification")
    print("=" * 70)
    
    metadata_ok, metadata = verify_model_metadata("models")
    
    print(f"\n✓ Metadata Check Status: {'PASS' if metadata_ok else 'FAIL'}")
    
    if metadata:
        print(f"  Model Name: {metadata.get('model_name', 'unknown')}")
        print(f"  Model Type: {metadata.get('model_class', 'unknown')}")
        print(f"  Training Timestamp: {metadata.get('training_timestamp', 'unknown')}")
        print(f"  Feature Count: {len(metadata.get('feature_names', []))}")
        print(f"  Schema Version: {metadata.get('schema_version', 'unknown')}")
    else:
        print("  No metadata available")
    
    return metadata_ok


def test_startup_checks():
    """Test complete startup checks."""
    print("\n" + "=" * 70)
    print("Testing Complete Startup Checks")
    print("=" * 70)
    
    from app.core.startup_safety import perform_startup_checks, get_startup_status
    from app.core.logging_config import configure_logging
    
    # Configure logging first
    configure_logging()
    
    print("\nRunning startup checks...")
    startup_status = perform_startup_checks()
    
    print(f"\n✓ Startup Status:")
    print(f"  Healthy: {startup_status.is_healthy}")
    print(f"  Degraded: {startup_status.is_degraded}")
    print(f"  Model Loaded: {startup_status.model_loaded}")
    print(f"  SHAP Available: {startup_status.shap_available}")
    print(f"  Startup Time: {startup_status.startup_time_ms:.2f}ms")
    
    if startup_status.errors:
        print(f"\n  Errors ({len(startup_status.errors)}):")
        for error in startup_status.errors:
            print(f"    - [{error.severity}] {error.component}: {error.error}")
    else:
        print("  No errors")
    
    return startup_status


def test_model_singleton():
    """Test model singleton behavior."""
    print("\n" + "=" * 70)
    print("Testing Model Singleton Pattern")
    print("=" * 70)
    
    from app.ml.model import get_model
    
    try:
        model1 = get_model()
        model2 = get_model()
        
        is_singleton = model1 is model2
        
        print(f"\n✓ Singleton Test: {'PASS' if is_singleton else 'FAIL'}")
        print(f"  Model 1 ID: {id(model1)}")
        print(f"  Model 2 ID: {id(model2)}")
        print(f"  Same Instance: {is_singleton}")
        
        # Get model info
        model_info = model1.get_model_info()
        print(f"\n  Model Info:")
        print(f"    Engine: {model_info.get('engine')}")
        print(f"    Type: {model_info.get('model_type')}")
        print(f"    Version: {model_info.get('model_version')}")
        print(f"    Training Timestamp: {model_info.get('training_timestamp')}")
        print(f"    Loaded: {model_info.get('is_loaded')}")
        
        return is_singleton
        
    except Exception as e:
        print(f"\n✗ Singleton Test: FAIL")
        print(f"  Error: {e}")
        return False


def main():
    """Run all validation tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "ML INFERENCE STABILITY VALIDATION" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    results = {
        "artifacts": test_artifact_verification(),
        "metadata": test_metadata_verification(),
        "startup": test_startup_checks(),
        "singleton": test_model_singleton(),
    }
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    all_passed = all(results.values())
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test_name.title():20} {status}")
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("✓ ALL TESTS PASSED - ML inference stability is ready for production")
    else:
        print("✗ SOME TESTS FAILED - Review errors above")
    
    print("=" * 70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
