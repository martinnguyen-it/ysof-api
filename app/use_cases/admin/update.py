import json
from typing import Optional
from fastapi import Depends, BackgroundTasks
from app.models.admin import AdminModel
from app.shared import request_object, use_case, response_object

from app.domain.admin.entity import Admin, AdminInDB, AdminInUpdate, AdminInUpdateTime
from app.infra.admin.admin_repository import AdminRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.shared.utils.general import get_current_season_value


class UpdateAdminRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str, current_admin: AdminModel, obj_in: AdminInUpdate) -> None:
        self.id = id
        self.obj_in = obj_in
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls, id: str, current_admin: AdminModel, payload: Optional[AdminInUpdate] | None = None
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Id không hợp lệ")

        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateAdminRequestObject(id=id, obj_in=payload, current_admin=current_admin)


class UpdateAdminUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        admin_repository: AdminRepository = Depends(AdminRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.background_tasks = background_tasks
        self.admin_repository = admin_repository
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: UpdateAdminRequestObject):
        admin: Optional[AdminModel] = self.admin_repository.get_by_id(req_object.id)
        if not admin:
            return response_object.ResponseFailure.build_not_found_error("Admin không tồn tại")

        self.admin_repository.update(id=admin.id, data=AdminInUpdateTime(**req_object.obj_in.model_dump()))
        admin.reload()

        current_season = get_current_season_value()
        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.UPDATE,
                endpoint=Endpoint.ADMIN,
                season=current_season,
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps(
                    req_object.obj_in.model_dump(exclude_none=True), default=str, ensure_ascii=False
                ),
            ),
        )

        return Admin(**AdminInDB.model_validate(admin).model_dump())
