from fastapi import APIRouter, Depends, Query, Path
from typing import Annotated
from app.infra.security.security_service import get_current_active_admin
from app.shared.decorator import response_decorator
from app.domain.subject.subject_evaluation.entity import (
    ManySubjectEvaluationAdminInResponse,
    SubjectEvaluationAdmin,
)
from app.use_cases.subject_evaluation.get import (
    GetSubjectEvaluationRequestObject,
    GetSubjectEvaluationUseCase,
)
from app.use_cases.subject_evaluation.list_by_student import (
    ListSubjectEvaluationByStudentRequestObject,
    ListSubjectEvaluationByStudentUseCase,
)
from app.use_cases.subject_evaluation.list import (
    ListSubjectEvaluationRequestObject,
    ListSubjectEvaluationUseCase,
)
from app.domain.shared.enum import Sort

router = APIRouter()


@router.get(
    "/detail",
    dependencies=[Depends(get_current_active_admin)],
    response_model=SubjectEvaluationAdmin,
)
@response_decorator()
def get_subject_evaluation(
    subject_id: str = Query(..., title="Subject id"),
    student_id: str = Query(..., title="Student id"),
    get_subject_evaluation_use_case: GetSubjectEvaluationUseCase = Depends(
        GetSubjectEvaluationUseCase
    ),
):
    req_object = GetSubjectEvaluationRequestObject.builder(
        subject_id=subject_id, current_student=student_id
    )
    response = get_subject_evaluation_use_case.execute(request_object=req_object)
    return response


@router.get(
    "/{student_id}",
    dependencies=[Depends(get_current_active_admin)],
    response_model=list[SubjectEvaluationAdmin],
)
@response_decorator()
def get_subject_evaluation_by_student_id(
    student_id: str = Path(..., title="Student id"),
    list_subject_evaluation_by_student: ListSubjectEvaluationByStudentUseCase = Depends(
        ListSubjectEvaluationByStudentUseCase
    ),
):
    req_object = ListSubjectEvaluationByStudentRequestObject.builder(current_student=student_id)
    response = list_subject_evaluation_by_student.execute(request_object=req_object)
    return response


@router.get(
    "",
    dependencies=[Depends(get_current_active_admin)],
    response_model=ManySubjectEvaluationAdminInResponse,
)
@response_decorator()
def get_all_subject_evaluation(
    subject_id: str,
    page_index: Annotated[int, Query(title="Page Index")] = 1,
    page_size: Annotated[int, Query(title="Page size", le=500)] = 300,
    search: str | None = Query(None, title="Search"),
    sort: Sort = Sort.ASCE,
    sort_by: str = "numerical_order",
    list_subject_evaluation_use_case: ListSubjectEvaluationUseCase = Depends(
        ListSubjectEvaluationUseCase
    ),
):
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}
    req_object = ListSubjectEvaluationRequestObject.builder(
        page_index=page_index,
        page_size=page_size,
        search=search,
        sort=sort_query,
        subject_id=subject_id,
    )
    response = list_subject_evaluation_use_case.execute(request_object=req_object)
    return response
