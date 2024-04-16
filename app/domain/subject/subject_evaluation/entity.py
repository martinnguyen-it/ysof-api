from datetime import datetime, timezone
from pydantic import ConfigDict

from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin
from app.domain.student.field import PydanticStudentType
from app.domain.subject.field import PydanticSubjectType
from app.domain.subject.subject_evaluation.enum import QualityValueEnum, TypeQuestionEnum
from app.domain.subject.entity import SubjectInStudent
from app.domain.student.entity import Student


class Quality(BaseEntity):
    focused_right_topic: QualityValueEnum
    practical_content: QualityValueEnum
    benefit_in_life: QualityValueEnum
    duration: QualityValueEnum
    method: QualityValueEnum
    model_config = ConfigDict(from_attributes=True)


class SubjectEvaluationBase(BaseEntity):
    quality: Quality
    most_resonated: str
    invited: str
    feedback_lecturer: str
    satisfied: int
    answers: list
    feedback_admin: str | None = None


class SubjectEvaluationInDB(IDModelMixin, DateTimeModelMixin, SubjectEvaluationBase):
    student: PydanticStudentType
    subject: PydanticSubjectType
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class SubjectEvaluationInCreate(SubjectEvaluationBase):
    pass


class SubjectEvaluation(SubjectEvaluationBase, DateTimeModelMixin):
    id: str
    subject: SubjectInStudent
    student: Student


class SubjectEvaluationInUpdate(BaseEntity):
    quality: Quality | None = None
    most_resonated: str | None = None
    invited: str | None = None
    feedback_lecturer: str | None = None
    satisfied: int | None = None
    answers: list | None = None
    feedback_admin: str | None = None


class SubjectEvaluationInUpdateTime(SubjectEvaluationInUpdate):
    updated_at: datetime = datetime.now(timezone.utc)


class Question(BaseEntity):
    """_summary_

    Args:
        title: Question /
        type: Type of question /
        answers: Answers if type is checkbox or radio
    """

    title: str
    type: TypeQuestionEnum
    answers: list[str] | None = None
    model_config = ConfigDict(from_attributes=True)


class SubjectEvaluationQuestionBase(BaseEntity):
    questions: list[Question]


class SubjectEvaluationQuestionInDB(IDModelMixin, DateTimeModelMixin, SubjectEvaluationQuestionBase):
    subject: PydanticSubjectType
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class SubjectEvaluationQuestionInCreate(SubjectEvaluationQuestionBase):
    pass


class SubjectEvaluationQuestion(SubjectEvaluationQuestionBase, DateTimeModelMixin):
    id: str
    questions: list[Question]


class SubjectEvaluationQuestionInUpdate(BaseEntity):
    questions: list[Question]


class SubjectEvaluationQuestionInUpdateTime(SubjectEvaluationQuestionInUpdate):
    updated_at: datetime = datetime.now(timezone.utc)
