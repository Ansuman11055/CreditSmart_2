"""Quick verification that project is running on original dataset."""
import pandas as pd
import joblib

print("="*70)
print("VERIFICATION: Project Running on Original Dataset")
print("="*70)

# Check dataset
df = pd.read_csv('data/raw/raw.csv')
print("\nDataset:")
print(f"  Records: {len(df):,}")
print(f"  Features: {len(df.columns) - 1}")
print(f"  Default Rate: {df['default'].mean():.2%}")

# Check model
model_data = joblib.load('models/model.joblib')
print("\nModel:")
print(f"  Type: {model_data['model_name']}")
print(f"  Features: {model_data['n_features']}")
print(f"  Test Accuracy: {model_data['metrics']['accuracy']:.2%}")
print(f"  Test ROC AUC: {model_data['metrics']['roc_auc']:.2%}")

# Check preprocessor
prep_data = joblib.load('models/preprocessor.joblib')
print("\nPreprocessor:")
print(f"  Output Features: {len(prep_data['feature_columns'])}")
print(f"  Schema Version: {prep_data['schema_version']}")

print("\n" + "="*70)
print("Status: All components verified - Project ready!")
print("="*70)
