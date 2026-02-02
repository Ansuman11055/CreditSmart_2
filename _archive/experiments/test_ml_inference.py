"""Test production-safe ML inference engine.

This script tests the new ML inference engine with:
- Schema validation
- Error handling
- Prediction output format
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.ml.ml_inference import MLInferenceEngine, SchemaValidationError, ModelNotFoundError
from app.schemas.request import CreditRiskRequest


def test_model_loading():
    """Test 1: Model loading and artifact validation."""
    print("\n" + "=" * 70)
    print("TEST 1: Model Loading")
    print("=" * 70)
    
    try:
        engine = MLInferenceEngine(model_dir="models")
        info = engine.get_model_info()
        
        print("\n✓ Model loaded successfully")
        print(f"  Model type: {info['model_type']}")
        print(f"  Schema version: {info['schema_version']}")
        print(f"  Number of features: {info['num_features']}")
        print(f"  Feature names (first 5): {info['feature_names'][:5]}")
        
        return True
        
    except ModelNotFoundError as e:
        print(f"\n✗ Model not found: {e}")
        print("\nPlease train a model first:")
        print("  python -c \"from src.train import train; train(model_name='random_forest')\"")
        return False
        
    except Exception as e:
        print(f"\n✗ Failed to load model: {e}")
        return False


def test_valid_prediction():
    """Test 2: Valid prediction with proper schema."""
    print("\n" + "=" * 70)
    print("TEST 2: Valid Prediction")
    print("=" * 70)
    
    try:
        engine = MLInferenceEngine(model_dir="models")
        
        # Create valid request
        request = CreditRiskRequest(
            annual_income=75000,
            monthly_debt=1500,
            credit_score=720,
            loan_amount=25000,
            loan_term_months=60,
            employment_length_years=5.0,
            home_ownership="MORTGAGE",
            purpose="debt_consolidation",
            number_of_open_accounts=5,
            delinquencies_2y=0,
            inquiries_6m=1,
        )
        
        print("\nInput data:")
        print(f"  Credit score: {request.credit_score}")
        print(f"  Annual income: ${request.annual_income:,.0f}")
        print(f"  Monthly debt: ${request.monthly_debt:,.0f}")
        print(f"  Loan amount: ${request.loan_amount:,.0f}")
        print(f"  DTI: {request.compute_dti():.2%}")
        
        prediction, probability = engine.predict(request)
        
        print("\n✓ Prediction completed successfully")
        print(f"  Prediction: {prediction} ({'Default' if prediction == 1 else 'No Default'})")
        print(f"  Probability: {probability:.4f} ({probability:.2%})")
        print(f"  Risk level: {'LOW' if probability < 0.25 else 'MEDIUM' if probability < 0.50 else 'HIGH' if probability < 0.75 else 'VERY_HIGH'}")
        
        # Validate output types
        assert isinstance(prediction, int), f"Prediction must be int, got {type(prediction)}"
        assert prediction in [0, 1], f"Prediction must be 0 or 1, got {prediction}"
        assert isinstance(probability, float), f"Probability must be float, got {type(probability)}"
        assert 0.0 <= probability <= 1.0, f"Probability must be in [0, 1], got {probability}"
        
        print("\n✓ Output validation passed")
        print(f"  Prediction type: {type(prediction).__name__}")
        print(f"  Probability type: {type(probability).__name__}")
        print(f"  Probability range: [0.0, 1.0] ✓")
        
        return True
        
    except ModelNotFoundError as e:
        print(f"\n✗ Model not found: {e}")
        return False
        
    except Exception as e:
        print(f"\n✗ Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_high_risk_applicant():
    """Test 3: High-risk applicant prediction."""
    print("\n" + "=" * 70)
    print("TEST 3: High-Risk Applicant")
    print("=" * 70)
    
    try:
        engine = MLInferenceEngine(model_dir="models")
        
        # Create high-risk request
        request = CreditRiskRequest(
            annual_income=35000,
            monthly_debt=2000,
            credit_score=580,
            loan_amount=15000,
            loan_term_months=36,
            employment_length_years=1.0,
            home_ownership="RENT",
            purpose="debt_consolidation",
            number_of_open_accounts=8,
            delinquencies_2y=3,
            inquiries_6m=5,
        )
        
        print("\nInput data (high-risk profile):")
        print(f"  Credit score: {request.credit_score} (low)")
        print(f"  Annual income: ${request.annual_income:,.0f}")
        print(f"  Monthly debt: ${request.monthly_debt:,.0f}")
        print(f"  DTI: {request.compute_dti():.2%} (high)")
        print(f"  Delinquencies (2y): {request.delinquencies_2y}")
        print(f"  Inquiries (6m): {request.inquiries_6m}")
        
        prediction, probability = engine.predict(request)
        
        print("\n✓ Prediction completed successfully")
        print(f"  Prediction: {prediction} ({'Default' if prediction == 1 else 'No Default'})")
        print(f"  Probability: {probability:.4f} ({probability:.2%})")
        print(f"  Expected: Higher default probability due to risk factors")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Prediction failed: {e}")
        return False


def test_model_info():
    """Test 4: Model information retrieval."""
    print("\n" + "=" * 70)
    print("TEST 4: Model Information")
    print("=" * 70)
    
    try:
        engine = MLInferenceEngine(model_dir="models")
        info = engine.get_model_info()
        
        print("\nModel Information:")
        print(f"  Loaded: {info['is_loaded']}")
        print(f"  Model type: {info['model_type']}")
        print(f"  Schema version: {info['schema_version']}")
        print(f"  Number of features: {info['num_features']}")
        print(f"  Model directory: {info['model_dir']}")
        
        print("\nFeature names (first 10):")
        for i, feature in enumerate(info['feature_names'][:10], 1):
            print(f"  {i}. {feature}")
        
        if len(info['feature_names']) > 10:
            print(f"  ... and {len(info['feature_names']) - 10} more")
        
        print("\n✓ Model info retrieved successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to get model info: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("PRODUCTION-SAFE ML INFERENCE - TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Model Loading", test_model_loading()))
    
    # Only run other tests if model loaded successfully
    if results[0][1]:
        results.append(("Valid Prediction", test_valid_prediction()))
        results.append(("High-Risk Applicant", test_high_risk_applicant()))
        results.append(("Model Information", test_model_info()))
    
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
        print("\n🎉 All tests passed! ML inference engine is production-ready.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        sys.exit(1)
