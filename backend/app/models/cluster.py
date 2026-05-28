"""
NexusOps AI — Cluster & Infrastructure Models
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class ClusterStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class ClusterProvider(str, Enum):
    AWS_EKS = "aws_eks"
    GCP_GKE = "gcp_gke"
    AZURE_AKS = "azure_aks"
    OPENSHIFT = "openshift"
    VANILLA = "vanilla"
    MINIKUBE = "minikube"
    KIND = "kind"
    OTHER = "other"


class Cluster(Base, UUIDMixin, TimestampMixin):
    """Represents a registered Kubernetes cluster."""
    __tablename__ = "clusters"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default=ClusterProvider.VANILLA)
    status: Mapped[str] = mapped_column(String(50), default=ClusterStatus.UNKNOWN)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    environment: Mapped[str] = mapped_column(String(50), default="production")
    api_server_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    kubernetes_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    node_count: Mapped[int] = mapped_column(Integer, default=0)
    namespace_count: Mapped[int] = mapped_column(Integer, default=0)
    pod_count: Mapped[int] = mapped_column(Integer, default=0)
    cpu_capacity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_capacity_gb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True, default=dict)

    # Relationships
    nodes: Mapped[list["ClusterNode"]] = relationship("ClusterNode", back_populates="cluster", cascade="all, delete-orphan")
    namespaces: Mapped[list["KubernetesNamespace"]] = relationship("KubernetesNamespace", back_populates="cluster", cascade="all, delete-orphan")
    workloads: Mapped[list["KubernetesWorkload"]] = relationship("KubernetesWorkload", back_populates="cluster", cascade="all, delete-orphan")


class ClusterNode(Base, UUIDMixin, TimestampMixin):
    """Represents a Kubernetes node within a cluster."""
    __tablename__ = "cluster_nodes"

    cluster_id: Mapped[str] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Ready")
    role: Mapped[str] = mapped_column(String(50), default="worker")
    kubernetes_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    os_image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    container_runtime: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cpu_allocatable: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_allocatable_gb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_usage_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    conditions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    labels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="nodes")


class KubernetesNamespace(Base, UUIDMixin, TimestampMixin):
    """Represents a Kubernetes namespace."""
    __tablename__ = "kubernetes_namespaces"

    cluster_id: Mapped[str] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Active")
    labels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    annotations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    resource_quota: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="namespaces")
    workloads: Mapped[list["KubernetesWorkload"]] = relationship("KubernetesWorkload", back_populates="namespace")


class KubernetesWorkload(Base, UUIDMixin, TimestampMixin):
    """Represents a Kubernetes workload (Deployment, StatefulSet, DaemonSet, etc.)."""
    __tablename__ = "kubernetes_workloads"

    cluster_id: Mapped[str] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    namespace_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("kubernetes_namespaces.id", ondelete="SET NULL"), nullable=True)
    namespace_name: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # Deployment, StatefulSet, etc.
    replicas_desired: Mapped[int] = mapped_column(Integer, default=1)
    replicas_ready: Mapped[int] = mapped_column(Integer, default=0)
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cpu_request_millicores: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    memory_request_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cpu_limit_millicores: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    memory_limit_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_usage_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    labels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    annotations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    manifest: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="workloads")
    namespace: Mapped[Optional["KubernetesNamespace"]] = relationship("KubernetesNamespace", back_populates="workloads")
