"""FastAPI application with strict API versioning discipline.

═══════════════════════════════════════════════════════════════════════
API VERSIONING ARCHITECTURE
═══════════════════════════════════════════════════════════════════════

All public endpoints are served under versioned paths:
- Current: /api/v1/* (stable, production)
- Future: /api/v2/* (when breaking changes needed)

VERSIONING GUARANTEES:
1. Endpoints under /api/v1/ have frozen contracts
2. Breaking changes require new version (v2, v3, etc.)
3. Old versions maintained for minimum 6 months
4. Version header (X-API-Version) on all responses

STABILITY FEATURES:
- Standardized error responses (RFC 7807 inspired)
- Global exception handlers for consistency
- CORS configured for safe cross-origin access
- Structured logging with request tracking

FRONTEND INTEGRATION:
- Base URL: /api/v1/
- camelCase field naming (TypeScript compatibility)
- 10-second timeout requirement honored
- See: PHASE_3A1_CONTRACT_DISCOVERY.md

═══════════════════════════════════════════════════════════════════════
"""

from fastapi import FastAPI, Request
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
import structlog

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.error_handlers import register_error_handlers
from app.api.v1 import v1_router
from app.schemas.errors import APIErrorResponse, ErrorCodes, create_error_response

logger = structlog.get_logger(__name__)

# API Version (frozen contract)
API_VERSION = "v1"

app = FastAPI(
    title=f"{settings.APP_NAME} - API v{API_VERSION}",
    version=settings.APP_VERSION,
    description=(
        "Credit Risk Prediction API with strict versioning discipline.\n\n"
        f"**Current Version:** v{API_VERSION} (stable)\n\n"
        "**Base URL:** `/api/v1/`\n\n"
        "All endpoints are versioned. Breaking changes will increment version number.\n"
        "See `/api/v1/health` for service status."
    ),
    openapi_url=f"/api/{API_VERSION}/openapi.json",
    docs_url=f"/api/{API_VERSION}/docs",
    redoc_url=f"/api/{API_VERSION}/redoc",
)

# ═══════════════════════════════════════════════════════════════════════
# CORS CONFIGURATION (PHASE 3B-1: LOCAL FRONTEND ACCESS)
# ═══════════════════════════════════════════════════════════════════════

# SAFE MODE CORS for local development:
# - Only localhost origins (no wildcard)
# - Only GET/POST methods (no PUT/DELETE/PATCH)
# - Credentials allowed for future cookie-based auth
# - NO production wildcards (*)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Explicit list only
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,  # GET, POST only
    allow_headers=["*"],  # Allow standard headers (Content-Type, Accept)
)

logger.info(
    "cors_enabled",
    origins=settings.CORS_ORIGINS,
    methods=settings.CORS_METHODS,
    environment=settings.ENVIRONMENT,
)

# ═══════════════════════════════════════════════════════════════════════
# API VERSIONING: Centralized Router Registration
# ═══════════════════════════════════════════════════════════════════════
# All v1 endpoints are registered through a single centralized router.
# This enforces versioning discipline and makes version management easier.
# Future versions (v2, v3) will follow the same pattern.

app.include_router(v1_router, prefix="/api/v1")


# ═══════════════════════════════════════════════════════════════════════
# CENTRALIZED ERROR HANDLING
# ═══════════════════════════════════════════════════════════════════════
# Register all error handlers from centralized module.
# This provides consistent error responses with request_id tracking.

register_error_handlers(app)


# ═══════════════════════════════════════════════════════════════════════
# MIDDLEWARE: API Versioning
# ═══════════════════════════════════════════════════════════════════════

@app.middleware("http")
async def add_api_version_header(request: Request, call_next):
    """Add X-API-Version header to all responses for contract tracking.
    
    This header allows frontend to verify API version compatibility.
    """
    response = await call_next(request)
    response.headers["X-API-Version"] = API_VERSION
    return response


# ═══════════════════════════════════════════════════════════════════════
# APPLICATION LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup with production-safe error handling.
    
    Phase 3C-1: Production Hardening
    - Never crashes on missing model files
    - Degrades gracefully to rule-based fallback
    - Validates configuration before starting
    - Provides clear diagnostics
    
    This function:
    1. Configures structured logging
    2. Validates environment configuration
    3. Safely loads ML model (with fallback to rule-based)
    4. Checks SHAP artifact availability (non-critical)
    5. Logs comprehensive startup status
    """
    # Configure logging first
    configure_logging()
    
    logger.info(
        "application_starting",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT
    )
    
    # Perform production-safe startup checks
    from app.core.startup_safety import perform_startup_checks, get_startup_status
    
    try:
        startup_status = perform_startup_checks()
        
        # Log final startup status
        if not startup_status.is_healthy:
            logger.error(
                "startup_unhealthy",
                errors=len(startup_status.errors),
                model_loaded=startup_status.model_loaded
            )
            # Note: We don't crash the app - it stays alive for health checks
        elif startup_status.is_degraded:
            logger.warning(
                "startup_degraded",
                warnings=len(startup_status.errors),
                model_loaded=startup_status.model_loaded,
                shap_available=startup_status.shap_available
            )
        else:
            logger.info(
                "startup_healthy",
                model_loaded=startup_status.model_loaded,
                shap_available=startup_status.shap_available,
                startup_time_ms=f"{startup_status.startup_time_ms:.2f}"
            )
            
    except Exception as e:
        # Ultimate safety net - log but don't crash
        logger.error(
            "startup_checks_exception",
            error=str(e),
            error_type=type(e).__name__,
            message="Application will attempt to continue in degraded mode"
        )
        # App stays alive for diagnostics
