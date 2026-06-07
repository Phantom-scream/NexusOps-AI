"""Prometheus telemetry provider scaffold.

The provider contract is implemented now so real Prometheus ingestion can be
enabled by configuration without changing service or API consumers.
"""

from collections.abc import Sequence

from app.models.cluster import Cluster
from app.observability.providers.base import TelemetrySnapshot


class PrometheusProvider:
    """Provider placeholder for Prometheus query_range ingestion."""

    source_type = "prometheus"

    def __init__(self, endpoint_url: str | None = None):
        self.endpoint_url = endpoint_url

    def collect(self, clusters: Sequence[Cluster], source_id: str) -> TelemetrySnapshot:
        _ = (clusters, source_id)
        return TelemetrySnapshot()
