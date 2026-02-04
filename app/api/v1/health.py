"""Health check endpoint - API v1.

═══════════════════════════════════════════════════════════════════════
ENDPOINT: GET /api/v1/health
═══════════════════════════════════════════════════════════════════════

API Version: v1 (stable)
Status: Production
Contract: Frozen (no breaking changes)

Production health check with enhanced observability:
- Fast response (<100ms target)
- Model loaded status (bool)
- Service uptime tracking
- API version tracking
- Schema version metadata
- Overall service health indicator

USAGE:
  GET /api/v1/health
  
  Response:
  {
    "service_status": "ok" | "degraded",
    "api_version": "v1",
    "model_loaded": true,
    "model_version": "ml_v1.0.0",
    "schema_version": "1.0.0",
    "uptime_seconds": 123.45,
    "app_version": "0.1.0"
  }

MONITORING:
- Kubernetes liveness probe
- Prometheus health check scraping
- Load balancer health checks
- CI/CD deployment validation

═══════════════════════════════════════════════════════════════════════
"""

from fastapi import APIRouter
from fastapi import status as http_status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Literal
import time
import structlog

from app.core.config import settings
from app.ml.model import get_model
from app.ml.metadata import get_metadata_registry

router = APIRouter()
logger = structlog.get_logger(__name__)

_START_TIME = time.time()

# API version for contract tracking
API_VERSION = "v1"


class HealthResponse(BaseModel):
    """Enhanced health response with model status and API version.
    
    Phase 3B-2: Enriched health check for frontend integration.
    
    This response includes operational metrics for observability
    and monitoring tools (e.g., Kubernetes, Prometheus, Datadog).
    
    New fields (Phase 3B-2):
    - api_version: API contract version (v1)
    - model_loaded: Boolean flag for quick model status check
    - uptime_seconds: Time since service started
    """
    
    service_status: Literal["ok", "degraded"] = Field(
        description="Overall service health. 'ok' if fully operational, 'degraded' if model not loaded."
    )
    
    api_version: str = Field(
        description="API version for contract tracking (e.g., 'v1')."
    )
    
    model_loaded: bool = Field(
        description="Whether ML model is loaded and ready for predictions."
    )
    
    model_version: str = Field(
        description="Version of loaded ML model (e.g., 'ml_v1.0.0')."
    )
    
    schema_version: str = Field(
        description="API schema version for request/response contracts."
    )
    
    uptime_seconds: float = Field(
        description="Time in seconds since service started."
    )
    
    app_version: str = Field(
        description="Application version."
    )


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Fast health check endpoint (<100ms response time).
    
    Phase 3B-2: Enriched with API version, model_loaded bool, and uptime.
    
    This endpoint checks service health WITHOUT loading or reloading
    the model. It queries cached metadata for fast responses.
    
    Returns:
        HealthResponse with service and model status
        
    Response Codes:
        - 200: Service is healthy (always returns 200)
        - service_status="ok": Model loaded and ready
        - service_status="degraded": Service running but model not loaded
        
    Example:
        ```
        GET /api/v1/health
        
        {
          "service_status": "ok",
          "api_version": "v1",
          "model_loaded": true,
          "model_version": "ml_v1.0.0",
          "schema_version": "v1",
          "uptime_seconds": 123.45,
          "app_version": "1.0.0"
        }
        ```
    """
    uptime = time.time() - _START_TIME
    
    # Check model status (fast, uses cached instance)
    try:
        model = get_model()
        model_loaded = model.is_loaded
        
        # Get model version from metadata registry (no model loading)
        metadata_registry = get_metadata_registry()
        metadata = metadata_registry.get_metadata()
        
        if metadata:
            model_version = metadata.model_version
            schema_version = metadata.schema_version
        else:
            model_version = "unknown"
            schema_version = "v1"
        
        # Determine service status
        service_status: Literal["ok", "degraded"] = "ok" if model_loaded else "degraded"
        
    except Exception:
        # If model check fails, service is degraded but still responding
        model_loaded = False
        model_version = "unknown"
        schema_version = "v1"
        service_status = "degraded"
    
    return HealthResponse(
        service_status=service_status,
        api_version=API_VERSION,
        model_loaded=model_loaded,
        model_version=model_version,
        schema_version=schema_version,
        uptime_seconds=round(uptime, 2),
        app_version=settings.APP_VERSION,
    )


@router.get("/ready", response_model=HealthResponse, tags=["health"])
def readiness_check() -> JSONResponse:
    """Readiness check endpoint for Kubernetes readiness probes.
    
    Phase 3E: Production Readiness
    - Returns 200 only if model is loaded and ready
    - Returns 503 if service is not ready for traffic
    - Faster than /health (no metadata lookups)
    
    Kubernetes Usage:
    -----------------
        readinessProbe:
          httpGet:
            path: /api/v1/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          failureThreshold: 3
    
    Load Balancer:
    --------------
    Use this endpoint to determine if instance should receive traffic.
    If /ready returns 503, route traffic to other instances.
    
    Returns:
        JSONResponse with HealthResponse schema
        
    Response Codes:
        - 200: Service ready for traffic (model loaded)
        - 503: Service not ready (model not loaded or cache unavailable)
    """
    uptime = time.time() - _START_TIME
    
    try:
        # Check model is loaded and ready
        model = get_model()
        model_loaded = model.is_loaded
        
        # Check cache is available (Phase 3E)
        from app.core.prediction_cache import get_prediction_cache
        cache = get_prediction_cache()
        cache_ready = cache is not None
        
        # Service is ready only if model is loaded AND cache is available
        is_ready = model_loaded and cache_ready
        
        # Get model version
        metadata_registry = get_metadata_registry()
        metadata = metadata_registry.get_metadata()
        
        if metadata:
            model_version = metadata.model_version
            schema_version = metadata.schema_version
        else:
            model_version = "unknown"
            schema_version = "v1"
        
        if not is_ready:
            # Return 503 Service Unavailable
            response_data = HealthResponse(
                service_status="degraded",
                api_version=API_VERSION,
                model_loaded=model_loaded,
                model_version=model_version,
                schema_version=schema_version,
                uptime_seconds=round(uptime, 2),
                app_version=settings.APP_VERSION,
            )
            return JSONResponse(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response_data.model_dump()
            )
        
        # Service is ready - return 200
        return HealthResponse(
            service_status="ok",
            api_version=API_VERSION,
            model_loaded=model_loaded,
            model_version=model_version,
            schema_version=schema_version,
            uptime_seconds=round(uptime, 2),
            app_version=settings.APP_VERSION,
        )
        
    except Exception as e:
        # Service not ready - return 503
        logger.error(
            "readiness_check_failed",
            error=str(e),
            exception_type=type(e).__name__
        )
        
        response_data = HealthResponse(
            service_status="degraded",
            api_version=API_VERSION,
            model_loaded=False,
            model_version="unknown",
            schema_version="v1",
            uptime_seconds=round(uptime, 2),
            app_version=settings.APP_VERSION,
        )
        return JSONResponse(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response_data.model_dump()
        )
