"""
NexusOps AI — Cluster & Infrastructure Models
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
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
    DEMO = "demo"
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
    service_count: Mapped[int] = mapped_column(Integer, default=0)
    deployment_count: Mapped[int] = mapped_column(Integer, default=0)
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
    pods: Mapped[list["KubernetesPod"]] = relationship("KubernetesPod", back_populates="cluster", cascade="all, delete-orphan")
    services: Mapped[list["KubernetesService"]] = relationship("KubernetesService", back_populates="cluster", cascade="all, delete-orphan")
    replicasets: Mapped[list["KubernetesReplicaSet"]] = relationship("KubernetesReplicaSet", back_populates="cluster", cascade="all, delete-orphan")


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
    pods: Mapped[list["KubernetesPod"]] = relationship("KubernetesPod", back_populates="namespace")
    services: Mapped[list["KubernetesService"]] = relationship("KubernetesService", back_populates="namespace")
    replicasets: Mapped[list["KubernetesReplicaSet"]] = relationship("KubernetesReplicaSet", back_populates="namespace")


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
    selector: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="workloads")
    namespace: Mapped[Optional["KubernetesNamespace"]] = relationship("KubernetesNamespace", back_populates="workloads")
    pods: Mapped[list["KubernetesPod"]] = relationship("KubernetesPod", back_populates="workload")


class KubernetesReplicaSet(Base, UUIDMixin, TimestampMixin):
    """Represents a Kubernetes ReplicaSet owned by a deployment or another workload."""
    __tablename__ = "kubernetes_replicasets"

    cluster_id: Mapped[str] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    namespace_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("kubernetes_namespaces.id", ondelete="SET NULL"), nullable=True)
    workload_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("kubernetes_workloads.id", ondelete="SET NULL"), nullable=True)
    namespace_name: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_kind: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    owner_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    replicas_desired: Mapped[int] = mapped_column(Integer, default=0)
    replicas_ready: Mapped[int] = mapped_column(Integer, default=0)
    labels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    selector: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="replicasets")
    namespace: Mapped[Optional["KubernetesNamespace"]] = relationship("KubernetesNamespace", back_populates="replicasets")


class KubernetesPod(Base, UUIDMixin, TimestampMixin):
    """Represents a Kubernetes pod and its runtime status."""
    __tablename__ = "kubernetes_pods"

    cluster_id: Mapped[str] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    namespace_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("kubernetes_namespaces.id", ondelete="SET NULL"), nullable=True)
    workload_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("kubernetes_workloads.id", ondelete="SET NULL"), nullable=True)
    namespace_name: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phase: Mapped[str] = mapped_column(String(50), default="Unknown")
    status: Mapped[str] = mapped_column(String(100), default="Unknown")
    node_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pod_ip: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    restart_count: Mapped[int] = mapped_column(Integer, default=0)
    ready: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_kind: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    owner_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    containers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    labels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    annotations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="pods")
    namespace: Mapped[Optional["KubernetesNamespace"]] = relationship("KubernetesNamespace", back_populates="pods")
    workload: Mapped[Optional["KubernetesWorkload"]] = relationship("KubernetesWorkload", back_populates="pods")


class KubernetesService(Base, UUIDMixin, TimestampMixin):
    """Represents a Kubernetes Service and its selected workload surface."""
    __tablename__ = "kubernetes_services"

    cluster_id: Mapped[str] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    namespace_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("kubernetes_namespaces.id", ondelete="SET NULL"), nullable=True)
    namespace_name: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    service_type: Mapped[str] = mapped_column(String(50), default="ClusterIP")
    cluster_ip: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    external_ip: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ports: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    selector: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    labels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    annotations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="services")
    namespace: Mapped[Optional["KubernetesNamespace"]] = relationship("KubernetesNamespace", back_populates="services")
