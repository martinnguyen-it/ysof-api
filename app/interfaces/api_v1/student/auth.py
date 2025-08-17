from fastapi.security import OAuth2PasswordRequestForm
from typing_extensions import Annotated
from fastapi import APIRouter, Body, Depends

from app.domain.auth.entity import (
    AuthStudentInfoInResponse,
    LoginRequest,
    UpdatePassword,
    ForgotPassword,
    ForgotPasswordResponse,
    VerifyOTP,
    VerifyOTPResponse,
    ResetPassword,
    ResetPasswordResponse,
)
from app.shared.decorator import response_decorator
from app.use_cases.student_endpoint.student_auth.login import (
    LoginStudentRequestObject,
    LoginStudentUseCase,
)
from app.use_cases.student_endpoint.student_auth.forgot_password import (
    ForgotPasswordStudentRequestObject,
    ForgotPasswordStudentUseCase,
)
from app.use_cases.student_endpoint.student_auth.verify_otp import (
    VerifyOTPStudentRequestObject,
    VerifyOTPStudentUseCase,
)
from app.use_cases.student_endpoint.student_auth.reset_password import (
    ResetPasswordStudentRequestObject,
    ResetPasswordStudentUseCase,
)
from app.infra.security.security_service import get_current_student
from app.models.student import StudentModel
from app.use_cases.student_endpoint.student_auth.update_password import (
    UpdateStudentPasswordRequestObject,
    UpdateStudentPasswordUseCase,
)

router = APIRouter()


@router.post("/login", response_model=AuthStudentInfoInResponse)
@response_decorator()
def login(
    payload: Annotated[OAuth2PasswordRequestForm, Depends()],
    login_use_case: LoginStudentUseCase = Depends(LoginStudentUseCase),
):
    req_object = LoginStudentRequestObject.builder(
        login_payload=LoginRequest(email=payload.username, password=payload.password)
    )
    response = login_use_case.execute(req_object)
    return response


@router.put(
    "/change-password",
)
@response_decorator()
def change_password(
    payload: UpdatePassword = Body(..., title="Student updated payload"),
    update_student_password_use_case: UpdateStudentPasswordUseCase = Depends(
        UpdateStudentPasswordUseCase
    ),
    current_student: StudentModel = Depends(get_current_student),
):
    req_object = UpdateStudentPasswordRequestObject.builder(
        payload=payload, current_student=current_student
    )
    response = update_student_password_use_case.execute(request_object=req_object)
    return response


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@response_decorator()
def forgot_password(
    payload: ForgotPassword = Body(..., title="Forgot password payload"),
    forgot_password_use_case: ForgotPasswordStudentUseCase = Depends(ForgotPasswordStudentUseCase),
):
    req_object = ForgotPasswordStudentRequestObject.builder(payload=payload)
    response = forgot_password_use_case.execute(req_object)
    return response


@router.post("/verify-otp", response_model=VerifyOTPResponse)
@response_decorator()
def verify_otp(
    payload: VerifyOTP = Body(..., title="Verify OTP payload"),
    verify_otp_use_case: VerifyOTPStudentUseCase = Depends(VerifyOTPStudentUseCase),
):
    req_object = VerifyOTPStudentRequestObject.builder(payload=payload)
    response = verify_otp_use_case.execute(req_object)
    return response


@router.post("/reset-password", response_model=ResetPasswordResponse)
@response_decorator()
def reset_password(
    payload: ResetPassword = Body(..., title="Reset password payload"),
    reset_password_use_case: ResetPasswordStudentUseCase = Depends(ResetPasswordStudentUseCase),
):
    req_object = ResetPasswordStudentRequestObject.builder(payload=payload)
    response = reset_password_use_case.execute(req_object)
    return response
