from datetime import datetime, date, timezone
from typing import Optional
from pydantic import ConfigDict, field_validator, ValidationInfo

from app.domain.shared.entity import BaseEntity, DateTimeModelMixin, IDModelMixin, Pagination
from app.domain.lecturer.field import PydanticLecturerType
from app.domain.lecturer.entity import Lecturer, LecturerInStudent
from app.domain.student.field import PydanticStudentType
from app.domain.subject.field import PydanticSubjectType
from app.domain.subject.enum import StatusSubjectEnum
from app.domain.document.field import PydanticDocumentType
from app.domain.document.entity import Document, DocumentInStudent


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
    abstract: Optional[str] = None


class SubjectInDB(IDModelMixin, DateTimeModelMixin, SubjectBase):
    lecturer: PydanticLecturerType
    season: int
    status: StatusSubjectEnum = StatusSubjectEnum.INIT
    attachments: Optional[list[PydanticDocumentType]] = None
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class SubjectInCreate(SubjectBase):
    lecturer: str
    attachments: Optional[list[str]] = None


class Subject(SubjectBase, DateTimeModelMixin):
    id: str
    lecturer: Lecturer
    season: int
    status: StatusSubjectEnum
    attachments: Optional[list[Document]] = None


class SubjectInStudent(BaseEntity):
    id: str
    title: str
    start_at: date
    subdivision: str
    code: str
    season: int
    question_url: Optional[str] = None
    abstract: Optional[str] = None
    documents_url: list[str] | None = None
    lecturer: LecturerInStudent
    status: StatusSubjectEnum
    attachments: Optional[list[DocumentInStudent]] = None


class SubjectBaseUpdate(BaseEntity):
    title: str | None = None
    start_at: date | None = None
    subdivision: str | None = None
    code: str | None = None
    question_url: Optional[str] = None
    zoom: Optional[Zoom] = None
    documents_url: list[str] | None = None
    abstract: Optional[str] = None


class SubjectInUpdate(SubjectBaseUpdate):
    lecturer: str | None = None
    attachments: Optional[list[str]] = None


class SubjectInUpdateTime(SubjectBaseUpdate):
    lecturer: PydanticLecturerType | None = None
    status: StatusSubjectEnum | None = None
    attachments: Optional[list[PydanticDocumentType]] = None
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


class StudentInSubject(BaseEntity):
    numerical_order: int
    group: int
    holy_name: str
    full_name: str
    email: str
    id: str


class _SubjectRegistrationInResponse(BaseEntity):
    student: StudentInSubject
    total: int
    subject_registrations: list[str] | list


class ListSubjectRegistrationInResponse(BaseEntity):
    pagination: Optional[Pagination] = None
    data: Optional[list[_SubjectRegistrationInResponse]] = None
