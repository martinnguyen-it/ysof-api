from datetime import datetime, timezone
from fastapi import Depends

from app.domain.auth.entity import UpdatePassword
from app.models.admin import AdminModel
from app.infra.security.security_service import get_password_hash, verify_password
from app.infra.admin.admin_repository import AdminRepository
from app.shared import request_object, use_case, response_object


class UpdateAdminPasswordRequestObject(request_object.ValidRequestObject):
    def __init__(self, payload: UpdatePassword, current_admin: AdminModel):
        self.payload = payload
        self.current_admin = current_admin

    @classmethod
    def builder(cls, payload: UpdatePassword, current_admin: AdminModel):
        invalid_req = request_object.InvalidRequestObject()
        if not payload:
            invalid_req.add_error("payload", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateAdminPasswordRequestObject(payload=payload, current_admin=current_admin)


class UpdateAdminPasswordUseCase(use_case.UseCase):
    def __init__(
        self,
        admin_repository: AdminRepository = Depends(AdminRepository),
    ):
        self.admin_repository = admin_repository

    def process_request(self, req_object: UpdateAdminPasswordRequestObject):
        checker = verify_password(req_object.payload.old_password, req_object.current_admin.password)
        if not checker:
            return response_object.ResponseFailure.build_parameters_error(message="Sai mật khẩu")

        res = self.admin_repository.update(
            id=req_object.current_admin.id,
            data={
                "password": get_password_hash(req_object.payload.new_password),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        if res:
            return {"success": True}
        else:
            return response_object.ResponseFailure.build_system_error(message="Something went wrong")
