from datetime import datetime
from typing import Optional, List
from pydantic import ConfigDict

from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin, Pagination
from app.domain.lecturer.field import PydanticLecturerType
from app.domain.lecturer.entity import Lecturer


class Zoom(BaseEntity):
    meeting_id: Optional[int] = None
    pass_code: Optional[str] = None
    link: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SubjectBase(BaseEntity):
    title: str
    date: datetime
    subdivision: str
    code: str
    question_url: Optional[str] = None
    zoom: Optional[Zoom] = None
    documents_url: list[str] | None = None


class SubjectInDB(IDModelMixin, DateTimeModelMixin, SubjectBase):
    lecturer: PydanticLecturerType
    session: int
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class SubjectInCreate(SubjectBase):
    lecturer: str


class Subject(SubjectBase, DateTimeModelMixin):
    id: str
    lecturer: Lecturer
    session: int


class ManySubjectsInResponse(BaseEntity):
    pagination: Optional[Pagination] = None
    data: Optional[List[Subject]] = None


class SubjectInUpdate(BaseEntity):
    title: str | None = None
    date: datetime | None = None
    subdivision: str | None = None
    code: int | None = None
    question_url: Optional[str] = None
    zoom: Optional[Zoom] = None
    documents_url: list[str] | None = None
    lecturer: str | None = None


class SubjectInUpdateTime(BaseEntity):
    updated_at: datetime = datetime.now()
