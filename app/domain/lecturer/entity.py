from datetime import datetime, timezone
from typing import Optional, List
from pydantic import ConfigDict

from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin, Pagination


class LecturerBase(BaseEntity):
    title: str
    holy_name: Optional[str] = None
    full_name: str
    information: Optional[str] = None
    contact: Optional[str] = None


class LecturerInDB(IDModelMixin, DateTimeModelMixin, LecturerBase):
    avatar: Optional[str] = None
    seasons: Optional[List[int]] = None
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class LecturerInCreate(LecturerBase):
    pass


class Lecturer(LecturerBase, DateTimeModelMixin):
    id: str
    avatar: Optional[str] = None
    seasons: Optional[List[int]] = None


class LecturerInStudent(BaseEntity):
    id: str
    avatar: Optional[str] = None
    title: str
    holy_name: Optional[str] = None
    full_name: str
    information: Optional[str] = None


class ManyLecturersInResponse(BaseEntity):
    pagination: Optional[Pagination] = None
    data: Optional[List[Lecturer]] = None


class LecturerInUpdate(BaseEntity):
    title: Optional[str] = None
    full_name: Optional[str] = None
    holy_name: Optional[str] = None
    information: Optional[str] = None
    contact: Optional[str] = None


class LecturerInUpdateTime(LecturerInUpdate):
    updated_at: datetime = datetime.now(timezone.utc)
