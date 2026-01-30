import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """Configure structured JSON logging (structlog + stdlib).

    This function is idempotent and safe to call on startup.
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.format_exc_info,
            timestamper,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )
