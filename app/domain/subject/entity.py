from datetime import datetime, date, timezone
from typing import Optional
from pydantic import ConfigDict, field_validator, ValidationInfo

from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin
from app.domain.lecturer.field import PydanticLecturerType
from app.domain.lecturer.entity import Lecturer, LecturerInStudent
from app.domain.student.field import PydanticStudentType
from app.domain.subject.field import PydanticSubjectType
from app.domain.subject.enum import StatusSubjectEnum


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
    status: StatusSubjectEnum = StatusSubjectEnum.INIT
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class SubjectInCreate(SubjectBase):
    lecturer: str


class Subject(SubjectBase, DateTimeModelMixin):
    id: str
    lecturer: Lecturer
    season: int
    status: StatusSubjectEnum


class SubjectInStudent(BaseEntity):
    id: str
    title: str
    start_at: date
    subdivision: str
    code: str
    season: int
    question_url: Optional[str] = None
    documents_url: list[str] | None = None
    lecturer: LecturerInStudent


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
    updated_at: datetime = datetime.now(timezone.utc)


class SubjectRegistrationInDB(IDModelMixin):
    student: PydanticStudentType
    subject: PydanticSubjectType
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class SubjectRegistrationInCreate(BaseEntity):
    subjects: list[str]

    @field_validator("subjects", mode="after")
    def remove_duplicate(cls, v):
        return list(set(v))


class SubjectRegistrationInResponse(BaseEntity):
    student_id: str
    subjects_registration: list[str]

    @field_validator("student_id", "subjects_registration", mode="before")
    def convert_to_string(cls, v, info: ValidationInfo):
        if info.field_name == "student_id":
            v = str(v)
        elif info.field_name == "subjects_registration":
            v = [str(val) for val in v]
        return v
