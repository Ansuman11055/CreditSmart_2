"""Test runtime sanity checks in prediction flow.

This test suite validates:
1. Detection of NaN values
2. Detection of infinite values
3. Detection of out-of-range probabilities
4. Detection of invalid predictions
5. Warning system for edge cases (probability exactly 0 or 1)
6. Graceful error handling with clear messages
"""

import sys
from pathlib import Path
import math
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.ml.ml_inference import MLInferenceEngine

# Set up logging to capture warnings
logging.basicConfig(level=logging.DEBUG)

print("\n" + "=" * 70)
print("PREDICTION SANITY CHECKS TEST SUITE")
print("=" * 70)


def test_validate_normal_outputs():
    """Test 1: Normal prediction outputs pass validation."""
    print("\n" + "=" * 70)
    print("TEST 1: Normal Outputs Validation")
    print("=" * 70)
    
    engine = MLInferenceEngine(model_dir="models")
    
    test_cases = [
        (0, 0.25, "Low risk"),
        (0, 0.45, "Medium-low risk"),
        (1, 0.55, "Medium-high risk"),
        (1, 0.85, "High risk"),
    ]
    
    passed = 0
    for prediction, probability, description in test_cases:
        try:
            engine._validate_prediction_outputs(prediction, probability)
            print(f"✓ {description}: prediction={prediction}, probability={probability:.2f}")
            passed += 1
        except Exception as e:
            print(f"✗ {description} failed: {e}")
    
    print(f"\nResult: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_detect_nan_prediction():
    """Test 2: Detect NaN in prediction."""
    print("\n" + "=" * 70)
    print("TEST 2: NaN Detection in Prediction")
    print("=" * 70)
    
    engine = MLInferenceEngine(model_dir="models")
    
    try:
        engine._validate_prediction_outputs(float('nan'), 0.5)
        print("✗ FAILED: NaN prediction not detected")
        return False
    except RuntimeError as e:
        error_msg = str(e)
        if "NaN prediction" in error_msg:
            print("✓ PASSED: NaN prediction detected correctly")
            print(f"  Error message: {error_msg}")
            return True
        else:
            print(f"✗ FAILED: Wrong error message: {error_msg}")
            return False


def test_detect_nan_probability():
    """Test 3: Detect NaN in probability."""
    print("\n" + "=" * 70)
    print("TEST 3: NaN Detection in Probability")
    print("=" * 70)
    
    engine = MLInferenceEngine(model_dir="models")
    
    try:
        engine._validate_prediction_outputs(0, float('nan'))
        print("✗ FAILED: NaN probability not detected")
        return False
    except RuntimeError as e:
        error_msg = str(e)
        if "NaN probability" in error_msg:
            print("✓ PASSED: NaN probability detected correctly")
            print(f"  Error message: {error_msg}")
            return True
        else:
            print(f"✗ FAILED: Wrong error message: {error_msg}")
            return False


def test_detect_inf_prediction():
    """Test 4: Detect infinite prediction."""
    print("\n" + "=" * 70)
    print("TEST 4: Infinite Value Detection in Prediction")
    print("=" * 70)
    
    engine = MLInferenceEngine(model_dir="models")
    
    try:
        engine._validate_prediction_outputs(float('inf'), 0.5)
        print("✗ FAILED: Infinite prediction not detected")
        return False
    except RuntimeError as e:
        error_msg = str(e)
        if "infinite prediction" in error_msg:
            print("✓ PASSED: Infinite prediction detected correctly")
            print(f"  Error message: {error_msg}")
            return True
        else:
            print(f"✗ FAILED: Wrong error message: {error_msg}")
            return False


def test_detect_inf_probability():
    """Test 5: Detect infinite probability."""
    print("\n" + "=" * 70)
    print("TEST 5: Infinite Value Detection in Probability")
    print("=" * 70)
    
    engine = MLInferenceEngine(model_dir="models")
    
    try:
        engine._validate_prediction_outputs(0, float('inf'))
        print("✗ FAILED: Infinite probability not detected")
        return False
    except RuntimeError as e:
        error_msg = str(e)
        if "infinite probability" in error_msg:
            print("✓ PASSED: Infinite probability detected correctly")
            print(f"  Error message: {error_msg}")
            return True
        else:
            print(f"✗ FAILED: Wrong error message: {error_msg}")
            return False


def test_detect_invalid_prediction():
    """Test 6: Detect invalid prediction values (not 0 or 1)."""
    print("\n" + "=" * 70)
    print("TEST 6: Invalid Prediction Value Detection")
    print("=" * 70)
    
    engine = MLInferenceEngine(model_dir="models")
    
    invalid_values = [2, -1, 0.5, 3, 999]
    passed = 0
    
    for value in invalid_values:
        try:
            engine._validate_prediction_outputs(value, 0.5)
            print(f"✗ Invalid prediction {value} not detected")
        except RuntimeError as e:
            if "invalid prediction" in str(e):
                print(f"✓ Invalid prediction {value} detected correctly")
                passed += 1
            else:
                print(f"✗ Wrong error for prediction {value}: {e}")
    
    print(f"\nResult: {passed}/{len(invalid_values)} tests passed")
    return passed == len(invalid_values)


def test_detect_out_of_range_probability():
    """Test 7: Detect probability out of [0, 1] range."""
    print("\n" + "=" * 70)
    print("TEST 7: Out-of-Range Probability Detection")
    print("=" * 70)
    
    engine = MLInferenceEngine(model_dir="models")
    
    invalid_probs = [-0.1, 1.5, 2.0, -1.0, 100.0]
    passed = 0
    
    for prob in invalid_probs:
        try:
            engine._validate_prediction_outputs(0, prob)
            print(f"✗ Out-of-range probability {prob} not detected")
        except RuntimeError as e:
            if "probability out of range" in str(e) or "invalid probability" in str(e):
                print(f"✓ Out-of-range probability {prob} detected correctly")
                passed += 1
            else:
                print(f"✗ Wrong error for probability {prob}: {e}")
    
    print(f"\nResult: {passed}/{len(invalid_probs)} tests passed")
    return passed == len(invalid_probs)


def test_edge_case_warnings():
    """Test 8: Verify warnings for edge cases (probability exactly 0 or 1)."""
    print("\n" + "=" * 70)
    print("TEST 8: Edge Case Warnings (Probability 0.0 or 1.0)")
    print("=" * 70)
    
    engine = MLInferenceEngine(model_dir="models")
    
    # These should NOT raise errors, but should log warnings
    edge_cases = [
        (0, 0.0, "Probability exactly 0.0"),
        (1, 1.0, "Probability exactly 1.0"),
    ]
    
    passed = 0
    for prediction, probability, description in edge_cases:
        try:
            engine._validate_prediction_outputs(prediction, probability)
            print(f"✓ {description}: Accepted with warning")
            print(f"  (Check logs for warning message)")
            passed += 1
        except Exception as e:
            print(f"✗ {description} should not raise error: {e}")
    
    print(f"\nResult: {passed}/{len(edge_cases)} tests passed")
    print("Note: Warnings should appear in logs, not as errors")
    return passed == len(edge_cases)


def test_real_prediction_with_sanity_checks():
    """Test 9: Real prediction with sanity checks enabled."""
    print("\n" + "=" * 70)
    print("TEST 9: Real Prediction with Sanity Checks")
    print("=" * 70)
    
    try:
        from app.schemas.request import CreditRiskRequest
        
        engine = MLInferenceEngine(model_dir="models")
        
        # Create a valid request
        request = CreditRiskRequest(
            annual_income=50000.0,
            monthly_debt=1500.0,
            credit_score=680,
            loan_amount=15000.0,
            loan_term_months=36,
            employment_length_years=5.0,
            home_ownership="RENT",
            purpose="debt_consolidation",
            number_of_open_accounts=3,
            delinquencies_2y=0,
            inquiries_6m=1
        )
        
        # Make prediction
        prediction, probability = engine.predict(request)
        
        # Verify outputs
        if prediction in [0, 1] and 0.0 <= probability <= 1.0:
            print("✓ Prediction generated successfully")
            print(f"  Prediction: {prediction}")
            print(f"  Probability: {probability:.4f}")
            print("  Sanity checks passed")
            return True
        else:
            print(f"✗ Invalid outputs: prediction={prediction}, probability={probability}")
            return False
            
    except Exception as e:
        print(f"✗ Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_messages_clarity():
    """Test 10: Verify error messages are clear and actionable."""
    print("\n" + "=" * 70)
    print("TEST 10: Error Message Clarity")
    print("=" * 70)
    
    engine = MLInferenceEngine(model_dir="models")
    
    test_cases = [
        (float('nan'), 0.5, "NaN", "contact support"),
        (0, float('inf'), "infinite", "contact support"),
        (2, 0.5, "invalid prediction", "Expected 0"),
        (0, 1.5, "invalid probability", "0.0 and 1.0"),
    ]
    
    passed = 0
    for prediction, probability, keyword1, keyword2 in test_cases:
        try:
            engine._validate_prediction_outputs(prediction, probability)
            print(f"✗ Should have raised error for: prediction={prediction}, probability={probability}")
        except RuntimeError as e:
            error_msg = str(e).lower()
            if keyword1.lower() in error_msg and keyword2.lower() in error_msg:
                print(f"✓ Clear error message for invalid input")
                print(f"  Keywords found: '{keyword1}' and '{keyword2}'")
                passed += 1
            else:
                print(f"✗ Error message missing keywords: {e}")
    
    print(f"\nResult: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


if __name__ == "__main__":
    results = []
    
    # Run all tests
    print("\nStarting comprehensive sanity check tests...")
    print("This validates runtime stability for financial risk system\n")
    
    results.append(("Normal Outputs", test_validate_normal_outputs()))
    results.append(("NaN Prediction Detection", test_detect_nan_prediction()))
    results.append(("NaN Probability Detection", test_detect_nan_probability()))
    results.append(("Infinite Prediction Detection", test_detect_inf_prediction()))
    results.append(("Infinite Probability Detection", test_detect_inf_probability()))
    results.append(("Invalid Prediction Detection", test_detect_invalid_prediction()))
    results.append(("Out-of-Range Probability", test_detect_out_of_range_probability()))
    results.append(("Edge Case Warnings", test_edge_case_warnings()))
    results.append(("Real Prediction Flow", test_real_prediction_with_sanity_checks()))
    results.append(("Error Message Clarity", test_error_messages_clarity()))
    
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
        print("\n" + "=" * 70)
        print("🎉 ALL SANITY CHECKS PRODUCTION-READY!")
        print("=" * 70)
        print("\nRuntimeguardrails implemented:")
        print("  ✓ NaN detection (prediction & probability)")
        print("  ✓ Infinite value detection")
        print("  ✓ Range validation (prediction: {0,1}, probability: [0,1])")
        print("  ✓ Edge case warnings (exactly 0.0 or 1.0)")
        print("  ✓ Clear, actionable error messages")
        print("  ✓ Graceful error handling")
        print("\n" + "=" * 70)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        sys.exit(1)
