from fastapi import APIRouter, Body, Depends, Path

from app.domain.shared.enum import AdminRole
from app.infra.security.security_service import authorization, get_current_active_admin
from app.shared.decorator import response_decorator

from app.models.admin import AdminModel
from app.shared.constant import SUPER_ADMIN
from app.use_cases.subject_evaluation_question.create import (
    CreateSubjectEvaluationQuestionRequestObject,
    CreateSubjectEvaluationQuestionUseCase,
)
from app.domain.subject.subject_evaluation.entity import (
    SubjectEvaluationQuestion,
    SubjectEvaluationQuestionInCreate,
    SubjectEvaluationQuestionInUpdate,
)
from app.use_cases.subject_evaluation_question.get import (
    GetSubjectEvaluationQuestionRequestObject,
    GetSubjectEvaluationQuestionUseCase,
)
from app.use_cases.subject_evaluation_question.update import (
    UpdateSubjectEvaluationQuestionRequestObject,
    UpdateSubjectEvaluationQuestionUseCase,
)

router = APIRouter()


@router.post(
    "/{subject_id}",
    response_model=SubjectEvaluationQuestion,
)
@response_decorator()
def create_subject_evaluation_question(
    subject_id: str = Path(..., title="Subject id"),
    payload: SubjectEvaluationQuestionInCreate = Body(..., title="Subject Evaluation Question In Create payload"),
    create_subject_use_case: CreateSubjectEvaluationQuestionUseCase = Depends(CreateSubjectEvaluationQuestionUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV])
    req_object = CreateSubjectEvaluationQuestionRequestObject.builder(
        payload=payload, current_admin=current_admin, subject_id=subject_id
    )
    response = create_subject_use_case.execute(request_object=req_object)
    return response


@router.get(
    "/{subject_id}",
    dependencies=[Depends(get_current_active_admin)],
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


@router.patch(
    "/{subject_id}",
    response_model=SubjectEvaluationQuestion,
)
@response_decorator()
def update_subject_evaluation_question(
    subject_id: str = Path(..., title="Subject id"),
    payload: SubjectEvaluationQuestionInUpdate = Body(..., title="Subject Evaluation Question In Create payload"),
    update_subject_evaluation_question_use_case: UpdateSubjectEvaluationQuestionUseCase = Depends(
        UpdateSubjectEvaluationQuestionUseCase
    ),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV])
    req_object = UpdateSubjectEvaluationQuestionRequestObject.builder(
        payload=payload, current_admin=current_admin, subject_id=subject_id
    )
    response = update_subject_evaluation_question_use_case.execute(request_object=req_object)
    return response
