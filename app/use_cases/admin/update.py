from typing import Optional
from fastapi import Depends
from app.models.admin import AdminModel
from app.shared import request_object, use_case, response_object

from app.domain.admin.entity import AdminInUpdate, AdminInDB, Admin
from app.infra.admin.admin_repository import AdminRepository


class UpdateAdminRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str, obj_in: AdminInUpdate) -> None:
        self.id = id
        self.obj_in = obj_in

    @classmethod
    def builder(cls, id: str, payload: Optional[AdminInUpdate]) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Id không hợp lệ")

        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateAdminRequestObject(id=id, obj_in=payload)


class UpdateAdminUseCase(use_case.UseCase):
    def __init__(self, admin_repository: AdminRepository = Depends(AdminRepository)):
        self.admin_repository = admin_repository

    def process_request(self, req_object: UpdateAdminRequestObject):
        admin: Optional[AdminModel] = self.admin_repository.get_by_id(
            req_object.id)
        if not admin:
            return response_object.ResponseFailure.build_not_found_error("Admin không tồn tại")

        self.admin_repository.update(id=admin.id, data=req_object.obj_in)
        admin.reload()
        return Admin(**AdminInDB.model_validate(admin).model_dump())
