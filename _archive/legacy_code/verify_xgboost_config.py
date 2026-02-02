"""Quick XGBoost configuration verification."""

from src.models.model_registry import get_registry

# Get XGBoost configuration
registry = get_registry()
config = registry.get_config("xgboost")
params = config.default_params

print("\n" + "="*70)
print("XGBOOST CONFIGURATION VERIFICATION")
print("="*70)

# Check key requirements
requirements = {
    "scale_pos_weight": 6.81,
    "objective": "binary:logistic",
    "use_label_encoder": False,
    "eval_metric": "auc",
}

all_passed = True
for param, expected in requirements.items():
    actual = params[param]
    if param == "scale_pos_weight":
        passed = abs(actual - expected) < 0.1
    else:
        passed = actual == expected
    
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {param}: {actual} (expected: {expected})")
    if not passed:
        all_passed = False

print("\nAdditional Configuration:")
additional = ["n_estimators", "max_depth", "learning_rate", "min_child_weight",
              "gamma", "reg_alpha", "reg_lambda", "subsample", "colsample_bytree"]
for param in additional:
    print(f"  {param}: {params[param]}")

print("\n" + "="*70)
if all_passed:
    print("SUCCESS: All requirements satisfied!")
    print(f"Description: {config.description}")
else:
    print("FAILURE: Some requirements not met")
print("="*70)
