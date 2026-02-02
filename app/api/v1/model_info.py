"""Model information endpoint for credit risk API.

This endpoint exposes safe model metadata for:
- Frontend display
- Model registry integration
- Audit and compliance tracking
- Operational monitoring
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import structlog

from app.ml.model import get_model
from app.ml.metadata import get_metadata_registry

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/model/info", response_model=Dict[str, Any], tags=["model"])
async def get_model_info() -> Dict[str, Any]:
    """Get comprehensive model metadata and information.
    
    This endpoint returns safe, non-sensitive model information including:
    - Model type and name (e.g., "RandomForest", "credit_risk_model")
    - Training timestamp or git hash
    - Feature count
    - Evaluation metrics (ROC-AUC, Recall, Precision, F1)
    - Framework versions (scikit-learn, xgboost, numpy)
    - Schema version
    
    This endpoint does NOT expose:
    - Training data
    - Model weights or parameters
    - Feature names (security/PII protection)
    - Internal preprocessing logic
    
    Returns:
        Dictionary containing safe model metadata
        
    Raises:
        HTTPException: 500 if model information cannot be retrieved
        
    Example Response:
        ```json
        {
          "model_name": "credit_risk_model",
          "model_type": "RandomForestClassifier",
          "model_version": "ml_v1.0.0",
          "trained_on": "2025-01-15T10:30:00Z",
          "feature_count": 23,
          "framework_versions": {
            "scikit-learn": "1.3.0",
            "numpy": "1.24.3"
          },
          "evaluation_metrics": {
            "roc_auc": 0.85,
            "recall": 0.78,
            "precision": 0.82
          },
          "schema_version": "v1",
          "is_loaded": true,
          "api_version": "v1.0.0"
        }
        ```
    """
    try:
        # Get metadata from registry (fast, no model loading)
        metadata_registry = get_metadata_registry()
        metadata = metadata_registry.get_metadata()
        
        if not metadata:
            # Fallback to model instance if registry failed
            logger.warning("Metadata registry not loaded, querying model instance")
            model = get_model()
            info = model.get_model_info()
        else:
            # Use cached metadata (preferred path)
            info = metadata.to_dict()
            
            # Add model loaded status from actual instance
            try:
                model = get_model()
                info["is_loaded"] = model.is_loaded
            except Exception:
                info["is_loaded"] = False
        
        # Log request for observability
        logger.info(
            "model_info_request",
            model_type=info.get("model_type", "unknown"),
            model_version=info.get("model_version", "unknown"),
            is_loaded=info.get("is_loaded", False),
        )
        
        # Add API version
        info["api_version"] = "v1.0.0"
        
        return info
        
    except Exception as e:
        logger.error("model_info_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model information.",
        )
