from datetime import datetime, date
from typing import Optional
from pydantic import ConfigDict

from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin
from app.domain.lecturer.field import PydanticLecturerType
from app.domain.lecturer.entity import Lecturer


class Zoom(BaseEntity):
    meeting_id: Optional[int] = None
    pass_code: Optional[str] = None
    link: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SubjectBase(BaseEntity):
    title: str
    start_at: date
    subdivision: str
    code: str
    question_url: Optional[str] = None
    zoom: Optional[Zoom] = None
    documents_url: list[str] | None = None


class SubjectInDB(IDModelMixin, DateTimeModelMixin, SubjectBase):
    lecturer: PydanticLecturerType
    season: int
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class SubjectInCreate(SubjectBase):
    lecturer: str


class Subject(SubjectBase, DateTimeModelMixin):
    id: str
    lecturer: Lecturer
    season: int


class SubjectBaseUpdate(BaseEntity):
    title: str | None = None
    start_at: date | None = None
    subdivision: str | None = None
    code: int | None = None
    question_url: Optional[str] = None
    zoom: Optional[Zoom] = None
    documents_url: list[str] | None = None


class SubjectInUpdate(SubjectBaseUpdate):
    lecturer: str | None = None


class SubjectInUpdateTime(SubjectBaseUpdate):
    lecturer: PydanticLecturerType | None = None
    updated_at: datetime = datetime.now()
