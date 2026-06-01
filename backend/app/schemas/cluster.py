"""
NexusOps AI — Cluster Pydantic Schemas
"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ClusterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    provider: str = "vanilla"
    region: Optional[str] = None
    environment: str = "production"
    api_server_url: Optional[str] = None
    tags: Optional[dict] = None


class ClusterCreate(ClusterBase):
    pass


class ClusterUpdate(BaseModel):
    display_name: Optional[str] = None
    provider: Optional[str] = None
    region: Optional[str] = None
    environment: Optional[str] = None
    tags: Optional[dict] = None
    is_active: Optional[bool] = None


class ClusterNodeOut(BaseModel):
    id: str
    name: str
    status: str
    role: str
    kubernetes_version: Optional[str]
    os_image: Optional[str]
    cpu_allocatable: Optional[float]
    memory_allocatable_gb: Optional[float]
    cpu_usage_percent: Optional[float]
    memory_usage_percent: Optional[float]

    model_config = {"from_attributes": True}


class ClusterOut(BaseModel):
    id: str
    name: str
    display_name: str
    provider: str
    status: str
    region: Optional[str]
    environment: str
    kubernetes_version: Optional[str]
    node_count: int
    namespace_count: int
    pod_count: int
    service_count: int = 0
    deployment_count: int = 0
    cpu_capacity: Optional[float]
    memory_capacity_gb: Optional[float]
    is_active: bool
    last_sync_at: Optional[datetime]
    tags: Optional[dict]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClusterDetailOut(ClusterOut):
    nodes: List[ClusterNodeOut] = []
    api_server_url: Optional[str]


class ClusterListResponse(BaseModel):
    items: List[ClusterOut]
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
    image: Optional[str]
    selector: Optional[dict] = None
    cpu_request_millicores: Optional[int]
    memory_request_mb: Optional[int]
    cpu_usage_percent: Optional[float]
    memory_usage_percent: Optional[float]
    is_healthy: bool
    labels: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class NamespaceOut(BaseModel):
    id: str
    cluster_id: str
    name: str
    status: str
    labels: Optional[dict]
    annotations: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class PodOut(BaseModel):
    id: str
    cluster_id: str
    namespace_name: str
    name: str
    phase: str
    status: str
    node_name: Optional[str]
    pod_ip: Optional[str]
    restart_count: int
    ready: bool
    owner_kind: Optional[str]
    owner_name: Optional[str]
    containers: Optional[Any]
    labels: Optional[dict]
    started_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ServiceOut(BaseModel):
    id: str
    cluster_id: str
    namespace_name: str
    name: str
    service_type: str
    cluster_ip: Optional[str]
    external_ip: Optional[str]
    ports: Optional[Any]
    selector: Optional[dict]
    labels: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class ReplicaSetOut(BaseModel):
    id: str
    cluster_id: str
    namespace_name: str
    name: str
    owner_kind: Optional[str]
    owner_name: Optional[str]
    replicas_desired: int
    replicas_ready: int
    labels: Optional[dict]
    selector: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class TopologyNode(BaseModel):
    id: str
    name: str
    type: str
    status: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    children: List["TopologyNode"] = Field(default_factory=list)


class ClusterTopologyOut(BaseModel):
    cluster_id: str
    generated_at: datetime
    root: TopologyNode


class SyncResponse(BaseModel):
    task_id: Optional[str] = None
    status: str
    cluster_id: str
    mode: str = "queued"
