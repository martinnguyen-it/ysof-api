from fastapi import APIRouter, Body, Depends, Query, Path
from typing import Optional, Annotated

from app.domain.shared.entity import ImportSpreadsheetsPayload
from app.domain.student.entity import (
    ImportSpreadsheetsInResponse,
    ManyStudentsInResponse,
    ResetPasswordResponse,
    Student,
    StudentInCreate,
    StudentInUpdate,
)
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
from app.use_cases.student_admin.import_from_spreadsheets import (
    ImportSpreadsheetsStudentRequestObject,
    ImportSpreadsheetsStudentUseCase,
)
from app.use_cases.student_admin.reset_password import (
    ResetPasswordStudentRequestObject,
    ResetPasswordStudentUseCase,
)

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
    dependencies=[Depends(get_current_active_admin)],
    response_model=ManyStudentsInResponse,
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
    season: int | None = None,
):
    if sort_by in ["numerical_order", "season", "group"]:
        sort_by = f"seasons_info.{sort_by}"
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListStudentsRequestObject.builder(
        page_index=page_index,
        page_size=page_size,
        search=search,
        sort=sort_query,
        group=group,
        season=season,
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
    req_object = UpdateStudentRequestObject.builder(
        id=id, payload=payload, current_admin=current_admin
    )
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


@router.post("/import", response_model=ImportSpreadsheetsInResponse)
@response_decorator()
def import_student_from_spreadsheets(
    payload: ImportSpreadsheetsPayload = Body(..., title="Url spreadsheets"),
    import_student_use_case: ImportSpreadsheetsStudentUseCase = Depends(
        ImportSpreadsheetsStudentUseCase
    ),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL])
    req_object = ImportSpreadsheetsStudentRequestObject.builder(
        payload=payload, current_admin=current_admin
    )
    response = import_student_use_case.execute(request_object=req_object)
    return response


@router.patch("/reset-password/{id}", response_model=ResetPasswordResponse)
@response_decorator()
def reset_password_student(
    id: str = Path(..., title="Student Id"),
    current_admin: AdminModel = Depends(get_current_active_admin),
    reset_password_student_use_case: ResetPasswordStudentUseCase = Depends(
        ResetPasswordStudentUseCase
    ),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL])
    req_object = ResetPasswordStudentRequestObject.builder(
        student_id=id, current_admin=current_admin
    )
    response = reset_password_student_use_case.execute(request_object=req_object)
    return response
