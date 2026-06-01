"""OpenTelemetry provider scaffold for trace ingestion."""

from typing import Sequence

from app.models.cluster import Cluster
from app.observability.providers.base import TelemetrySnapshot


class OpenTelemetryProvider:
    """Provider placeholder for OTLP trace ingestion pipelines."""

    source_type = "opentelemetry"

    def __init__(self, endpoint_url: str | None = None):
        self.endpoint_url = endpoint_url

    def collect(self, clusters: Sequence[Cluster], source_id: str) -> TelemetrySnapshot:
        _ = (clusters, source_id)
        return TelemetrySnapshot()
