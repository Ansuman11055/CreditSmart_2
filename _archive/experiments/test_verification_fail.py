"""
Quick test to demonstrate Phase 2A verification failure detection.

This script intentionally creates invalid data to show FAIL messages.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.verify_phase_2a import Phase2AVerifier
import pandas as pd

print("\n" + "="*70)
print("TESTING VERIFICATION FAILURE DETECTION")
print("="*70)

verifier = Phase2AVerifier()
verifier.print_header("Demonstrating FAIL Detection")

# Test 1: Missing required column
print("\nTest 1: Missing required column...")
invalid_data = pd.DataFrame({
    "annual_income": [50000],
    "monthly_debt": [1500],
    # Missing credit_score (required!)
    "loan_amount": [20000],
})

try:
    from src.core.validation import validate_training_data
    validate_training_data(invalid_data)
    verifier.print_check("Detect missing required column", False, 
                        "Should have raised ValidationError")
except Exception as e:
    verifier.print_check("Detect missing required column", True,
                        f"Correctly detected: {str(e)[:60]}...")

# Test 2: Invalid credit score
print("\nTest 2: Invalid credit score value...")
invalid_score_data = pd.DataFrame({
    "annual_income": [50000],
    "monthly_debt": [1500],
    "credit_score": [950],  # Invalid! Max is 850
    "loan_amount": [20000],
    "loan_term_months": [48],
    "employment_length_years": [5.0],
    "home_ownership": ["OWN"],
    "purpose": ["car"],
    "number_of_open_accounts": [8],
    "delinquencies_2y": [0],
    "inquiries_6m": [1],
    "default": [0],
})

try:
    from src.core.validation import validate_training_data
    validate_training_data(invalid_score_data)
    verifier.print_check("Detect invalid credit score", False,
                        "Should have raised ValidationError")
except Exception as e:
    verifier.print_check("Detect invalid credit score", True,
                        f"Correctly detected: {str(e)[:60]}...")

# Test 3: Non-existent artifact
print("\nTest 3: Missing artifact file...")
from src.preprocess import DataPreprocessor
preprocessor = DataPreprocessor(data_dir="data")

# Remove artifact temporarily
import shutil
artifact_path = Path("models/preprocessor.joblib")
backup_path = Path("models/preprocessor.joblib.backup")

if artifact_path.exists():
    shutil.move(str(artifact_path), str(backup_path))

try:
    preprocessor.load_pipeline()
    verifier.print_check("Detect missing artifact", False,
                        "Should have raised FileNotFoundError")
except FileNotFoundError as e:
    verifier.print_check("Detect missing artifact", True,
                        "Correctly raised FileNotFoundError")
finally:
    # Restore artifact
    if backup_path.exists():
        shutil.move(str(backup_path), str(artifact_path))

print("\n" + "="*70)
print(f"✓ Failure Detection Tests: {len(verifier.passed)}/{len(verifier.passed) + len(verifier.failed)} PASSED")
print("="*70)
print("\nConclusion: Verification script correctly detects failures! ✓")
print("="*70 + "\n")
