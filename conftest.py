"""Global pytest configuration for CreditSmart backend.

This file sets up fixtures that run for all tests, ensuring:
1. Model is properly initialized before tests run
2. Test isolation is maintained
3. Consistent test environment

Phase 3C-1: Production Hardening
The model now requires explicit initialization (no lazy loading).
Tests must initialize the model before using prediction endpoints.
"""

import pytest
from app.ml.model import CreditRiskModel, set_model_instance


@pytest.fixture(scope="session", autouse=True)
def initialize_model():
    """Initialize ML model once per test session.
    
    This fixture runs automatically for all tests (autouse=True).
    It ensures the model singleton is initialized before any test
    attempts to use prediction endpoints.
    
    Scope: session (runs once per pytest session, not per test)
    
    Note:
        Phase 3C-1 changed model loading from lazy to explicit.
        Tests require this fixture to avoid RuntimeError on model access.
    """
    # Initialize model for all tests
    model = CreditRiskModel()
    set_model_instance(model)
    
    yield model
    
    # Cleanup: Reset model instance after all tests complete
    # This ensures tests don't interfere with each other across sessions
    from app.ml.model import _reset_model_instance
    try:
        _reset_model_instance()
    except AttributeError:
        # Function doesn't exist yet, that's ok
        pass
