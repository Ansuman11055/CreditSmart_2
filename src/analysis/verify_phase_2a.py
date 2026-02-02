"""
Phase 2A Verification Script
============================

Internal quality checks for preprocessing pipeline.

Usage:
    python src/analysis/verify_phase_2a.py
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.preprocess import DataPreprocessor
from src.core.feature_schema import (
    FEATURE_NAMES,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    REQUIRED_FEATURES,
    TARGET,
    SCHEMA_VERSION,
)
from src.core.validation import validate_training_data, ValidationError


class Phase2AVerifier:
    """Verification suite for Phase 2A preprocessing pipeline."""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def print_header(self, text: str) -> None:
        """Print formatted section header."""
        print(f"\n{'='*70}")
        print(f"{text}")
        print(f"{'='*70}")
    
    def print_check(self, name: str, passed: bool, details: str = "") -> None:
        """Print check result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        color = "green" if passed else "red"
        print(f"{status}: {name}")
        if details:
            print(f"       {details}")
        
        if passed:
            self.passed.append(name)
        else:
            self.failed.append(name)
    
    def print_warning(self, message: str) -> None:
        """Print warning message."""
        print(f"⚠ WARNING: {message}")
        self.warnings.append(message)
    
    def verify_sample_data(self) -> pd.DataFrame:
        """Create and validate sample data."""
        self.print_header("CHECK 1: Sample Data Creation")
        
        try:
            # Create synthetic data matching schema
            sample_data = pd.DataFrame({
                # Required numeric features
                "annual_income": [50000, 75000, 120000, 35000, 90000],
                "monthly_debt": [1200, 1800, 2500, 2000, 1500],
                "credit_score": [680, 720, 780, 580, 750],
                "loan_amount": [15000, 20000, 30000, 40000, 25000],
                "loan_term_months": [36, 48, 60, 84, 48],
                "employment_length_years": [2.5, 5.0, 10.0, 0.5, 7.0],
                
                # Required categorical features
                "home_ownership": ["RENT", "MORTGAGE", "OWN", "RENT", "MORTGAGE"],
                "purpose": ["debt_consolidation", "home_improvement", "car", 
                           "major_purchase", "debt_consolidation"],
                
                # Optional numeric features (with some missing values)
                "number_of_open_accounts": [5, 8, 12, 15, 6],
                "delinquencies_2y": [0, 1, 0, 3, 0],
                "inquiries_6m": [2, 1, 1, 6, np.nan],
                
                # Target
                "default": [0, 0, 0, 1, 0],
            })
            
            self.print_check("Create sample data", True, 
                           f"{len(sample_data)} records, {len(sample_data.columns)} columns")
            return sample_data
            
        except Exception as e:
            self.print_check("Create sample data", False, str(e))
            raise
    
    def verify_schema_validation(self, df: pd.DataFrame) -> None:
        """Verify schema validation works."""
        self.print_header("CHECK 2: Schema Validation")
        
        # Check 2.1: Required features present
        try:
            missing_features = set(REQUIRED_FEATURES) - set(df.columns)
            passed = len(missing_features) == 0
            self.print_check("All required features present", passed,
                           f"{len(REQUIRED_FEATURES)} required features")
        except Exception as e:
            self.print_check("All required features present", False, str(e))
        
        # Check 2.2: Target column present
        try:
            passed = TARGET in df.columns
            self.print_check("Target column present", passed, f"'{TARGET}'")
        except Exception as e:
            self.print_check("Target column present", False, str(e))
        
        # Check 2.3: Schema validation passes
        try:
            validate_training_data(df)
            self.print_check("Schema validation passes", True,
                           f"Schema version {SCHEMA_VERSION}")
        except ValidationError as e:
            self.print_check("Schema validation passes", False, str(e))
        except Exception as e:
            self.print_check("Schema validation passes", False, str(e))
        
        # Check 2.4: Data types correct
        try:
            type_errors = []
            for col in df.columns:
                if col in NUMERIC_FEATURES:
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        type_errors.append(f"{col} should be numeric")
                elif col in CATEGORICAL_FEATURES:
                    if not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                        type_errors.append(f"{col} should be string/object")
            
            passed = len(type_errors) == 0
            details = "All types correct" if passed else ", ".join(type_errors)
            self.print_check("Data types correct", passed, details)
        except Exception as e:
            self.print_check("Data types correct", False, str(e))
    
    def verify_preprocessing_pipeline(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """Verify preprocessing pipeline works."""
        self.print_header("CHECK 3: Preprocessing Pipeline")
        
        # Check 3.1: Initialize preprocessor
        try:
            preprocessor = DataPreprocessor(data_dir="data")
            self.print_check("Initialize preprocessor", True,
                           f"Models dir: {preprocessor.models_dir}")
        except Exception as e:
            self.print_check("Initialize preprocessor", False, str(e))
            raise
        
        # Check 3.2: Fit preprocessing pipeline
        try:
            X, y, metadata = preprocessor.preprocess(df, fit=True, save_output=False)
            self.print_check("Fit preprocessing pipeline", True,
                           f"{metadata['n_output_features']} output features")
        except Exception as e:
            self.print_check("Fit preprocessing pipeline", False, str(e))
            raise
        
        # Check 3.3: No missing values after preprocessing
        try:
            missing_count = X.isnull().sum().sum()
            passed = missing_count == 0
            self.print_check("No missing values in output", passed,
                           f"{missing_count} missing values" if not passed else "All values present")
        except Exception as e:
            self.print_check("No missing values in output", False, str(e))
        
        # Check 3.4: Correct number of features
        try:
            expected_min = len(NUMERIC_FEATURES) + len(CATEGORICAL_FEATURES)
            actual = len(X.columns)
            # One-hot encoding increases feature count
            passed = actual >= expected_min
            self.print_check("Correct feature count", passed,
                           f"{actual} features (min expected: {expected_min})")
        except Exception as e:
            self.print_check("Correct feature count", False, str(e))
        
        # Check 3.5: Feature names stored
        try:
            passed = preprocessor.feature_columns is not None
            count = len(preprocessor.feature_columns) if passed else 0
            self.print_check("Feature names stored", passed,
                           f"{count} feature names")
        except Exception as e:
            self.print_check("Feature names stored", False, str(e))
        
        # Check 3.6: Numeric features scaled
        try:
            numeric_cols = [col for col in X.columns if col in NUMERIC_FEATURES or col == "debt_to_income_ratio"]
            if len(numeric_cols) > 0:
                means = X[numeric_cols].mean()
                stds = X[numeric_cols].std()
                # Check if approximately standardized (mean ~0, std ~1)
                mean_check = all(abs(m) < 0.5 for m in means)
                std_check = all(abs(s - 1.0) < 0.5 for s in stds)
                passed = mean_check and std_check
                details = f"Mean range: [{means.min():.3f}, {means.max():.3f}], Std range: [{stds.min():.3f}, {stds.max():.3f}]"
                self.print_check("Numeric features scaled", passed, details)
            else:
                self.print_warning("No numeric features found to verify scaling")
        except Exception as e:
            self.print_check("Numeric features scaled", False, str(e))
        
        # Check 3.7: Categorical features encoded
        try:
            # Look for one-hot encoded columns (e.g., home_ownership_RENT)
            encoded_cols = [col for col in X.columns if any(cat in col for cat in CATEGORICAL_FEATURES)]
            passed = len(encoded_cols) > 0
            self.print_check("Categorical features encoded", passed,
                           f"{len(encoded_cols)} encoded columns")
        except Exception as e:
            self.print_check("Categorical features encoded", False, str(e))
        
        # Check 3.8: Transform mode (inference) works
        try:
            X_inference, _, _ = preprocessor.preprocess(df.iloc[:1], fit=False, save_output=False)
            passed = X_inference.shape[1] == X.shape[1]
            self.print_check("Transform mode works", passed,
                           f"Inference shape: {X_inference.shape}")
        except Exception as e:
            self.print_check("Transform mode works", False, str(e))
        
        return X, y
    
    def verify_artifact_persistence(self) -> None:
        """Verify artifact can be saved and loaded."""
        self.print_header("CHECK 4: Artifact Persistence")
        
        # Check 4.1: Create test data and fit pipeline
        try:
            test_data = pd.DataFrame({
                "annual_income": [60000],
                "monthly_debt": [1500],
                "credit_score": [700],
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
            
            preprocessor = DataPreprocessor(data_dir="data")
            X1, y1, _ = preprocessor.preprocess(test_data, fit=True, save_output=True)
            
            artifact_path = Path("models/preprocessor.joblib")
            passed = artifact_path.exists()
            size_kb = artifact_path.stat().st_size / 1024 if passed else 0
            self.print_check("Artifact saved", passed,
                           f"{artifact_path} ({size_kb:.2f} KB)" if passed else str(artifact_path))
        except Exception as e:
            self.print_check("Artifact saved", False, str(e))
            return
        
        # Check 4.2: Load artifact
        try:
            preprocessor2 = DataPreprocessor(data_dir="data")
            preprocessor2.load_pipeline()
            passed = preprocessor2.preprocessing_pipeline is not None
            self.print_check("Artifact loaded", passed,
                           f"{len(preprocessor2.feature_columns)} features")
        except Exception as e:
            self.print_check("Artifact loaded", False, str(e))
            return
        
        # Check 4.3: Consistency check (same transformation)
        try:
            X2, y2, _ = preprocessor2.preprocess(test_data, fit=False, save_output=False)
            passed = np.allclose(X1.values, X2.values)
            self.print_check("Transformation consistency", passed,
                           "Saved and loaded pipelines produce identical output")
        except Exception as e:
            self.print_check("Transformation consistency", False, str(e))
    
    def verify_feature_engineering(self) -> None:
        """Verify feature engineering works correctly."""
        self.print_header("CHECK 5: Feature Engineering")
        
        # Check 5.1: Debt-to-income ratio calculated
        try:
            test_data = pd.DataFrame({
                "annual_income": [60000, 120000],
                "monthly_debt": [1500, 3000],
                "credit_score": [700, 750],
                "loan_amount": [20000, 30000],
                "loan_term_months": [48, 60],
                "employment_length_years": [5.0, 10.0],
                "home_ownership": ["OWN", "OWN"],
                "purpose": ["car", "car"],
                "number_of_open_accounts": [8, 10],
                "delinquencies_2y": [0, 0],
                "inquiries_6m": [1, 1],
                "default": [0, 0],
            })
            
            preprocessor = DataPreprocessor(data_dir="data")
            X, y, _ = preprocessor.preprocess(test_data, fit=True, save_output=False)
            
            # Check if debt_to_income_ratio was created
            passed = "debt_to_income_ratio" in X.columns
            self.print_check("Debt-to-income ratio engineered", passed,
                           "Feature 'debt_to_income_ratio' found" if passed else "Feature not found")
        except Exception as e:
            self.print_check("Debt-to-income ratio engineered", False, str(e))
    
    def print_summary(self) -> int:
        """Print verification summary."""
        self.print_header("VERIFICATION SUMMARY")
        
        total_checks = len(self.passed) + len(self.failed)
        pass_rate = (len(self.passed) / total_checks * 100) if total_checks > 0 else 0
        
        print(f"\nTotal Checks: {total_checks}")
        print(f"Passed: {len(self.passed)} ✓")
        print(f"Failed: {len(self.failed)} ✗")
        print(f"Warnings: {len(self.warnings)} ⚠")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.warnings:
            print(f"\nWarnings:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
        
        if self.failed:
            print(f"\nFailed Checks:")
            for check in self.failed:
                print(f"  ✗ {check}")
        
        print(f"\n{'='*70}")
        if len(self.failed) == 0:
            print("✓ PHASE 2A VERIFICATION: PASSED")
            print("All preprocessing pipeline checks passed successfully!")
        else:
            print("✗ PHASE 2A VERIFICATION: FAILED")
            print(f"{len(self.failed)} check(s) failed. Please review and fix.")
        print(f"{'='*70}\n")
        
        return 0 if len(self.failed) == 0 else 1
    
    def run(self) -> int:
        """Run all verification checks."""
        print("\n" + "="*70)
        print("PHASE 2A VERIFICATION SCRIPT")
        print("="*70)
        print(f"Schema Version: {SCHEMA_VERSION}")
        print(f"Date: 2026-01-31")
        
        try:
            # Run all checks
            df = self.verify_sample_data()
            self.verify_schema_validation(df)
            X, y = self.verify_preprocessing_pipeline(df)
            self.verify_artifact_persistence()
            self.verify_feature_engineering()
            
        except Exception as e:
            print(f"\n✗ CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.failed.append("Critical error during verification")
        
        # Print summary
        return self.print_summary()


def main():
    """Main entry point."""
    verifier = Phase2AVerifier()
    exit_code = verifier.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
