"""
NexusOps AI — Structured Logging Configuration
Using structlog with JSON output for production observability
"""
import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from app.core.config import settings


def add_app_context(logger: WrappedLogger, method: str, event_dict: EventDict) -> EventDict:
    """Inject application context into every log entry."""
    event_dict["app"] = settings.APP_NAME
    event_dict["version"] = settings.APP_VERSION
    event_dict["env"] = settings.APP_ENV
    return event_dict


def configure_logging() -> None:
    """Initialize structlog with JSON or human-readable formatting."""
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
    ]

    if settings.LOG_FORMAT == "json":
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Suppress noisy loggers
    for noisy_logger in [
        "uvicorn.access",
        "sqlalchemy.engine",
        "asyncio",
    ]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
