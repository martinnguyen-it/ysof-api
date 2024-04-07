from fastapi import APIRouter, Body, Depends, Query, HTTPException, Path
from typing import Optional, Annotated

from app.domain.student.entity import ManyStudentsInResponse, Student, StudentInCreate, StudentInUpdate
from app.domain.shared.enum import AdminRole, Sort
from app.infra.security.security_service import authorization, get_current_active_admin
from app.shared.decorator import response_decorator
from app.use_cases.student_admin.list import ListStudentsUseCase, ListStudentsRequestObject
from app.use_cases.student_admin.update import UpdateStudentUseCase, UpdateStudentRequestObject
from app.use_cases.student_admin.get import (
    GetStudentRequestObject,
    GetStudentCase,
)
from app.use_cases.student_admin.create import (
    CreateStudentRequestObject,
    CreateStudentUseCase,
)
from app.models.admin import AdminModel
from app.shared.constant import SUPER_ADMIN
from app.use_cases.student_admin.delete import DeleteStudentRequestObject, DeleteStudentUseCase

router = APIRouter()


@router.get(
    "/{student_id}",
    dependencies=[Depends(get_current_active_admin)],
    response_model=Student,
)
@response_decorator()
def get_student_by_id(
    student_id: str = Path(..., title="Student id"),
    get_student_use_case: GetStudentCase = Depends(GetStudentCase),
):
    get_student_request_object = GetStudentRequestObject.builder(student_id=student_id)
    response = get_student_use_case.execute(request_object=get_student_request_object)
    return response


@router.post(
    "",
    response_model=Student,
)
@response_decorator()
def create_student(
    payload: StudentInCreate = Body(..., title="Student In Create payload"),
    create_student_use_case: CreateStudentUseCase = Depends(CreateStudentUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL])
    req_object = CreateStudentRequestObject.builder(payload=payload, current_admin=current_admin)
    response = create_student_use_case.execute(request_object=req_object)
    return response


@router.get(
    "",
    response_model=ManyStudentsInResponse,
)
@response_decorator()
def get_list_students(
    list_students_use_case: ListStudentsUseCase = Depends(ListStudentsUseCase),
    page_index: Annotated[int, Query(title="Page Index")] = 1,
    page_size: Annotated[int, Query(title="Page size")] = 300,
    search: Optional[str] = Query(None, title="Search"),
    sort: Optional[Sort] = Sort.DESC,
    sort_by: Optional[str] = "numerical_order",
    group: Optional[int] = None,
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    annotations = {}
    for base in reversed(Student.__mro__):
        annotations.update(getattr(base, "__annotations__", {}))
    if sort_by not in annotations:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by: {sort_by}")
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListStudentsRequestObject.builder(
        page_index=page_index,
        page_size=page_size,
        search=search,
        current_admin=current_admin,
        sort=sort_query,
        group=group,
    )
    response = list_students_use_case.execute(request_object=req_object)
    return response


@router.put(
    "/{id}",
    response_model=Student,
)
@response_decorator()
def update_student(
    id: str = Path(..., title="Student Id"),
    payload: StudentInUpdate = Body(..., title="Student updated payload"),
    update_student_use_case: UpdateStudentUseCase = Depends(UpdateStudentUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL])
    req_object = UpdateStudentRequestObject.builder(id=id, payload=payload, current_admin=current_admin)
    response = update_student_use_case.execute(request_object=req_object)
    return response


@router.delete("/{id}")
@response_decorator()
def delete_student(
    id: str = Path(..., title="Student Id"),
    delete_student_use_case: DeleteStudentUseCase = Depends(DeleteStudentUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL])
    req_object = DeleteStudentRequestObject.builder(id=id, current_admin=current_admin)
    response = delete_student_use_case.execute(request_object=req_object)
    return response
