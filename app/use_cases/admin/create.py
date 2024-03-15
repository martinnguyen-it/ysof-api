from typing import Optional
from fastapi import Depends

from app.config import settings
from app.infra.security.security_service import get_password_hash, generate_random_password
from app.shared import request_object, use_case, response_object

from app.domain.admin.entity import Admin, AdminInCreate, AdminInDB
from app.infra.admin.admin_repository import AdminRepository


class CreateAdminRequestObject(request_object.ValidRequestObject):
    def __init__(self, admin_in: AdminInCreate = None) -> None:
        self.admin_in = admin_in

    @classmethod
    def builder(cls, payload: Optional[AdminInCreate] = None) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if not payload.email:
            invalid_req.add_error("payload.email", "Invalid email")

        if invalid_req.has_errors():
            return invalid_req

        return CreateAdminRequestObject(admin_in=payload)


class CreateAdminUseCase(use_case.UseCase):
    def __init__(self, admin_repository: AdminRepository = Depends(AdminRepository)):
        self.admin_repository = admin_repository

    def process_request(self, req_object: CreateAdminRequestObject):
        admin_in: AdminInCreate = req_object.admin_in
        existing_admin: Optional[AdminInDB] = self.admin_repository.get_by_email(email=admin_in.email)
        if existing_admin:
            return response_object.ResponseFailure.build_parameters_error(message="Email is existed.")

        obj_in: AdminInDB = AdminInDB(
            **admin_in.model_dump(exclude={"password"}), 
            password=get_password_hash(password="12345678"),
            # password=get_password_hash(password=generate_random_password()),
            current_season=settings.CURRENT_SEASON,
            seasons=[settings.CURRENT_SEASON],
        )
        admin_in_db: AdminInDB = self.admin_repository.create(admin=obj_in)
        return Admin(**admin_in_db.model_dump())
