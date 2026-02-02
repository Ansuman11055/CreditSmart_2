"""System information endpoint - API v1.

═══════════════════════════════════════════════════════════════════════
ENDPOINT: GET /api/v1/system/info
═══════════════════════════════════════════════════════════════════════

API Version: v1 (stable)
Status: Production
Purpose: ML Inference Stability & Observability

Provides critical system information for production monitoring:
- Model version and training timestamp
- Artifact verification status
- System uptime and health
- Feature schema information

USAGE:
  GET /api/v1/system/info
  
  Response:
  {
    "service_name": "CreditSmart API",
    "api_version": "v1",
    "app_version": "1.0.0",
    "uptime_seconds": 12345.67,
    "model": {
      "model_name": "credit_risk_model",
      "model_type": "RandomForest",
      "model_version": "ml_v1.0.0",
      "training_timestamp": "2024-01-15T10:30:00Z",
      "is_loaded": true,
      "engine": "ml" | "rule_based",
      "feature_count": 11,
      "schema_version": "v1"
    },
    "artifacts": {
      "model_file_present": true,
      "preprocessor_present": true,
      "shap_explainer_present": true
    },
    "startup": {
      "healthy": true,
      "degraded": false,
      "errors": []
    }
  }

MONITORING USE CASES:
- Verify correct model version is deployed
- Check model training timestamp (for audit trails)
- Monitor artifact availability
- Detect degraded mode (rule-based fallback)
- Validate feature schema alignment

═══════════════════════════════════════════════════════════════════════
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any, Optional
import time
import structlog
from pathlib import Path

from app.core.config import settings
from app.ml.model import get_model
from app.ml.metadata import get_metadata_registry
from app.core.startup_safety import get_startup_status

router = APIRouter()
logger = structlog.get_logger(__name__)

_START_TIME = time.time()

# API version for contract tracking
API_VERSION = "v1"


class ModelInfo(BaseModel):
    """Model information subschema."""
    
    model_name: str = Field(
        description="Human-readable model name"
    )
    
    model_type: str = Field(
        description="Model algorithm type (e.g., RandomForest, XGBoost, rule_based)"
    )
    
    model_version: str = Field(
        description="Model version identifier (e.g., ml_v1.0.0)"
    )
    
    training_timestamp: str = Field(
        description="ISO 8601 timestamp when model was trained, or 'N/A' for rule-based"
    )
    
    is_loaded: bool = Field(
        description="Whether the model is successfully loaded in memory"
    )
    
    engine: Literal["ml", "rule_based"] = Field(
        description="Type of inference engine in use"
    )
    
    feature_count: int = Field(
        description="Number of input features expected by the model"
    )
    
    schema_version: str = Field(
        description="Schema version for API contracts"
    )
    
    evaluation_metrics: Optional[Dict[str, float]] = Field(
        default=None,
        description="Model evaluation metrics (if available)"
    )


class ArtifactsInfo(BaseModel):
    """Model artifacts availability information."""
    
    model_file_present: bool = Field(
        description="Whether model.joblib file is present and readable"
    )
    
    preprocessor_present: bool = Field(
        description="Whether preprocessor.joblib file is present and readable"
    )
    
    shap_explainer_present: bool = Field(
        description="Whether SHAP explainer artifacts are present (optional)"
    )


class StartupInfo(BaseModel):
    """Startup status information."""
    
    healthy: bool = Field(
        description="True if all required components loaded successfully"
    )
    
    degraded: bool = Field(
        description="True if service is running in degraded mode (e.g., rule-based fallback)"
    )
    
    errors: List[Dict[str, str]] = Field(
        description="List of startup errors/warnings with component and severity"
    )


class SystemInfoResponse(BaseModel):
    """Complete system information response.
    
    Provides comprehensive system status for monitoring and observability.
    """
    
    service_name: str = Field(
        description="Name of the service"
    )
    
    api_version: str = Field(
        description="API version (v1, v2, etc.)"
    )
    
    app_version: str = Field(
        description="Application version"
    )
    
    environment: str = Field(
        description="Deployment environment (development, staging, production)"
    )
    
    uptime_seconds: float = Field(
        description="Service uptime in seconds since last restart"
    )
    
    model: ModelInfo = Field(
        description="Detailed model information"
    )
    
    artifacts: ArtifactsInfo = Field(
        description="Model artifact availability status"
    )
    
    startup: StartupInfo = Field(
        description="Startup status and error information"
    )


def check_artifact_presence(model_dir: str = "models") -> ArtifactsInfo:
    """Check which model artifacts are present on disk.
    
    Args:
        model_dir: Directory containing model artifacts
        
    Returns:
        ArtifactsInfo with presence status of each artifact
    """
    model_path = Path(model_dir)
    
    model_file = model_path / "model.joblib"
    preprocessor_file = model_path / "preprocessor.joblib"
    
    # Check multiple SHAP file options
    shap_files = [
        model_path / "shap_explainer.joblib",
        model_path / "shap_explainer_new.joblib"
    ]
    
    shap_present = any(
        f.exists() and f.is_file() and f.stat().st_size > 0
        for f in shap_files
    )
    
    return ArtifactsInfo(
        model_file_present=(
            model_file.exists() and 
            model_file.is_file() and 
            model_file.stat().st_size > 0
        ),
        preprocessor_present=(
            preprocessor_file.exists() and 
            preprocessor_file.is_file() and 
            preprocessor_file.stat().st_size > 0
        ),
        shap_explainer_present=shap_present
    )


@router.get("/system/info", response_model=SystemInfoResponse, tags=["system"])
def get_system_info() -> SystemInfoResponse:
    """Get comprehensive system and model information.
    
    This endpoint provides detailed information about the deployed model,
    system status, and artifact availability. Use this for:
    
    - Verifying correct model version in production
    - Monitoring model training timestamps (audit trail)
    - Detecting degraded mode (rule-based fallback)
    - Validating artifact availability
    - Tracking system uptime
    
    Returns:
        SystemInfoResponse with complete system information
        
    Response Codes:
        - 200: Always returns 200 (even in degraded mode)
        
    Example:
        ```
        GET /api/v1/system/info
        
        {
          "service_name": "CreditSmart API",
          "api_version": "v1",
          "app_version": "1.0.0",
          "environment": "production",
          "uptime_seconds": 12345.67,
          "model": {
            "model_name": "credit_risk_model",
            "model_type": "RandomForest",
            "model_version": "ml_v1.0.0",
            "training_timestamp": "2024-01-15T10:30:00Z",
            "is_loaded": true,
            "engine": "ml",
            "feature_count": 11,
            "schema_version": "v1"
          },
          "artifacts": {
            "model_file_present": true,
            "preprocessor_present": true,
            "shap_explainer_present": true
          },
          "startup": {
            "healthy": true,
            "degraded": false,
            "errors": []
          }
        }
        ```
    """
    uptime = time.time() - _START_TIME
    
    # Get model information
    try:
        model = get_model()
        model_info_dict = model.get_model_info()
        
        # Extract training timestamp from metadata
        training_timestamp = model_info_dict.get("training_timestamp", "unknown")
        
        # Get evaluation metrics if available
        evaluation_metrics = model_info_dict.get("evaluation_metrics")
        
        model_info = ModelInfo(
            model_name=model_info_dict.get("model_name", "unknown"),
            model_type=model_info_dict.get("model_type", "unknown"),
            model_version=model_info_dict.get("model_version", "unknown"),
            training_timestamp=training_timestamp,
            is_loaded=model_info_dict.get("is_loaded", False),
            engine=model_info_dict.get("engine", "rule_based"),
            feature_count=model_info_dict.get("feature_count", 0),
            schema_version=model_info_dict.get("schema_version", "unknown"),
            evaluation_metrics=evaluation_metrics
        )
        
    except Exception as e:
        logger.error(
            "system_info_model_check_failed",
            error=str(e),
            error_type=type(e).__name__
        )
        
        # Return minimal info if model check fails
        model_info = ModelInfo(
            model_name="unknown",
            model_type="unknown",
            model_version="unknown",
            training_timestamp="N/A",
            is_loaded=False,
            engine="rule_based",
            feature_count=0,
            schema_version="unknown",
            evaluation_metrics=None
        )
    
    # Check artifact presence
    artifacts_info = check_artifact_presence()
    
    # Get startup status
    startup_status = get_startup_status()
    startup_info = StartupInfo(
        healthy=startup_status.is_healthy,
        degraded=startup_status.is_degraded,
        errors=[e.to_dict() for e in startup_status.errors]
    )
    
    return SystemInfoResponse(
        service_name=settings.APP_NAME,
        api_version=API_VERSION,
        app_version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=round(uptime, 2),
        model=model_info,
        artifacts=artifacts_info,
        startup=startup_info
    )
