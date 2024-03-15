from fastapi import Depends

from app.domain.auth.entity import LoginRequest, TokenData, AuthAdminInfoInResponse
from app.domain.admin.entity import Admin, AdminInDB
from app.models.admin import AdminModel
from app.infra.security.security_service import verify_password, create_access_token
from app.infra.admin.admin_repository import AdminRepository
from app.shared import request_object, use_case, response_object


class LoginRequestObject(request_object.ValidRequestObject):
    def __init__(self, login_payload: LoginRequest):
        self.login_payload = login_payload

    @classmethod
    def builder(cls, login_payload: LoginRequest):
        invalid_req = request_object.InvalidRequestObject()
        if not login_payload:
            invalid_req.add_error("login_payload", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return LoginRequestObject(login_payload=login_payload)


class LoginUseCase(use_case.UseCase):
    def __init__(
            self,
            admin_repository: AdminRepository = Depends(AdminRepository),
    ):
        self.admin_repository = admin_repository

    def process_request(self, req_object: LoginRequestObject):
        admin: AdminModel = self.admin_repository.get_by_email(req_object.login_payload.email)
        checker = False
        if admin:
            checker = verify_password(req_object.login_payload.password, admin.password)
        if not admin or not checker:
            return response_object.ResponseFailure.build_parameters_error(message="Incorrect email or password")
        access_token = create_access_token(
            data=TokenData(email=admin.email, id=str(admin.id))
        )
        return AuthAdminInfoInResponse(access_token=access_token,
                                       user=Admin(**AdminInDB.model_validate(admin).model_dump()))
