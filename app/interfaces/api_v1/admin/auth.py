from typing import Annotated
from fastapi import APIRouter, Body, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.domain.auth.entity import (
    AuthAdminInfoInResponse,
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
from app.use_cases.admin_auth.login import LoginRequestObject, LoginUseCase
from app.use_cases.admin_auth.update_password import (
    UpdateAdminPasswordRequestObject,
    UpdateAdminPasswordUseCase,
)
from app.use_cases.admin_auth.forgot_password import (
    ForgotPasswordRequestObject,
    ForgotPasswordUseCase,
)
from app.use_cases.admin_auth.verify_otp import (
    VerifyOTPRequestObject,
    VerifyOTPUseCase,
)
from app.use_cases.admin_auth.reset_password import (
    ResetPasswordRequestObject,
    ResetPasswordUseCase,
)
from app.models.admin import AdminModel
from app.infra.security.security_service import get_current_admin

router = APIRouter()


@router.post("/login", response_model=AuthAdminInfoInResponse)
@response_decorator()
def login(
    payload: Annotated[OAuth2PasswordRequestForm, Depends()],
    login_use_case: LoginUseCase = Depends(LoginUseCase),
):
    req_object = LoginRequestObject.builder(
        login_payload=LoginRequest(email=payload.username, password=payload.password)
    )
    response = login_use_case.execute(req_object)
    return response


@router.put(
    "/change-password",
)
@response_decorator()
def change_password(
    payload: UpdatePassword = Body(..., title="Admin updated payload"),
    update_admin_password_use_case: UpdateAdminPasswordUseCase = Depends(
        UpdateAdminPasswordUseCase
    ),
    current_admin: AdminModel = Depends(get_current_admin),
):
    req_object = UpdateAdminPasswordRequestObject.builder(
        payload=payload, current_admin=current_admin
    )
    response = update_admin_password_use_case.execute(request_object=req_object)
    return response


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@response_decorator()
def forgot_password(
    payload: ForgotPassword = Body(..., title="Forgot password payload"),
    forgot_password_use_case: ForgotPasswordUseCase = Depends(ForgotPasswordUseCase),
):
    req_object = ForgotPasswordRequestObject.builder(payload=payload)
    response = forgot_password_use_case.execute(req_object)
    return response


@router.post("/verify-otp", response_model=VerifyOTPResponse)
@response_decorator()
def verify_otp(
    payload: VerifyOTP = Body(..., title="Verify OTP payload"),
    verify_otp_use_case: VerifyOTPUseCase = Depends(VerifyOTPUseCase),
):
    req_object = VerifyOTPRequestObject.builder(payload=payload)
    response = verify_otp_use_case.execute(req_object)
    return response


@router.post("/reset-password", response_model=ResetPasswordResponse)
@response_decorator()
def reset_password(
    payload: ResetPassword = Body(..., title="Reset password payload"),
    reset_password_use_case: ResetPasswordUseCase = Depends(ResetPasswordUseCase),
):
    req_object = ResetPasswordRequestObject.builder(payload=payload)
    response = reset_password_use_case.execute(req_object)
    return response
