"""Test strict Pydantic schema validation.

This script tests the strict validation requirements:
- Extra fields rejected
- Missing fields rejected  
- Invalid data types rejected
- Out-of-range values rejected
- Invalid enum values rejected
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pydantic import ValidationError
from app.schemas.request import CreditRiskRequest


def test_valid_request():
    """Test 1: Valid request with all fields."""
    print("\n" + "=" * 70)
    print("TEST 1: Valid Request (All Fields Present)")
    print("=" * 70)
    
    try:
        request = CreditRiskRequest(
            annual_income=75000,
            monthly_debt=1200,
            credit_score=720,
            loan_amount=25000,
            loan_term_months=60,
            employment_length_years=5.0,
            home_ownership="MORTGAGE",
            purpose="debt_consolidation",
            number_of_open_accounts=8,
            delinquencies_2y=0,
            inquiries_6m=1,
        )
        
        print("\n✓ Request validated successfully")
        print(f"  Credit score: {request.credit_score}")
        print(f"  Loan amount: ${request.loan_amount:,.0f}")
        print(f"  DTI: {request.compute_dti():.2f}%")
        
        return True
        
    except ValidationError as e:
        print(f"\n✗ Validation failed (unexpected): {e}")
        return False


def test_extra_field_rejected():
    """Test 2: Extra fields are rejected."""
    print("\n" + "=" * 70)
    print("TEST 2: Extra Field Rejection")
    print("=" * 70)
    
    try:
        request = CreditRiskRequest(
            annual_income=75000,
            monthly_debt=1200,
            credit_score=720,
            loan_amount=25000,
            loan_term_months=60,
            employment_length_years=5.0,
            home_ownership="MORTGAGE",
            purpose="debt_consolidation",
            number_of_open_accounts=8,
            delinquencies_2y=0,
            inquiries_6m=1,
            extra_field="not_allowed",  # Extra field
        )
        
        print("\n✗ Extra field was NOT rejected (test failed)")
        return False
        
    except ValidationError as e:
        print("\n✓ Extra field correctly rejected")
        print(f"  Error: {e.errors()[0]['msg']}")
        print(f"  Field: {e.errors()[0]['loc']}")
        return True


def test_missing_field_rejected():
    """Test 3: Missing required fields are rejected."""
    print("\n" + "=" * 70)
    print("TEST 3: Missing Required Field Rejection")
    print("=" * 70)
    
    try:
        # Missing credit_score (required field)
        request = CreditRiskRequest(
            annual_income=75000,
            monthly_debt=1200,
            # credit_score=720,  # Missing
            loan_amount=25000,
            loan_term_months=60,
            employment_length_years=5.0,
            home_ownership="MORTGAGE",
            purpose="debt_consolidation",
            number_of_open_accounts=8,
            delinquencies_2y=0,
            inquiries_6m=1,
        )
        
        print("\n✗ Missing field was NOT rejected (test failed)")
        return False
        
    except ValidationError as e:
        print("\n✓ Missing field correctly rejected")
        print(f"  Error: {e.errors()[0]['msg']}")
        print(f"  Field: {e.errors()[0]['loc']}")
        return True


def test_invalid_type_rejected():
    """Test 4: Invalid data types are rejected."""
    print("\n" + "=" * 70)
    print("TEST 4: Invalid Data Type Rejection")
    print("=" * 70)
    
    try:
        request = CreditRiskRequest(
            annual_income=75000,
            monthly_debt=1200,
            credit_score="not_a_number",  # Should be int
            loan_amount=25000,
            loan_term_months=60,
            employment_length_years=5.0,
            home_ownership="MORTGAGE",
            purpose="debt_consolidation",
            number_of_open_accounts=8,
            delinquencies_2y=0,
            inquiries_6m=1,
        )
        
        print("\n✗ Invalid type was NOT rejected (test failed)")
        return False
        
    except ValidationError as e:
        print("\n✓ Invalid type correctly rejected")
        print(f"  Error: {e.errors()[0]['msg']}")
        print(f"  Field: {e.errors()[0]['loc']}")
        print(f"  Input: {e.errors()[0]['input']}")
        return True


def test_out_of_range_rejected():
    """Test 5: Out-of-range values are rejected."""
    print("\n" + "=" * 70)
    print("TEST 5: Out-of-Range Value Rejection")
    print("=" * 70)
    
    try:
        request = CreditRiskRequest(
            annual_income=75000,
            monthly_debt=1200,
            credit_score=950,  # Out of range (max 850)
            loan_amount=25000,
            loan_term_months=60,
            employment_length_years=5.0,
            home_ownership="MORTGAGE",
            purpose="debt_consolidation",
            number_of_open_accounts=8,
            delinquencies_2y=0,
            inquiries_6m=1,
        )
        
        print("\n✗ Out-of-range value was NOT rejected (test failed)")
        return False
        
    except ValidationError as e:
        print("\n✓ Out-of-range value correctly rejected")
        print(f"  Error: {e.errors()[0]['msg']}")
        print(f"  Field: {e.errors()[0]['loc']}")
        print(f"  Input: {e.errors()[0]['input']}")
        return True


def test_invalid_enum_rejected():
    """Test 6: Invalid enum values are rejected."""
    print("\n" + "=" * 70)
    print("TEST 6: Invalid Enum Value Rejection")
    print("=" * 70)
    
    try:
        request = CreditRiskRequest(
            annual_income=75000,
            monthly_debt=1200,
            credit_score=720,
            loan_amount=25000,
            loan_term_months=60,
            employment_length_years=5.0,
            home_ownership="INVALID_STATUS",  # Invalid enum
            purpose="debt_consolidation",
            number_of_open_accounts=8,
            delinquencies_2y=0,
            inquiries_6m=1,
        )
        
        print("\n✗ Invalid enum was NOT rejected (test failed)")
        return False
        
    except ValidationError as e:
        print("\n✓ Invalid enum correctly rejected")
        print(f"  Error: {e.errors()[0]['msg']}")
        print(f"  Field: {e.errors()[0]['loc']}")
        print(f"  Input: {e.errors()[0]['input']}")
        return True


def test_negative_value_rejected():
    """Test 7: Negative values are rejected where not allowed."""
    print("\n" + "=" * 70)
    print("TEST 7: Negative Value Rejection")
    print("=" * 70)
    
    try:
        request = CreditRiskRequest(
            annual_income=-50000,  # Negative income
            monthly_debt=1200,
            credit_score=720,
            loan_amount=25000,
            loan_term_months=60,
            employment_length_years=5.0,
            home_ownership="MORTGAGE",
            purpose="debt_consolidation",
            number_of_open_accounts=8,
            delinquencies_2y=0,
            inquiries_6m=1,
        )
        
        print("\n✗ Negative value was NOT rejected (test failed)")
        return False
        
    except ValidationError as e:
        print("\n✓ Negative value correctly rejected")
        print(f"  Error: {e.errors()[0]['msg']}")
        print(f"  Field: {e.errors()[0]['loc']}")
        print(f"  Input: {e.errors()[0]['input']}")
        return True


def test_whitespace_stripping():
    """Test 8: Whitespace is stripped from string fields."""
    print("\n" + "=" * 70)
    print("TEST 8: Whitespace Stripping")
    print("=" * 70)
    
    try:
        request = CreditRiskRequest(
            annual_income=75000,
            monthly_debt=1200,
            credit_score=720,
            loan_amount=25000,
            loan_term_months=60,
            employment_length_years=5.0,
            home_ownership="  MORTGAGE  ",  # Whitespace
            purpose="  debt_consolidation  ",  # Whitespace
            number_of_open_accounts=8,
            delinquencies_2y=0,
            inquiries_6m=1,
        )
        
        print("\n✓ Whitespace correctly stripped")
        print(f"  home_ownership: '{request.home_ownership}'")
        print(f"  purpose: '{request.purpose}'")
        
        assert request.home_ownership == "MORTGAGE"
        assert request.purpose == "debt_consolidation"
        
        return True
        
    except ValidationError as e:
        print(f"\n✗ Validation failed: {e}")
        return False


def test_all_required_fields():
    """Test 9: All 11 fields are required (no defaults for credit history)."""
    print("\n" + "=" * 70)
    print("TEST 9: All Required Fields Validation")
    print("=" * 70)
    
    required_fields = [
        "annual_income",
        "monthly_debt",
        "credit_score",
        "loan_amount",
        "loan_term_months",
        "employment_length_years",
        "home_ownership",
        "purpose",
        "number_of_open_accounts",
        "delinquencies_2y",
        "inquiries_6m",
    ]
    
    # Try omitting each field
    failed_fields = []
    
    for field in required_fields:
        data = {
            "annual_income": 75000,
            "monthly_debt": 1200,
            "credit_score": 720,
            "loan_amount": 25000,
            "loan_term_months": 60,
            "employment_length_years": 5.0,
            "home_ownership": "MORTGAGE",
            "purpose": "debt_consolidation",
            "number_of_open_accounts": 8,
            "delinquencies_2y": 0,
            "inquiries_6m": 1,
        }
        
        # Remove the field
        del data[field]
        
        try:
            request = CreditRiskRequest(**data)
            failed_fields.append(field)
        except ValidationError:
            pass  # Expected
    
    if failed_fields:
        print(f"\n✗ These fields were NOT required: {failed_fields}")
        return False
    else:
        print(f"\n✓ All {len(required_fields)} fields are required")
        print(f"  Required fields: {', '.join(required_fields)}")
        return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("STRICT PYDANTIC SCHEMA VALIDATION - TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Valid Request", test_valid_request()))
    results.append(("Extra Field Rejection", test_extra_field_rejected()))
    results.append(("Missing Field Rejection", test_missing_field_rejected()))
    results.append(("Invalid Type Rejection", test_invalid_type_rejected()))
    results.append(("Out-of-Range Rejection", test_out_of_range_rejected()))
    results.append(("Invalid Enum Rejection", test_invalid_enum_rejected()))
    results.append(("Negative Value Rejection", test_negative_value_rejected()))
    results.append(("Whitespace Stripping", test_whitespace_stripping()))
    results.append(("All Required Fields", test_all_required_fields()))
    
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
        print("\n🎉 All tests passed! Schema validation is strict and production-ready.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        sys.exit(1)
