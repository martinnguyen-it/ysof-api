from fastapi import APIRouter, Depends, Body, Path

from app.infra.security.security_service import get_current_student
from app.shared.decorator import response_decorator
from app.models.student import StudentModel
from app.domain.subject.subject_evaluation.entity import (
    SubjectEvaluationStudent,
    SubjectEvaluationInCreate,
    SubjectEvaluationInUpdate,
)
from app.use_cases.student_endpoint.subject_evaluation.create import (
    CreateSubjectEvaluationRequestObject,
    CreateSubjectEvaluationUseCase,
)
from app.use_cases.subject_evaluation.get import (
    GetSubjectEvaluationRequestObject,
    GetSubjectEvaluationUseCase,
)
from app.use_cases.student_endpoint.subject_evaluation.update import (
    UpdateSubjectEvaluationRequestObject,
    UpdateSubjectEvaluationUseCase,
)
from app.use_cases.subject_evaluation.list_by_student import (
    ListSubjectEvaluationByStudentRequestObject,
    ListSubjectEvaluationByStudentUseCase,
)


router = APIRouter()


@router.post("/{subject_id}", response_model=SubjectEvaluationStudent)
@response_decorator()
def create_subject_evaluation(
    subject_id: str = Path(..., title="Subject id"),
    payload: SubjectEvaluationInCreate = Body(..., title="Subject evaluation In Create payload"),
    create_subject_evaluation_use_case: CreateSubjectEvaluationUseCase = Depends(CreateSubjectEvaluationUseCase),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = CreateSubjectEvaluationRequestObject.builder(
        subject_id=subject_id, payload=payload, current_student=current_student
    )
    response = create_subject_evaluation_use_case.execute(request_object=req_object)
    return response


@router.patch("/{subject_id}", response_model=SubjectEvaluationStudent)
@response_decorator()
def update_subject_evaluation(
    subject_id: str = Path(..., title="Subject id"),
    payload: SubjectEvaluationInUpdate = Body(..., title="Subject evaluation In update payload"),
    update_subject_evaluation_use_case: UpdateSubjectEvaluationUseCase = Depends(UpdateSubjectEvaluationUseCase),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = UpdateSubjectEvaluationRequestObject.builder(
        subject_id=subject_id, payload=payload, current_student=current_student
    )
    response = update_subject_evaluation_use_case.execute(request_object=req_object)
    return response


@router.get("/{subject_id}", response_model=SubjectEvaluationStudent)
@response_decorator()
def get_subject_evaluation(
    subject_id: str = Path(..., title="Subject id"),
    get_subject_evaluation_use_case: GetSubjectEvaluationUseCase = Depends(GetSubjectEvaluationUseCase),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = GetSubjectEvaluationRequestObject.builder(subject_id=subject_id, current_student=current_student)
    response = get_subject_evaluation_use_case.execute(request_object=req_object)
    return response


@router.get("", response_model=SubjectEvaluationStudent)
@response_decorator()
def get_all_subject_evaluation_me(
    list_subject_evaluation_use_case: ListSubjectEvaluationByStudentUseCase = Depends(
        ListSubjectEvaluationByStudentUseCase
    ),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = ListSubjectEvaluationByStudentRequestObject.builder(current_student=current_student)
    response = list_subject_evaluation_use_case.execute(request_object=req_object)
    return response
