from datetime import datetime, timezone
from typing import Optional, List
from pydantic import ConfigDict

from app.domain.admin.field import PydanticAdminType
from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin, Pagination
from app.domain.general_task.enum import GeneralTaskType
from app.domain.document.entity import Document
from app.domain.document.field import PydanticDocumentType


class AdminInGeneralTask(BaseEntity):
    id: str
    full_name: str
    avatar: Optional[str] = None
    active: Optional[bool] = False


class GeneralTaskBase(BaseEntity):
    title: str
    short_desc: Optional[str] = None
    description: str
    start_at: datetime
    end_at: datetime
    role: str
    label: Optional[list[str]] = None
    type: GeneralTaskType


class GeneralTaskInDB(IDModelMixin, DateTimeModelMixin, GeneralTaskBase):
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    author: PydanticAdminType
    season: Optional[int] = None
    attachments: Optional[List[PydanticDocumentType]] = None
    model_config = ConfigDict(from_attributes=True)


class GeneralTaskInCreate(GeneralTaskBase):
    attachments: Optional[List[str]] = None


class GeneralTask(GeneralTaskBase, DateTimeModelMixin):
    id: str
    author: AdminInGeneralTask
    season: int
    attachments: Optional[List[Document]] = None


class ManyGeneralTasksInResponse(BaseEntity):
    pagination: Optional[Pagination] = None
    data: Optional[List[GeneralTask]] = None


class GeneralTaskInUpdate(BaseEntity):
    title: Optional[str] = None
    short_desc: Optional[str] = None
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    role: Optional[str] = None
    label: Optional[list[str]] = None
    type: Optional[GeneralTaskType] = None
    attachments: Optional[List[str]] = None


class GeneralTaskInUpdateTime(GeneralTaskInUpdate):
    updated_at: datetime = datetime.now(timezone.utc)
