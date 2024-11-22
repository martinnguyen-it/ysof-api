from fastapi import APIRouter, Depends, Query, HTTPException, Path
from typing import Optional

from app.domain.subject.entity import Subject, SubjectInStudent
from app.domain.shared.enum import Sort
from app.infra.security.security_service import get_current_student
from app.shared.decorator import response_decorator
from app.use_cases.student_endpoint.subject.get import (
    GetSubjectStudentCase,
    GetSubjectStudentRequestObject,
)
from app.use_cases.student_endpoint.subject.list import (
    ListSubjectsStudentRequestObject,
    ListSubjectsStudentUseCase,
)
from app.models.student import StudentModel
from app.domain.subject.enum import StatusSubjectEnum

router = APIRouter()


@router.get(
    "/{subject_id}",
    dependencies=[Depends(get_current_student)],
    response_model=SubjectInStudent,
)
@response_decorator()
def get_subject_by_id(
    subject_id: str = Path(..., title="Subject id"),
    get_subject_use_case: GetSubjectStudentCase = Depends(GetSubjectStudentCase),
):
    get_subject_request_object = GetSubjectStudentRequestObject.builder(subject_id=subject_id)
    response = get_subject_use_case.execute(request_object=get_subject_request_object)
    return response


@router.get("", response_model=list[SubjectInStudent])
@response_decorator()
def get_list_subjects(
    list_subjects_use_case: ListSubjectsStudentUseCase = Depends(ListSubjectsStudentUseCase),
    search: Optional[str] = Query(None, title="Search"),
    sort: Optional[Sort] = Sort.DESC,
    sort_by: Optional[str] = "id",
    status: Optional[list[StatusSubjectEnum]] = Query(None, title="Status"),
    subdivision: Optional[str] = None,
    current_student: StudentModel = Depends(get_current_student),
    season: Optional[int] = None,
):
    annotations = {}
    for base in reversed(Subject.__mro__):
        annotations.update(getattr(base, "__annotations__", {}))
    if sort_by not in annotations:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by: {sort_by}")
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListSubjectsStudentRequestObject.builder(
        search=search,
        sort=sort_query,
        subdivision=subdivision,
        current_student=current_student,
        status=status,
        season=season,
    )
    response = list_subjects_use_case.execute(request_object=req_object)
    return response
