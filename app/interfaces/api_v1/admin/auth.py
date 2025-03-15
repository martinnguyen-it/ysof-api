from typing import Annotated
from fastapi import APIRouter, Body, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.domain.auth.entity import AuthAdminInfoInResponse, LoginRequest, UpdatePassword
from app.shared.decorator import response_decorator
from app.use_cases.admin_auth.login import LoginRequestObject, LoginUseCase
from app.use_cases.admin_auth.update_password import (
    UpdateAdminPasswordRequestObject,
    UpdateAdminPasswordUseCase,
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
