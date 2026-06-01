"""Telemetry provider abstraction."""

from dataclasses import dataclass, field
from typing import Protocol, Sequence

from app.models.cluster import Cluster


@dataclass
class TelemetrySnapshot:
    """Provider-neutral telemetry payload ready for ingestion."""

    metrics: list[dict] = field(default_factory=list)
    logs: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    traces: list[dict] = field(default_factory=list)


class TelemetryProvider(Protocol):
    """Common provider contract for real and simulated observability backends."""

    source_type: str

    def collect(self, clusters: Sequence[Cluster], source_id: str) -> TelemetrySnapshot:
        """Collect telemetry for the supplied persisted infrastructure topology."""
        ...
