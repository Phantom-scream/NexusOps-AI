"""
NexusOps AI — Cluster Pydantic Schemas
"""
from datetime import datetime
from typing import List, Optional

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
    cpu_request_millicores: Optional[int]
    memory_request_mb: Optional[int]
    cpu_usage_percent: Optional[float]
    memory_usage_percent: Optional[float]
    is_healthy: bool
    labels: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}
