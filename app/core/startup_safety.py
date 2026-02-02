"""Production-safe application startup with graceful degradation.

Phase 3C-1: Production Readiness & System Hardening

This module ensures the application:
- Never crashes on startup due to missing resources
- Degrades gracefully when models are unavailable
- Provides clear diagnostics without exposing internals
- Remains alive and responds to health checks even in degraded mode
"""

import structlog
from pathlib import Path
from typing import Dict, Any, Optional
import sys

logger = structlog.get_logger(__name__)


class StartupError:
    """Represents a non-fatal startup issue."""
    
    def __init__(self, component: str, error: str, severity: str = "warning"):
        self.component = component
        self.error = error
        self.severity = severity
        self.timestamp = None
        
    def to_dict(self) -> Dict[str, str]:
        return {
            "component": self.component,
            "error": self.error,
            "severity": self.severity
        }


class StartupStatus:
    """Tracks application startup status and issues."""
    
    def __init__(self):
        self.is_healthy = True
        self.is_degraded = False
        self.errors: list[StartupError] = []
        self.model_loaded = False
        self.shap_available = False
        self.startup_time_ms: Optional[float] = None
        
    def add_error(self, component: str, error: str, severity: str = "warning"):
        """Add a startup error/warning."""
        startup_error = StartupError(component, error, severity)
        self.errors.append(startup_error)
        
        if severity == "error":
            self.is_degraded = True
        
    def get_status_dict(self) -> Dict[str, Any]:
        """Get status as dictionary for health checks."""
        return {
            "healthy": self.is_healthy,
            "degraded": self.is_degraded,
            "model_loaded": self.model_loaded,
            "shap_available": self.shap_available,
            "errors": [e.to_dict() for e in self.errors]
        }


# Global startup status (singleton)
_startup_status = StartupStatus()


def get_startup_status() -> StartupStatus:
    """Get global startup status."""
    return _startup_status


def verify_model_artifacts(model_dir: str = "models") -> tuple[bool, list[str]]:
    """Verify all required model artifacts exist and are readable.
    
    This function performs explicit checks for production ML inference stability:
    - model.joblib: Main model file (REQUIRED)
    - preprocessor.joblib: Preprocessing pipeline (REQUIRED)
    - shap_explainer.joblib: SHAP explainer (OPTIONAL, for explanations)
    
    Args:
        model_dir: Directory containing model artifacts
        
    Returns:
        Tuple of (success, missing_files)
        - success: True if all required files exist and are readable
        - missing_files: List of missing/unreadable file names
    """
    model_path = Path(model_dir)
    missing_files = []
    
    # Check directory exists
    if not model_path.exists():
        logger.error(
            "artifact_check_failed",
            reason="model_directory_not_found",
            path=str(model_path)
        )
        return False, [f"directory: {model_dir}"]
    
    if not model_path.is_dir():
        logger.error(
            "artifact_check_failed",
            reason="path_is_not_directory",
            path=str(model_path)
        )
        return False, [f"not a directory: {model_dir}"]
    
    # Check required files
    required_files = [
        ("model.joblib", "Main ML model file"),
        ("preprocessor.joblib", "Feature preprocessing pipeline")
    ]
    
    for filename, description in required_files:
        file_path = model_path / filename
        
        if not file_path.exists():
            logger.error(
                "artifact_missing",
                file=filename,
                description=description,
                expected_path=str(file_path)
            )
            missing_files.append(filename)
        elif not file_path.is_file():
            logger.error(
                "artifact_invalid",
                file=filename,
                reason="not_a_file",
                path=str(file_path)
            )
            missing_files.append(f"{filename} (not a file)")
        elif file_path.stat().st_size == 0:
            logger.error(
                "artifact_invalid",
                file=filename,
                reason="empty_file",
                path=str(file_path)
            )
            missing_files.append(f"{filename} (empty)")
        else:
            # File exists and has content
            logger.info(
                "artifact_verified",
                file=filename,
                size_bytes=file_path.stat().st_size,
                path=str(file_path)
            )
    
    # Check optional SHAP file (non-blocking)
    shap_files = [
        "shap_explainer.joblib",
        "shap_explainer_new.joblib"
    ]
    
    shap_found = False
    for shap_file in shap_files:
        shap_path = model_path / shap_file
        if shap_path.exists() and shap_path.is_file() and shap_path.stat().st_size > 0:
            logger.info(
                "shap_artifact_found",
                file=shap_file,
                size_bytes=shap_path.stat().st_size
            )
            shap_found = True
            _startup_status.shap_available = True
            break
    
    if not shap_found:
        logger.info(
            "shap_artifact_not_found",
            message="SHAP explanations will be unavailable (non-critical)",
            checked_files=shap_files
        )
        _startup_status.shap_available = False
    
    # Return success status
    if missing_files:
        return False, missing_files
    
    return True, []


def verify_model_metadata(model_dir: str = "models") -> tuple[bool, Optional[dict]]:
    """Verify model metadata is readable and contains required information.
    
    Args:
        model_dir: Directory containing model artifacts
        
    Returns:
        Tuple of (success, metadata_dict)
        - success: True if metadata is readable
        - metadata_dict: Extracted metadata or None if unreadable
    """
    import joblib
    
    model_path = Path(model_dir) / "model.joblib"
    
    if not model_path.exists():
        logger.error("metadata_check_failed", reason="model_file_missing")
        return False, None
    
    try:
        logger.info("loading_model_metadata", path=str(model_path))
        
        # Load only to check metadata (quick check, doesn't keep in memory)
        artifact = joblib.load(model_path)
        
        if not isinstance(artifact, dict):
            logger.warning(
                "metadata_check_warning",
                reason="legacy_format",
                message="Model uses legacy format without metadata dictionary"
            )
            return True, {"format": "legacy", "has_metadata": False}
        
        # Extract key metadata fields
        metadata = {
            "model_name": artifact.get("model_name", "unknown"),
            "model_class": artifact.get("model_class", "unknown"),
            "schema_version": artifact.get("schema_version", "unknown"),
            "feature_names": artifact.get("feature_names", []),
            "metadata": artifact.get("metadata", {}),
            "has_metadata": True
        }
        
        # Extract training timestamp if available
        training_timestamp = metadata["metadata"].get("training_timestamp", "unknown")
        metadata["training_timestamp"] = training_timestamp
        
        # Log metadata summary
        logger.info(
            "model_metadata_extracted",
            model_name=metadata["model_name"],
            model_class=metadata["model_class"],
            schema_version=metadata["schema_version"],
            feature_count=len(metadata["feature_names"]),
            training_timestamp=training_timestamp
        )
        
        return True, metadata
        
    except Exception as e:
        logger.error(
            "metadata_check_failed",
            error=str(e),
            error_type=type(e).__name__,
            path=str(model_path)
        )
        return False, None


def safe_load_model(model_dir: str = "models") -> tuple[Any, bool]:
    """Safely load ML model with graceful fallback.
    
    This function NEVER raises exceptions. It always returns a model
    instance (even if degraded) and a success flag.
    
    Production ML Inference Stability:
    - Verifies model.joblib exists and is readable
    - Verifies preprocessor.joblib exists and is readable
    - Checks SHAP files (optional, non-blocking)
    - Validates model metadata is readable
    - Fails gracefully with clear structured logs
    - Falls back to rule-based engine if ML artifacts unavailable
    
    Args:
        model_dir: Directory containing model artifacts
        
    Returns:
        Tuple of (model_instance, success_flag)
        - model_instance: Always returns a model (ML or rule-based fallback)
        - success_flag: True if ML model loaded, False if using fallback
    """
    from app.ml.model import CreditRiskModel
    
    logger.info("startup_model_loading_begin", model_dir=model_dir)
    
    # STEP 1: Verify all model artifacts exist and are readable
    logger.info("startup_check_artifacts", step="verify_files")
    artifacts_ok, missing_files = verify_model_artifacts(model_dir)
    
    if not artifacts_ok:
        logger.error(
            "startup_artifacts_missing",
            missing_files=missing_files,
            model_dir=model_dir,
            action="falling_back_to_rule_based"
        )
        _startup_status.add_error(
            "model_loader",
            f"Required model artifacts missing: {', '.join(missing_files)}",
            "warning"
        )
        
        # Return rule-based fallback
        try:
            logger.info("loading_fallback_rule_engine")
            model = CreditRiskModel(use_ml_model=False)
            _startup_status.model_loaded = False
            logger.info("fallback_rule_engine_loaded_successfully")
            return model, False
        except Exception as e:
            logger.error(
                "rule_engine_fallback_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            _startup_status.add_error(
                "rule_engine",
                f"Fallback engine failed: {str(e)}",
                "error"
            )
            _startup_status.is_healthy = False
            return None, False
    
    # STEP 2: Verify model metadata is readable
    logger.info("startup_check_metadata", step="verify_metadata")
    metadata_ok, metadata = verify_model_metadata(model_dir)
    
    if not metadata_ok:
        logger.warning(
            "startup_metadata_unreadable",
            model_dir=model_dir,
            message="Model metadata could not be read, but continuing with model load"
        )
        _startup_status.add_error(
            "metadata_loader",
            "Model metadata is unreadable or corrupted",
            "warning"
        )
        # Continue anyway - metadata is not critical for model execution
    
    # STEP 3: Try to load ML model
    try:
        logger.info("startup_loading_ml_model", model_dir=model_dir)
        model = CreditRiskModel(model_path=str(model_dir), use_ml_model=True)
        
        if model.is_loaded and model.ml_engine is not None:
            logger.info(
                "startup_ml_model_loaded_successfully",
                model_type="ml",
                shap_available=_startup_status.shap_available
            )
            _startup_status.model_loaded = True
            
            return model, True
        else:
            # ML loading failed, should have fallen back to rule-based
            logger.warning(
                "startup_ml_load_failed_using_fallback",
                reason="model_initialization_incomplete"
            )
            _startup_status.model_loaded = False
            return model, False
            
    except Exception as e:
        logger.error(
            "startup_ml_model_load_exception",
            error=str(e),
            error_type=type(e).__name__,
            action="falling_back_to_rule_based"
        )
        _startup_status.add_error(
            "model_loader",
            f"ML model load failed: {type(e).__name__} - {str(e)}",
            "warning"
        )
        
        # Final fallback to rule-based
        try:
            logger.info("loading_final_fallback_rule_engine")
            model = CreditRiskModel(use_ml_model=False)
            _startup_status.model_loaded = False
            logger.info("final_fallback_rule_engine_loaded_successfully")
            return model, False
        except Exception as fallback_error:
            logger.error(
                "startup_all_model_loading_failed",
                error=str(fallback_error),
                error_type=type(fallback_error).__name__,
                message="NO MODEL AVAILABLE - SERVICE IN CRITICAL STATE"
            )
            _startup_status.add_error(
                "model_loader",
                "All model loading attempts failed (ML and rule-based)",
                "error"
            )
            _startup_status.is_healthy = False
            return None, False


def validate_required_config() -> bool:
    """Validate that all required configuration is present.
    
    Returns:
        True if all required config is valid, False otherwise
    """
    from app.core.config import settings
    
    required_checks = []
    
    # Check APP_NAME
    if not settings.APP_NAME or settings.APP_NAME == "":
        logger.error("config_validation_failed", field="APP_NAME", reason="empty")
        _startup_status.add_error("config", "APP_NAME is required", "error")
        required_checks.append(False)
    else:
        required_checks.append(True)
    
    # Check ENVIRONMENT is valid
    valid_environments = ["development", "staging", "production"]
    if settings.ENVIRONMENT not in valid_environments:
        logger.warning(
            "config_validation_warning",
            field="ENVIRONMENT",
            value=settings.ENVIRONMENT,
            allowed=valid_environments
        )
        _startup_status.add_error(
            "config",
            f"ENVIRONMENT '{settings.ENVIRONMENT}' not in {valid_environments}",
            "warning"
        )
    
    # Check CORS origins
    if not settings.CORS_ORIGINS or len(settings.CORS_ORIGINS) == 0:
        logger.warning(
            "config_validation_warning",
            field="CORS_ORIGINS",
            reason="no origins configured"
        )
        _startup_status.add_error(
            "config",
            "No CORS origins configured (API may not be accessible from frontend)",
            "warning"
        )
    
    # Check for wildcard CORS in production
    if settings.ENVIRONMENT == "production":
        if "*" in settings.CORS_ORIGINS:
            logger.error(
                "config_validation_failed",
                field="CORS_ORIGINS",
                reason="wildcard not allowed in production"
            )
            _startup_status.add_error(
                "config",
                "Wildcard CORS origin not allowed in production",
                "error"
            )
            required_checks.append(False)
        else:
            required_checks.append(True)
    
    # Check log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if settings.LOG_LEVEL.upper() not in valid_log_levels:
        logger.warning(
            "config_validation_warning",
            field="LOG_LEVEL",
            value=settings.LOG_LEVEL,
            allowed=valid_log_levels
        )
        _startup_status.add_error(
            "config",
            f"LOG_LEVEL '{settings.LOG_LEVEL}' not in {valid_log_levels}",
            "warning"
        )
    
    all_required_valid = all(required_checks)
    
    if not all_required_valid:
        logger.error("config_validation_failed", message="Required configuration is invalid")
        _startup_status.is_healthy = False
    
    return all_required_valid


def perform_startup_checks() -> StartupStatus:
    """Perform all startup checks in sequence.
    
    This function is designed to be called during application startup.
    It NEVER raises exceptions - all errors are captured and logged.
    
    Returns:
        StartupStatus object with complete diagnostics
    """
    import time
    start_time = time.time()
    
    logger.info("startup_checks_begin")
    
    # 1. Validate configuration
    logger.info("checking_configuration")
    config_valid = validate_required_config()
    
    if not config_valid:
        logger.error("startup_checks_failed", reason="invalid_configuration")
        _startup_status.startup_time_ms = (time.time() - start_time) * 1000
        return _startup_status
    
    # 2. Load model (with graceful degradation)
    logger.info("loading_model")
    model, ml_loaded = safe_load_model()
    
    if model is None:
        logger.error("startup_checks_failed", reason="no_model_available")
        _startup_status.is_healthy = False
        _startup_status.startup_time_ms = (time.time() - start_time) * 1000
        return _startup_status
    
    # 3. Store model in singleton (for get_model())
    from app.ml.model import set_model_instance
    set_model_instance(model)
    
    # Log final status
    elapsed_ms = (time.time() - start_time) * 1000
    _startup_status.startup_time_ms = elapsed_ms
    
    if _startup_status.is_degraded:
        logger.warning(
            "startup_complete_degraded",
            time_ms=f"{elapsed_ms:.2f}",
            model_type="rule_based" if not ml_loaded else "ml",
            errors=len(_startup_status.errors)
        )
    else:
        logger.info(
            "startup_complete_healthy",
            time_ms=f"{elapsed_ms:.2f}",
            model_type="ml" if ml_loaded else "rule_based",
            shap_available=_startup_status.shap_available
        )
    
    return _startup_status
