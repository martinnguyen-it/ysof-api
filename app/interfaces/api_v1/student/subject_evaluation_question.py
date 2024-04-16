from fastapi import APIRouter, Depends, Path

from app.infra.security.security_service import get_current_student
from app.shared.decorator import response_decorator

from app.domain.subject.subject_evaluation.entity import SubjectEvaluationQuestion
from app.use_cases.subject_evaluation_question.get import (
    GetSubjectEvaluationQuestionRequestObject,
    GetSubjectEvaluationQuestionUseCase,
)

router = APIRouter()


@router.get(
    "/{subject_id}",
    dependencies=[Depends(get_current_student)],
    response_model=SubjectEvaluationQuestion,
)
@response_decorator()
def get_subject_evaluation_question(
    subject_id: str = Path(..., title="Subject id"),
    get_subject_evaluation_question_use_case: GetSubjectEvaluationQuestionUseCase = Depends(
        GetSubjectEvaluationQuestionUseCase
    ),
):
    req_object = GetSubjectEvaluationQuestionRequestObject.builder(subject_id=subject_id)
    response = get_subject_evaluation_question_use_case.execute(request_object=req_object)
    return response
