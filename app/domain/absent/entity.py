from datetime import datetime, timezone
from pydantic import ConfigDict

from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin
from app.domain.student.field import PydanticStudentType
from app.domain.subject.field import PydanticSubjectType
from app.domain.student.entity import Student
from app.domain.subject.subject_evaluation.entity import SubjectInEvaluation


class StudentAbsentInCreate(BaseEntity):
    """_summary_
    StudentAbsentInCreate: Create by student
    """

    reason: str


class AdminAbsentInCreate(BaseEntity):
    """_summary_
    Create by admin when student can't create
    """

    reason: str | None = None
    note: str | None = None


class AbsentInDB(IDModelMixin, DateTimeModelMixin):
    student: PydanticStudentType
    subject: PydanticSubjectType
    reason: str | None = None
    note: str | None = None
    status: bool = True
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class AbsentResponseBase(DateTimeModelMixin):
    id: str
    subject: SubjectInEvaluation
    reason: str | None = None


class StudentAbsentInResponse(AbsentResponseBase):
    pass


class AdminAbsentInResponse(AbsentResponseBase):
    student: Student
    note: str | None = None
    status: bool


class StudentAbsentInUpdate(BaseEntity):
    reason: str | None = None


class AdminAbsentInUpdate(StudentAbsentInUpdate):
    note: str | None = None
    status: bool | None = None


class AbsentInUpdateTime(AdminAbsentInUpdate):
    updated_at: datetime = datetime.now(timezone.utc)
