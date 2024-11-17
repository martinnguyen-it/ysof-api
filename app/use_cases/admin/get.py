from fastapi import Depends
from typing import Optional
from app.shared import request_object, response_object, use_case
from app.domain.admin.entity import Admin, AdminInDB
from app.infra.admin.admin_repository import AdminRepository
from app.models.admin import AdminModel


class GetAdminRequestObject(request_object.ValidRequestObject):
    def __init__(self, admin_id: str):
        self.admin_id = admin_id

    @classmethod
    def builder(cls, admin_id: str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not id:
            invalid_req.add_error("id", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return GetAdminRequestObject(admin_id=admin_id)


class GetAdminCase(use_case.UseCase):
    def __init__(self, admin_repository: AdminRepository = Depends(AdminRepository)):
        self.admin_repository = admin_repository

    def process_request(self, req_object: GetAdminRequestObject):
        admin: Optional[AdminModel] = self.admin_repository.get_by_id(admin_id=req_object.admin_id)
        if not admin:
            return response_object.ResponseFailure.build_not_found_error(
                message="Admin không tồn tại"
            )

        return Admin(**AdminInDB.model_validate(admin).model_dump())
