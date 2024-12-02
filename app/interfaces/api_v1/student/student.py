from fastapi import APIRouter, Depends, Query
from app.domain.student.entity import ManyStudentsInStudentRequestResponse, Student, StudentInDB
from app.models.student import StudentModel
from app.infra.security.security_service import get_current_student
from app.shared.decorator import response_decorator
from typing import Annotated, Optional
from app.domain.shared.enum import Sort
from app.use_cases.student_endpoint.student.list import (
    ListStudentsInStudentRequestObject,
    ListStudentsInStudentRequestUseCase,
)

router = APIRouter()


@router.get("/me", response_model=Student)
@response_decorator()
def get_me(
    current_student: StudentModel = Depends(get_current_student),
):
    return Student(**StudentInDB.model_validate(current_student).model_dump())


@router.get("", response_model=ManyStudentsInStudentRequestResponse)
@response_decorator()
def get_list_students(
    list_students_use_case: ListStudentsInStudentRequestUseCase = Depends(
        ListStudentsInStudentRequestUseCase
    ),
    page_index: Annotated[int, Query(title="Page Index")] = 1,
    page_size: Annotated[int, Query(title="Page size", le=500)] = 300,
    search: Optional[str] = Query(None, title="Search"),
    sort: Optional[Sort] = Sort.ASCE,
    sort_by: Optional[str] = "numerical_order",
    group: Optional[int] = None,
    current_student: StudentModel = Depends(get_current_student),
    season: int | None = None,
):
    if sort_by in ["numerical_order", "season", "group"]:
        sort_by = f"seasons_info.{sort_by}"
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListStudentsInStudentRequestObject.builder(
        page_index=page_index,
        page_size=page_size,
        search=search,
        sort=sort_query,
        group=group,
        current_student=current_student,
        season=season,
    )
    response = list_students_use_case.execute(request_object=req_object)
    return response
