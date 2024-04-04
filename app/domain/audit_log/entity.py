from datetime import datetime
from typing import Optional, List
from pydantic import ConfigDict

from app.domain.shared.entity import BaseEntity, IDModelMixin, Pagination
from app.domain.audit_log.enum import Endpoint, AuditLogType
from app.domain.admin.field import PydanticAdminType
from app.domain.admin.entity import Admin


class AuditLogBase(BaseEntity):
    type: AuditLogType
    endpoint: Endpoint
    author_name: str
    author_email: str
    author_roles: list[str]
    description: str | None = None


class AuditLogInDB(IDModelMixin, AuditLogBase):
    author: PydanticAdminType | None = None
    season: int
    created_at: datetime | None = None
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class AuditLog(AuditLogBase):
    id: str
    author: Admin | None = None
    season: int
    created_at: datetime | None = None


class ManyLogsInResponse(BaseEntity):
    pagination: Optional[Pagination] = None
    data: Optional[List[AuditLog]] = None
