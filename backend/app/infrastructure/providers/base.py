"""Provider abstraction for infrastructure discovery."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class InfrastructureSnapshot:
    """Normalized infrastructure snapshot emitted by every provider."""

    cluster: dict[str, Any]
    nodes: list[dict[str, Any]] = field(default_factory=list)
    namespaces: list[dict[str, Any]] = field(default_factory=list)
    deployments: list[dict[str, Any]] = field(default_factory=list)
    workloads: list[dict[str, Any]] = field(default_factory=list)
    replicasets: list[dict[str, Any]] = field(default_factory=list)
    pods: list[dict[str, Any]] = field(default_factory=list)
    services: list[dict[str, Any]] = field(default_factory=list)


class InfrastructureProvider(ABC):
    """Base class for Kubernetes, local, and demo infrastructure providers."""

    source: str

    @abstractmethod
    def discover(self) -> InfrastructureSnapshot:
        """Return a complete normalized infrastructure snapshot."""
