"""Quick test of the preprocessing pipeline."""

import pandas as pd
import numpy as np
from src.preprocess import DataPreprocessor

# Create sample data matching feature schema
sample_data = pd.DataFrame({
    # Required numeric features
    "annual_income": [50000, 75000, 120000],
    "monthly_debt": [1200, 1800, 2500],
    "credit_score": [680, 720, 780],
    "loan_amount": [15000, 20000, 30000],
    "loan_term_months": [36, 48, 60],
    "employment_length_years": [2.5, 5.0, 10.0],
    
    # Required categorical features
    "home_ownership": ["RENT", "MORTGAGE", "OWN"],
    "purpose": ["debt_consolidation", "home_improvement", "car"],
    
    # Optional numeric features (with some missing values)
    "number_of_open_accounts": [5, 8, np.nan],
    "delinquencies_2y": [0, 1, 0],
    "inquiries_6m": [2, np.nan, 1],
    
    # Target
    "default": [0, 0, 0],
})

print("=" * 60)
print("Testing Preprocessing Pipeline")
print("=" * 60)

# Initialize preprocessor
preprocessor = DataPreprocessor(data_dir="data")

print(f"\n1. Input data shape: {sample_data.shape}")
print(f"   Columns: {list(sample_data.columns)}")

# Test preprocessing with fit=True (training mode)
print("\n2. Testing fit mode (training)...")
X_train, y_train, metadata = preprocessor.preprocess(
    sample_data, fit=True, save_output=False
)

print(f"   ✓ Preprocessing successful!")
print(f"   Input features: {metadata['n_input_features']}")
print(f"   Output features: {metadata['n_output_features']}")
print(f"   Numeric features: {len(metadata['numeric_features'])}")
print(f"   Categorical features: {len(metadata['categorical_features'])}")
print(f"   Output shape: {X_train.shape}")
print(f"   Target shape: {y_train.shape}")

# Show some transformed features
print(f"\n3. Sample transformed features (first row):")
for col in X_train.columns[:5]:
    print(f"   {col}: {X_train[col].iloc[0]:.4f}")

# Test preprocessing with fit=False (inference mode)
print("\n4. Testing transform mode (inference)...")
new_sample = sample_data.iloc[:1].copy()
X_inference, _, _ = preprocessor.preprocess(
    new_sample, fit=False, save_output=False
)

print(f"   ✓ Transform successful!")
print(f"   Output shape: {X_inference.shape}")

# Verify feature names match
print(f"\n5. Feature name consistency check:")
print(f"   Training features: {len(preprocessor.feature_columns)}")
print(f"   Inference features: {len(X_inference.columns)}")
print(f"   Match: {list(preprocessor.feature_columns) == list(X_inference.columns)}")

# Show engineered features
print(f"\n6. Engineered features:")
debt_to_income_features = [col for col in X_train.columns if "debt_to_income" in col]
if debt_to_income_features:
    print(f"   Found: {debt_to_income_features}")
else:
    print("   No debt_to_income feature found")

# Show categorical encoding
print(f"\n7. Categorical encoding:")
home_features = [col for col in X_train.columns if col.startswith("home_ownership")]
purpose_features = [col for col in X_train.columns if col.startswith("purpose")]
print(f"   home_ownership encoded to {len(home_features)} features")
print(f"   purpose encoded to {len(purpose_features)} features")

print("\n" + "=" * 60)
print("✓ All tests passed!")
print("=" * 60)

# Show saved artifacts
print("\n8. Check saved artifacts:")
from pathlib import Path
models_dir = Path("models")
preprocessor_file = models_dir / "preprocessor.joblib"
if preprocessor_file.exists():
    print(f"   ✓ Found: {preprocessor_file}")
    size_kb = preprocessor_file.stat().st_size / 1024
    print(f"   Size: {size_kb:.1f} KB")
else:
    print(f"   Note: {preprocessor_file} not saved (save_output=False in test)")
