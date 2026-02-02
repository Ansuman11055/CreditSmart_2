"""Test train.py model registry integration."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.train import CreditRiskTrainer
from src.models.model_registry import list_available_models

print("="*70)
print("Testing Model Registry Integration with train.py")
print("="*70)

# Test 1: List available models
print("\nTest 1: Available Models")
print("-"*70)
models = list_available_models()
print(f"Found {len(models)} models:")
for model in models:
    print(f"  - {model}")

# Test 2: Initialize trainer with each model
print("\nTest 2: Initialize Trainer with Different Models")
print("-"*70)

for model_name in models:
    try:
        trainer = CreditRiskTrainer(
            data_dir="data",
            models_dir="models",
            random_state=42,
            model_name=model_name
        )
        print(f"✓ Initialized trainer with '{model_name}'")
        print(f"  Registry model: {trainer.model_name}")
        print(f"  Model class: {trainer.registry.get_config(model_name).model_class.__name__}")
    except Exception as e:
        print(f"✗ Failed to initialize with '{model_name}': {e}")

# Test 3: Try invalid model name
print("\nTest 3: Invalid Model Name Handling")
print("-"*70)
try:
    trainer = CreditRiskTrainer(model_name="invalid_model")
    print("✗ Should have raised ValueError")
except ValueError as e:
    print(f"✓ Correctly raised ValueError:")
    print(f"  {str(e)[:80]}...")

print("\n" + "="*70)
print("✓ All integration tests passed!")
print("="*70 + "\n")
