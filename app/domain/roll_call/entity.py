from app.domain.shared.entity import ImportSpreadsheetsPayload
from typing import Optional
from pydantic import validator

from app.domain.absent.enum import AbsentType
from app.domain.shared.entity import BaseEntity
from app.domain.subject.entity import SubjectShortResponse


class SubjectRollCallResult(BaseEntity):
    attend_zoom: bool
    evaluation: bool
    absent_type: Optional[AbsentType] = None
    result: str | None = None

    @validator("result", pre=True, always=True)
    def create_web_link(cls, v, values):
        if values["attend_zoom"] and (
            values["evaluation"] or values["absent_type"] == AbsentType.NO_EVALUATION
        ):
            return "completed"
        if values["absent_type"] == AbsentType.NO_ATTEND:
            return "absent"
        return "no_complete"


class SubjectRollCallResultInStudent(BaseEntity):
    subject: SubjectShortResponse
    attend_zoom: bool
    evaluation: bool
    absent_type: Optional[AbsentType] = None
    result: str | None = None

    @validator("result", pre=True, always=True)
    def create_web_link(cls, v, values):
        if values["attend_zoom"] and (
            values["evaluation"] or values["absent_type"] == AbsentType.NO_EVALUATION
        ):
            return "completed"
        if values["absent_type"] == AbsentType.NO_ATTEND:
            return "absent"
        return "no_complete"


class StudentRollCallResult(BaseEntity):
    id: str
    numerical_order: int
    holy_name: str
    full_name: str
    subjects: dict[str, SubjectRollCallResult | None]  # key is subject_id
    subject_completed: int = 0
    subject_not_completed: int = 0
    subject_registered: int = 0


class StudentRollCallResultInStudentResponse(BaseEntity):
    subjects: list[SubjectRollCallResultInStudent]
    subject_completed: int = 0
    subject_not_completed: int = 0
    subject_registered: int = 0


class StudentRollCallResultInResponse(BaseEntity):
    data: list[StudentRollCallResult]
    summary: dict[str, dict[str, int]]


class RollCallBulkSheet(ImportSpreadsheetsPayload):
    subject_id: str
