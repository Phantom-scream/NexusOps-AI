"""
NexusOps AI — Cluster Pydantic Schemas
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ClusterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    provider: str = "vanilla"
    region: str | None = None
    environment: str = "production"
    api_server_url: str | None = None
    tags: dict | None = None


class ClusterCreate(ClusterBase):
    pass


class ClusterUpdate(BaseModel):
    display_name: str | None = None
    provider: str | None = None
    region: str | None = None
    environment: str | None = None
    tags: dict | None = None
    is_active: bool | None = None


class ClusterNodeOut(BaseModel):
    id: str
    name: str
    status: str
    role: str
    kubernetes_version: str | None
    os_image: str | None
    cpu_allocatable: float | None
    memory_allocatable_gb: float | None
    cpu_usage_percent: float | None
    memory_usage_percent: float | None

    model_config = {"from_attributes": True}


class ClusterOut(BaseModel):
    id: str
    name: str
    display_name: str
    provider: str
    status: str
    region: str | None
    environment: str
    kubernetes_version: str | None
    node_count: int
    namespace_count: int
    pod_count: int
    service_count: int = 0
    deployment_count: int = 0
    cpu_capacity: float | None
    memory_capacity_gb: float | None
    is_active: bool
    last_sync_at: datetime | None
    tags: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClusterDetailOut(ClusterOut):
    nodes: list[ClusterNodeOut] = []
    api_server_url: str | None


class ClusterListResponse(BaseModel):
    items: list[ClusterOut]
    total: int
    page: int
    page_size: int


class WorkloadOut(BaseModel):
    id: str
    cluster_id: str
    namespace_name: str
    name: str
    kind: str
    replicas_desired: int
    replicas_ready: int
    image: str | None
    selector: dict | None = None
    cpu_request_millicores: int | None
    memory_request_mb: int | None
    cpu_usage_percent: float | None
    memory_usage_percent: float | None
    is_healthy: bool
    labels: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NamespaceOut(BaseModel):
    id: str
    cluster_id: str
    name: str
    status: str
    labels: dict | None
    annotations: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PodOut(BaseModel):
    id: str
    cluster_id: str
    namespace_name: str
    name: str
    phase: str
    status: str
    node_name: str | None
    pod_ip: str | None
    restart_count: int
    ready: bool
    owner_kind: str | None
    owner_name: str | None
    containers: Any | None
    labels: dict | None
    started_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ServiceOut(BaseModel):
    id: str
    cluster_id: str
    namespace_name: str
    name: str
    service_type: str
    cluster_ip: str | None
    external_ip: str | None
    ports: Any | None
    selector: dict | None
    labels: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReplicaSetOut(BaseModel):
    id: str
    cluster_id: str
    namespace_name: str
    name: str
    owner_kind: str | None
    owner_name: str | None
    replicas_desired: int
    replicas_ready: int
    labels: dict | None
    selector: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TopologyNode(BaseModel):
    id: str
    name: str
    type: str
    status: str | None = None
    metadata: dict = Field(default_factory=dict)
    children: list["TopologyNode"] = Field(default_factory=list)


class ClusterTopologyOut(BaseModel):
    cluster_id: str
    generated_at: datetime
    root: TopologyNode


class SyncResponse(BaseModel):
    task_id: str | None = None
    status: str
    cluster_id: str
    mode: str = "queued"
