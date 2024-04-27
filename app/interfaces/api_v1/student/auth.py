from fastapi import APIRouter, Body, Depends

from app.domain.auth.entity import AuthAdminInfoInResponse, LoginRequest, UpdatePassword
from app.shared.decorator import response_decorator
from app.use_cases.student_endpoint.student_auth.login import LoginStudentRequestObject, LoginStudentUseCase
from app.infra.security.security_service import get_current_student
from app.models.student import StudentModel
from app.use_cases.student_endpoint.student_auth.update_password import (
    UpdateStudentPasswordRequestObject,
    UpdateStudentPasswordUseCase,
)

router = APIRouter()


@router.post("/login", response_model=AuthAdminInfoInResponse)
@response_decorator()
def login(payload: LoginRequest = Body(...), login_use_case: LoginStudentUseCase = Depends(LoginStudentUseCase)):
    req_object = LoginStudentRequestObject.builder(login_payload=payload)
    response = login_use_case.execute(req_object)
    return response


@router.put(
    "/change-password",
)
@response_decorator()
def change_password(
    payload: UpdatePassword = Body(..., title="Admin updated payload"),
    update_admin_password_use_case: UpdateStudentPasswordUseCase = Depends(UpdateStudentPasswordUseCase),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = UpdateStudentPasswordRequestObject.builder(payload=payload, current_student=current_student)
    response = update_admin_password_use_case.execute(request_object=req_object)
    return response
