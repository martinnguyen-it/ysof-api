from fastapi import APIRouter, Depends, Query
from app.domain.student.entity import ManyStudentsInStudentRequestResponse, Student, StudentInDB
from app.models.student import StudentModel
from app.infra.security.security_service import get_current_student
from app.shared.decorator import response_decorator
from app.use_cases.student_admin.list import ListStudentsRequestObject, ListStudentsUseCase
from typing import Annotated, Optional
from app.domain.shared.enum import Sort

router = APIRouter()


@router.get("/me", response_model=Student)
@response_decorator()
def get_me(
    current_student: StudentModel = Depends(get_current_student),
):
    return Student(**StudentInDB.model_validate(current_student).model_dump())


@router.get(
    "",
    dependencies=[Depends(get_current_student)],
    response_model=ManyStudentsInStudentRequestResponse,
)
@response_decorator()
def get_list_students(
    list_students_use_case: ListStudentsUseCase = Depends(ListStudentsUseCase),
    page_index: Annotated[int, Query(title="Page Index")] = 1,
    page_size: Annotated[int, Query(title="Page size", le=500)] = 300,
    search: Optional[str] = Query(None, title="Search"),
    sort: Optional[Sort] = Sort.ASCE,
    sort_by: Optional[str] = "numerical_order",
    group: Optional[int] = None,
):
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListStudentsRequestObject.builder(
        page_index=page_index,
        page_size=page_size,
        search=search,
        sort=sort_query,
        group=group,
        is_student_request=True,
    )
    response = list_students_use_case.execute(request_object=req_object)
    return response
