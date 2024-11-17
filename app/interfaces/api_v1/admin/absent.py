from fastapi import APIRouter, Depends, Body, Path

from app.infra.security.security_service import authorization, get_current_active_admin
from app.shared.decorator import response_decorator
from app.domain.absent.entity import AdminAbsentInCreate, AdminAbsentInResponse, AdminAbsentInUpdate
from app.use_cases.absent.create import CreateAbsentRequestObject, CreateAbsentUseCase
from app.use_cases.absent.get import GetAbsentRequestObject, GetAbsentUseCase
from app.use_cases.absent.update import UpdateAbsentRequestObject, UpdateAbsentUseCase
from app.use_cases.absent.delete import DeleteAbsentRequestObject, DeleteAbsentUseCase
from app.models.admin import AdminModel
from app.use_cases.absent.list import ListAbsentRequestObject, ListAbsentUseCase
from app.shared.constant import SUPER_ADMIN
from app.domain.shared.enum import AdminRole

router = APIRouter()


@router.post("/subject/{subject_id}/student/{student_id}", response_model=AdminAbsentInResponse)
@response_decorator()
def create_absent(
    subject_id: str = Path(..., title="Subject id"),
    student_id: str = Path(..., title="Student id"),
    payload: AdminAbsentInCreate = Body(..., title="Subject absent In Create payload"),
    create_absent_use_case: CreateAbsentUseCase = Depends(CreateAbsentUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL])
    req_object = CreateAbsentRequestObject.builder(
        subject_id=subject_id,
        current_admin=current_admin,
        reason=payload.reason,
        note=payload.note,
        current_student=student_id,
    )
    response = create_absent_use_case.execute(request_object=req_object)
    return response


@router.patch("/subject/{subject_id}/student/{student_id}", response_model=AdminAbsentInResponse)
@response_decorator()
def update_absent(
    subject_id: str = Path(..., title="Subject id"),
    student_id: str = Path(..., title="Student id"),
    payload: AdminAbsentInUpdate = Body(..., title="Subject absent In update payload"),
    update_absent_use_case: UpdateAbsentUseCase = Depends(UpdateAbsentUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL])
    req_object = UpdateAbsentRequestObject.builder(
        subject_id=subject_id,
        payload=payload,
        current_admin=current_admin,
        current_student=student_id,
    )
    response = update_absent_use_case.execute(request_object=req_object)
    return response


@router.get("/subject/{subject_id}/student/{student_id}", response_model=AdminAbsentInResponse)
@response_decorator()
def get_absent(
    subject_id: str = Path(..., title="Subject id"),
    student_id: str = Path(..., title="Student id"),
    get_absent_use_case: GetAbsentUseCase = Depends(GetAbsentUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL, AdminRole.BHV])
    req_object = GetAbsentRequestObject.builder(subject_id=subject_id, current_student=student_id)
    response = get_absent_use_case.execute(request_object=req_object)
    return response


@router.get(
    "/{subject_id}",
    response_model=AdminAbsentInResponse,
)
@response_decorator()
def list_absent_by_subject_id(
    subject_id: str = Path(..., title="Subject id"),
    get_absent_use_case: ListAbsentUseCase = Depends(ListAbsentUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL, AdminRole.BHV])
    req_object = ListAbsentRequestObject.builder(subject_id=subject_id)
    response = get_absent_use_case.execute(request_object=req_object)
    return response


@router.delete("/subject/{subject_id}/student/{student_id}")
@response_decorator()
def delete_absent(
    subject_id: str = Path(..., title="Subject id"),
    student_id: str = Path(..., title="Student id"),
    delete_absent_use_case: DeleteAbsentUseCase = Depends(DeleteAbsentUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL])
    req_object = DeleteAbsentRequestObject.builder(
        subject_id=subject_id, current_admin=current_admin, current_student=student_id
    )
    response = delete_absent_use_case.execute(request_object=req_object)
    return response
