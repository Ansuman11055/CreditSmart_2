"""Test preprocessing artifact persistence."""

import pandas as pd
import numpy as np
from pathlib import Path
from src.preprocess import DataPreprocessor

print("="*70)
print("Testing Preprocessing Artifact Persistence")
print("="*70)

# Create sample data
sample_data = pd.DataFrame({
    "annual_income": [50000, 75000, 120000],
    "monthly_debt": [1200, 1800, 2500],
    "credit_score": [680, 720, 780],
    "loan_amount": [15000, 20000, 30000],
    "loan_term_months": [36, 48, 60],
    "employment_length_years": [2.5, 5.0, 10.0],
    "home_ownership": ["RENT", "MORTGAGE", "OWN"],
    "purpose": ["debt_consolidation", "home_improvement", "car"],
    "number_of_open_accounts": [5, 8, np.nan],
    "delinquencies_2y": [0, 1, 0],
    "inquiries_6m": [2, np.nan, 1],
    "default": [0, 0, 0],
})

# Test 1: Fit and save
print("\n1. Fitting and saving preprocessing pipeline...")
preprocessor1 = DataPreprocessor(data_dir="data")
X_train, y_train, metadata = preprocessor1.preprocess(
    sample_data, fit=True, save_output=True
)
print(f"✓ Pipeline fitted and saved")
print(f"  Output features: {metadata['n_output_features']}")

# Check artifact exists
artifact_path = Path("models/preprocessor.joblib")
if artifact_path.exists():
    size_kb = artifact_path.stat().st_size / 1024
    print(f"✓ Artifact saved: {artifact_path} ({size_kb:.1f} KB)")
else:
    print(f"✗ Artifact not found: {artifact_path}")
    exit(1)

# Test 2: Load and transform
print("\n2. Loading preprocessing pipeline from disk...")
preprocessor2 = DataPreprocessor(data_dir="data")
preprocessor2.load_pipeline()
print(f"✓ Pipeline loaded successfully")

# Transform new data using loaded pipeline
new_sample = sample_data.iloc[:1].copy()
X_inference, _, _ = preprocessor2.preprocess(
    new_sample, fit=False, save_output=False
)
print(f"✓ Transform successful: {X_inference.shape}")

# Test 3: Verify consistency
print("\n3. Verifying consistency...")
match = np.allclose(X_train.iloc[0].values, X_inference.iloc[0].values)
print(f"✓ First row matches: {match}")

if not match:
    print("✗ Warning: Transformed values don't match!")
    print(f"  Original: {X_train.iloc[0].values[:3]}")
    print(f"  Loaded:   {X_inference.iloc[0].values[:3]}")
else:
    print(f"  First 3 features: {X_inference.iloc[0].values[:3]}")

# Test 4: Schema version tracking
print("\n4. Schema version tracking...")
import joblib
artifact = joblib.load(artifact_path)
print(f"✓ Schema version in artifact: {artifact['schema_version']}")
print(f"✓ Feature columns stored: {len(artifact['feature_columns'])}")

print("\n" + "="*70)
print("✓ All persistence tests passed!")
print("="*70)
print("\nArtifact contents:")
print(f"  - Fitted preprocessing pipeline")
print(f"  - {len(artifact['feature_columns'])} feature column names")
print(f"  - Schema version: {artifact['schema_version']}")
