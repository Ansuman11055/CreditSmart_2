from fastapi import FastAPI

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.api.v1.health import router as health_router
from app.api.v1.predict import router as predict_router
from app.api.v1.advisor import router as advisor_router

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.include_router(health_router, prefix="/api/v1")
app.include_router(predict_router, prefix="/api/v1")
app.include_router(advisor_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    configure_logging()
    # lightweight startup log that will appear in structured logs
    import structlog

    structlog.get_logger("app").info("startup", version=settings.APP_VERSION)
