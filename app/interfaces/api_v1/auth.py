from fastapi import APIRouter, Body, Depends

from app.domain.auth.entity import LoginRequest, AuthAdminInfoInResponse
from app.shared.decorator import response_decorator
from app.use_cases.auth.login import LoginRequestObject, LoginUseCase

router = APIRouter()


@router.post("/login", response_model=AuthAdminInfoInResponse)
@response_decorator()
def login(payload: LoginRequest = Body(...), login_use_case: LoginUseCase = Depends(LoginUseCase)):
    req_object = LoginRequestObject.builder(login_payload=payload)
    response = login_use_case.execute(req_object)
    return response
