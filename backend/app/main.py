"""
NexusOps AI — Backend Application Entry Point
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import configure_logging
from app.core.middleware import RequestIDMiddleware, RateLimitMiddleware
from app.events.kafka_client import kafka_manager
from app.observability.tracing import configure_tracing

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — startup and shutdown lifecycle."""
    # Startup
    logger.info("NexusOps AI starting up", version=settings.APP_VERSION, env=settings.APP_ENV)

    # Initialize database tables (dev only; use Alembic in production)
    if settings.APP_ENV == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Connect Kafka producer
    await kafka_manager.start()

    logger.info("NexusOps AI startup complete")
    yield

    # Shutdown
    logger.info("NexusOps AI shutting down")
    await kafka_manager.stop()
    await engine.dispose()
    logger.info("NexusOps AI shutdown complete")


def create_application() -> FastAPI:
    configure_logging()
    configure_tracing()

    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-Powered Multi-Cloud AIOps & Infrastructure Intelligence Platform",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ----------------------------------------------------------
    # Middleware
    # ----------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # ----------------------------------------------------------
    # Prometheus Metrics
    # ----------------------------------------------------------
    Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics")

    # ----------------------------------------------------------
    # Routers
    # ----------------------------------------------------------
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # ----------------------------------------------------------
    # Global Exception Handler
    # ----------------------------------------------------------
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled exception",
            exc_type=type(exc).__name__,
            exc_msg=str(exc),
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    # ----------------------------------------------------------
    # Health Check
    # ----------------------------------------------------------
    @app.get("/health", tags=["system"])
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        }

    @app.get("/", tags=["system"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    return app


app = create_application()
