from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.core.config import settings
import time

router = APIRouter()

_START_TIME = time.time()


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health():
    """Stable health endpoint returning status and uptime."""
    uptime = time.time() - _START_TIME
    return HealthResponse(status="ok", uptime=uptime, version=settings.APP_VERSION)
