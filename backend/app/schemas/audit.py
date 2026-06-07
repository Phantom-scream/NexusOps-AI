"""Audit event schemas."""

from datetime import datetime

from pydantic import AliasChoices, BaseModel, Field


class AuditEventOut(BaseModel):
    id: str
    actor_id: str | None
    actor_email: str | None
    actor_role: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    status: str
    request_id: str | None
    ip_address: str | None
    user_agent: str | None
    timestamp: datetime
    metadata: dict | None = Field(
        default=None,
        validation_alias=AliasChoices("metadata_", "metadata"),
    )

    model_config = {"from_attributes": True}


class AuditEventListResponse(BaseModel):
    items: list[AuditEventOut]
    total: int
    page: int
    page_size: int
