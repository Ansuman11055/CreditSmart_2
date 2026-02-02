"""API v1 - Stable production endpoints with frozen contracts.

═══════════════════════════════════════════════════════════════════════
API VERSION 1 (STABLE)
═══════════════════════════════════════════════════════════════════════

Release Date: February 1, 2026
Status: STABLE (Production)
Deprecation: None planned

CONTRACT GUARANTEES:
- Request/response schemas are frozen
- Field names will not change (camelCase for frontend compatibility)
- Field types will not change
- Required fields will remain required
- Breaking changes will trigger v2 (not modify v1)

ENDPOINTS:
├── /api/v1/health          - Health check with model status
├── /api/v1/predict         - Full ML prediction (11 fields)
├── /api/v1/risk-analysis   - Frontend adapter (5 fields)
├── /api/v1/advisor         - Financial advice generation
└── /api/v1/model/info      - Model metadata

MODULES:
├── health.py        - Health check endpoint
├── predict.py       - ML prediction endpoints (UX-safe responses)
├── risk_analysis.py - Frontend-compatible adapter endpoint
├── advisor.py       - Financial advisory endpoint
├── model_info.py    - Model metadata endpoint
└── __init__.py      - This file (centralized router)

VERSIONING RULES:
1. All v1 endpoints maintain backward compatibility
2. New optional fields allowed (default values required)
3. New endpoints can be added to v1
4. Breaking changes (field removals, renames, type changes) → v2

FRONTEND INTEGRATION:
- TypeScript interfaces match Pydantic schemas exactly
- camelCase field naming convention
- See: PHASE_3A1_CONTRACT_DISCOVERY.md

═══════════════════════════════════════════════════════════════════════
"""

from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.predict import router as predict_router
from app.api.v1.advisor import router as advisor_router
from app.api.v1.model_info import router as model_info_router
from app.api.v1.risk_analysis import router as risk_analysis_router
from app.api.v1.system_info import router as system_info_router

# Centralized v1 router - all v1 endpoints included here
v1_router = APIRouter()
v1_router.include_router(health_router, tags=["health"])
v1_router.include_router(predict_router, tags=["prediction"])
v1_router.include_router(advisor_router, tags=["advisor"])
v1_router.include_router(model_info_router, tags=["model"])
v1_router.include_router(risk_analysis_router, tags=["frontend-adapter"])
v1_router.include_router(system_info_router, tags=["system"])

__all__ = ["v1_router"]
