import json
from typing import Optional

from fastapi import Depends, BackgroundTasks
from app.infra.general_task.general_task_repository import GeneralTaskRepository
from app.shared import request_object, response_object, use_case
from app.shared.constant import SUPER_ADMIN
from app.models.general_task import GeneralTaskModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.domain.general_task.entity import GeneralTaskInDB
from app.models.admin import AdminModel
from app.shared.utils.general import get_current_season_value


class DeleteGeneralTaskRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str, current_admin: AdminModel):
        self.id = id
        self.current_admin = current_admin

    @classmethod
    def builder(cls, id: str, current_admin: AdminModel) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if invalid_req.has_errors():
            return invalid_req

        return DeleteGeneralTaskRequestObject(id=id, current_admin=current_admin)


class DeleteGeneralTaskUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        general_task_repository: GeneralTaskRepository = Depends(GeneralTaskRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.general_task_repository = general_task_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: DeleteGeneralTaskRequestObject):
        general_task: Optional[GeneralTaskModel] = self.general_task_repository.get_by_id(
            req_object.id
        )
        if not general_task:
            return response_object.ResponseFailure.build_not_found_error("Tài liệu không tồn tại")
        if general_task.role not in req_object.current_admin.roles and not any(
            role in SUPER_ADMIN for role in req_object.current_admin.roles
        ):
            return response_object.ResponseFailure.build_not_found_error("Bạn không có quyền")

        try:
            self.general_task_repository.delete(id=general_task.id)

            current_season = get_current_season_value()
            self.background_tasks.add_task(
                self.audit_log_repository.create,
                AuditLogInDB(
                    type=AuditLogType.DELETE,
                    endpoint=Endpoint.GENERAL_TASK,
                    season=current_season,
                    author=req_object.current_admin,
                    author_email=req_object.current_admin.email,
                    author_name=req_object.current_admin.full_name,
                    author_roles=req_object.current_admin.roles,
                    description=json.dumps(
                        GeneralTaskInDB.model_validate(general_task).model_dump(exclude_none=True),
                        default=str,
                        ensure_ascii=False,
                    ),
                ),
            )
            return {"success": True}
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went error.")
