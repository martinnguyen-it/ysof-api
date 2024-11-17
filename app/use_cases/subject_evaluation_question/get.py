from fastapi import Depends

from app.shared import request_object, use_case, response_object

from app.domain.subject.subject_evaluation.entity import (
    SubjectEvaluationQuestion,
    SubjectEvaluationQuestionInDB,
)
from app.infra.subject.subject_evaluation_question_repository import (
    SubjectEvaluationQuestionRepository,
)
from app.models.subject_evaluation import SubjectEvaluationQuestionModel


class GetSubjectEvaluationQuestionRequestObject(request_object.ValidRequestObject):
    def __init__(self, subject_id=str) -> None:
        self.subject_id = subject_id

    @classmethod
    def builder(cls, subject_id: str) -> request_object.RequestObject:
        return GetSubjectEvaluationQuestionRequestObject(subject_id=subject_id)


class GetSubjectEvaluationQuestionUseCase(use_case.UseCase):
    def __init__(
        self,
        subject_evaluation_question_repository: SubjectEvaluationQuestionRepository = Depends(
            SubjectEvaluationQuestionRepository
        ),
    ):
        self.subject_evaluation_question_repository = subject_evaluation_question_repository

    def process_request(self, req_object: GetSubjectEvaluationQuestionRequestObject):
        subject_evaluation_question: SubjectEvaluationQuestionModel = (
            self.subject_evaluation_question_repository.get_by_subject_id(
                subject_id=req_object.subject_id
            )
        )

        if not subject_evaluation_question:
            return response_object.ResponseFailure.build_not_found_error(
                message="Câu hỏi lượng giá chưa được thêm."
            )

        return SubjectEvaluationQuestion(
            **SubjectEvaluationQuestionInDB.model_validate(subject_evaluation_question).model_dump(
                exclude=({"subject"})
            ),
        )
