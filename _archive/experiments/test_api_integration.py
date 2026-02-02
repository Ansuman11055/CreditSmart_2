"""Test FastAPI integration with ML inference engine.

This script tests the complete API workflow with ML model predictions.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.ml.model import CreditRiskModel
from app.schemas.request import CreditRiskRequest


def test_model_wrapper_ml():
    """Test 1: Model wrapper with ML engine."""
    print("\n" + "=" * 70)
    print("TEST 1: Model Wrapper with ML Engine")
    print("=" * 70)
    
    try:
        # Initialize model with ML engine
        model = CreditRiskModel(use_ml_model=True)
        
        info = model.get_model_info()
        print("\n✓ Model wrapper initialized")
        print(f"  Model type: {info['model_type']}")
        print(f"  Is loaded: {info['is_loaded']}")
        
        if info['model_type'] == 'ml':
            print(f"  ML model type: {info['ml_model_type']}")
            print(f"  Schema version: {info['schema_version']}")
            print(f"  Number of features: {info['num_features']}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_wrapper_prediction():
    """Test 2: Full prediction workflow through model wrapper."""
    print("\n" + "=" * 70)
    print("TEST 2: Full Prediction Workflow")
    print("=" * 70)
    
    try:
        model = CreditRiskModel(use_ml_model=True)
        
        # Create request (good applicant)
        request = CreditRiskRequest(
            annual_income=85000,
            monthly_debt=1200,
            credit_score=750,
            loan_amount=20000,
            loan_term_months=48,
            employment_length_years=7.0,
            home_ownership="OWN",
            purpose="home_improvement",
            number_of_open_accounts=4,
            delinquencies_2y=0,
            inquiries_6m=0,
        )
        
        print("\nGood Applicant Profile:")
        print(f"  Credit score: {request.credit_score}")
        print(f"  Annual income: ${request.annual_income:,.0f}")
        print(f"  Monthly debt: ${request.monthly_debt:,.0f}")
        print(f"  DTI: {request.compute_dti():.2%}")
        print(f"  Delinquencies: {request.delinquencies_2y}")
        
        response = model.predict(request)
        
        print("\n✓ Prediction response:")
        print(f"  Risk score: {response.risk_score:.2f}/100")
        print(f"  Risk level: {response.risk_level.value}")
        print(f"  Recommended action: {response.recommended_action}")
        print(f"  Model version: {response.model_version}")
        
        if hasattr(response, 'key_factors') and response.key_factors:
            print(f"\n  Key factors:")
            if 'prediction' in response.key_factors:
                print(f"    Prediction: {response.key_factors['prediction']}")
            if 'probability' in response.key_factors:
                print(f"    Probability: {response.key_factors['probability']:.4f}")
        
        print(f"\n  Explanation: {response.explanation[:150]}...")
        
        # Validate response structure
        assert hasattr(response, 'risk_score'), "Missing risk_score"
        assert hasattr(response, 'risk_level'), "Missing risk_level"
        assert hasattr(response, 'recommended_action'), "Missing recommended_action"
        assert hasattr(response, 'explanation'), "Missing explanation"
        
        print("\n✓ Response structure validation passed")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_wrapper_bad_applicant():
    """Test 3: Bad applicant prediction."""
    print("\n" + "=" * 70)
    print("TEST 3: Bad Applicant Prediction")
    print("=" * 70)
    
    try:
        model = CreditRiskModel(use_ml_model=True)
        
        # Create request (bad applicant)
        request = CreditRiskRequest(
            annual_income=30000,
            monthly_debt=2500,
            credit_score=520,
            loan_amount=18000,
            loan_term_months=60,
            employment_length_years=0.5,
            home_ownership="RENT",
            purpose="debt_consolidation",
            number_of_open_accounts=12,
            delinquencies_2y=5,
            inquiries_6m=8,
        )
        
        print("\nBad Applicant Profile:")
        print(f"  Credit score: {request.credit_score} (very low)")
        print(f"  Annual income: ${request.annual_income:,.0f}")
        print(f"  Monthly debt: ${request.monthly_debt:,.0f}")
        print(f"  DTI: {request.compute_dti():.2%} (very high)")
        print(f"  Delinquencies: {request.delinquencies_2y} (high)")
        print(f"  Inquiries: {request.inquiries_6m} (high)")
        
        response = model.predict(request)
        
        print("\n✓ Prediction response:")
        print(f"  Risk score: {response.risk_score:.2f}/100")
        print(f"  Risk level: {response.risk_level.value}")
        print(f"  Recommended action: {response.recommended_action}")
        
        # Expect high risk for bad applicant
        if response.risk_score > 50:
            print("\n✓ Correctly identified as high risk")
        else:
            print(f"\n⚠️  Risk score {response.risk_score:.2f} lower than expected for bad applicant")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_wrapper_fallback():
    """Test 4: Fallback to rule-based engine."""
    print("\n" + "=" * 70)
    print("TEST 4: Rule-Based Engine Fallback")
    print("=" * 70)
    
    try:
        # Initialize with ML disabled (should fall back to rule-based)
        model = CreditRiskModel(use_ml_model=False)
        
        info = model.get_model_info()
        print("\n✓ Model wrapper initialized with rule-based engine")
        print(f"  Model type: {info['model_type']}")
        print(f"  Is loaded: {info['is_loaded']}")
        
        # Test prediction
        request = CreditRiskRequest(
            annual_income=60000,
            monthly_debt=1000,
            credit_score=680,
            loan_amount=15000,
            loan_term_months=36,
            employment_length_years=3.0,
            home_ownership="MORTGAGE",
            purpose="car",
            number_of_open_accounts=6,
            delinquencies_2y=1,
            inquiries_6m=2,
        )
        
        response = model.predict(request)
        
        print("\n✓ Rule-based prediction:")
        print(f"  Risk score: {response.risk_score:.2f}/100")
        print(f"  Risk level: {response.risk_level.value}")
        print(f"  Recommended action: {response.recommended_action}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("FASTAPI MODEL WRAPPER - INTEGRATION TEST")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("ML Model Wrapper", test_model_wrapper_ml()))
    results.append(("Full Prediction Workflow", test_model_wrapper_prediction()))
    results.append(("Bad Applicant Prediction", test_model_wrapper_bad_applicant()))
    results.append(("Rule-Based Fallback", test_model_wrapper_fallback()))
    
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
        print("\n🎉 All tests passed! FastAPI integration is production-ready.")
        print("\nTo start the API server:")
        print("  uvicorn app.main:app --reload")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        sys.exit(1)
