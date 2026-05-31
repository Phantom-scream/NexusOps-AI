"""
NexusOps AI — Observability & Tracing Configuration
OpenTelemetry setup with OTLP export
"""
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    _OTEL_AVAILABLE = True
except Exception:
    _OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry not available, tracing disabled")


def configure_tracing() -> None:
    """Initialize OpenTelemetry distributed tracing."""
    if not _OTEL_AVAILABLE:
        logger.warning("Skipping tracing configuration — OpenTelemetry unavailable")
        return

    resource = Resource.create({
        "service.name": settings.OTEL_SERVICE_NAME,
        "service.version": settings.APP_VERSION,
        "deployment.environment": settings.APP_ENV,
    })

    provider = TracerProvider(resource=resource)

    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
                insecure=True,
            )
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info("OTLP tracing configured", endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
        except Exception as exc:
            logger.warning("OTLP exporter setup failed, using console", error=str(exc))
            if settings.APP_DEBUG:
                provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument()
    logger.info("OpenTelemetry tracing initialized", service=settings.OTEL_SERVICE_NAME)


def get_tracer(name: str = __name__):
    if not _OTEL_AVAILABLE:
        return None
    return trace.get_tracer(name)
