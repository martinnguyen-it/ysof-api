from fastapi import APIRouter, Depends, Body, Path

from app.infra.security.security_service import get_current_student
from app.shared.decorator import response_decorator
from app.models.student import StudentModel
from app.domain.absent.entity import (
    StudentAbsentInCreate,
    StudentAbsentInResponse,
    StudentAbsentInUpdate,
)
from app.use_cases.absent.create import CreateAbsentRequestObject, CreateAbsentUseCase
from app.use_cases.absent.get import GetAbsentRequestObject, GetAbsentUseCase
from app.use_cases.absent.update import UpdateAbsentRequestObject, UpdateAbsentUseCase
from app.use_cases.absent.delete import DeleteAbsentRequestObject, DeleteAbsentUseCase

router = APIRouter()


@router.post("/{subject_id}", response_model=StudentAbsentInResponse)
@response_decorator()
def create_absent(
    subject_id: str = Path(..., title="Subject id"),
    payload: StudentAbsentInCreate = Body(..., title="Subject evaluation In Create payload"),
    create_absent_use_case: CreateAbsentUseCase = Depends(CreateAbsentUseCase),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = CreateAbsentRequestObject.builder(
        subject_id=subject_id, current_student=current_student, reason=payload.reason
    )
    response = create_absent_use_case.execute(request_object=req_object)
    return response


@router.patch("/{subject_id}", response_model=StudentAbsentInResponse)
@response_decorator()
def update_absent_by_subject_id(
    subject_id: str = Path(..., title="Subject id"),
    payload: StudentAbsentInUpdate = Body(..., title="Subject evaluation In update payload"),
    update_absent_use_case: UpdateAbsentUseCase = Depends(UpdateAbsentUseCase),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = UpdateAbsentRequestObject.builder(
        subject_id=subject_id, payload=payload, current_student=current_student
    )
    response = update_absent_use_case.execute(request_object=req_object)
    return response


@router.get("/{subject_id}", response_model=StudentAbsentInResponse)
@response_decorator()
def get_absent_by_subject_id(
    subject_id: str = Path(..., title="Subject id"),
    get_absent_use_case: GetAbsentUseCase = Depends(GetAbsentUseCase),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = GetAbsentRequestObject.builder(
        subject_id=subject_id, current_student=current_student
    )
    response = get_absent_use_case.execute(request_object=req_object)
    return response


@router.delete("/{subject_id}", response_model=StudentAbsentInResponse)
@response_decorator()
def delete_absent_by_subject_id(
    subject_id: str = Path(..., title="Subject id"),
    delete_absent_use_case: DeleteAbsentUseCase = Depends(DeleteAbsentUseCase),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = DeleteAbsentRequestObject.builder(
        subject_id=subject_id, current_student=current_student
    )
    response = delete_absent_use_case.execute(request_object=req_object)
    return response
