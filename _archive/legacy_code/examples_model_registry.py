"""
Example: Using Model Registry with train.py
============================================

Demonstrates how to train different models using the registry.
"""

from src.models.model_registry import (
    list_available_models,
    get_model,
    get_registry,
    print_model_info
)

print("\n" + "="*70)
print("MODEL REGISTRY USAGE EXAMPLES")
print("="*70)

# Example 1: List available models
print("\n1. List Available Models:")
print("-"*70)
models = list_available_models()
for model in models:
    print(f"  - {model}")

# Example 2: Get model info
print("\n2. Get Model Information:")
print("-"*70)
registry = get_registry()
config = registry.get_config("random_forest")
print(f"Name: {config.name}")
print(f"Class: {config.model_class.__name__}")
print(f"Description: {config.description}")
print(f"Supports Probability: {config.supports_probability}")

# Example 3: Create model instances
print("\n3. Create Model Instances:")
print("-"*70)
for model_name in models:
    model = get_model(model_name)
    print(f"Created: {model_name} -> {type(model).__name__}")

# Example 4: Custom parameters
print("\n4. Create Model with Custom Parameters:")
print("-"*70)
custom_rf = get_model("random_forest", custom_params={"n_estimators": 200, "max_depth": 15})
print(f"Custom Random Forest:")
print(f"  n_estimators: {custom_rf.n_estimators}")
print(f"  max_depth: {custom_rf.max_depth}")

# Example 5: Training different models (pseudo-code)
print("\n5. Training Different Models (using train.py):")
print("-"*70)
print("""
# Train Logistic Regression
from src.train import train
metrics_lr = train(model_name="logistic_regression")

# Train Random Forest
metrics_rf = train(model_name="random_forest")

# Train XGBoost
metrics_xgb = train(model_name="xgboost")

# Compare results
print(f"Logistic Regression ROC-AUC: {metrics_lr['roc_auc']:.4f}")
print(f"Random Forest ROC-AUC: {metrics_rf['roc_auc']:.4f}")
print(f"XGBoost ROC-AUC: {metrics_xgb['roc_auc']:.4f}")
""")

# Example 6: Full model info
print("\n6. Full Model Registry Info:")
print("-"*70)
print_model_info()

print("\n" + "="*70)
print("✓ Model Registry Ready for Training!")
print("="*70)
print("\nNext Steps:")
print("  1. Create training data: data/raw/train.csv")
print("  2. Train model: python -m src.train (uses random_forest by default)")
print("  3. Or specify model: from src.train import train; train(model_name='xgboost')")
print("="*70 + "\n")
