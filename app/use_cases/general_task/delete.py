from typing import Optional

from fastapi import Depends
from app.infra.general_task.general_task_repository import GeneralTaskRepository
from app.shared import request_object, response_object, use_case
from app.domain.shared.enum import AdminRole
from app.shared.constant import SUPER_ADMIN
from app.models.general_task import GeneralTaskModel


class DeleteGeneralTaskRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str,
                 admin_roles: list[AdminRole]):
        self.id = id
        self.admin_roles = admin_roles

    @classmethod
    def builder(cls, id: str,
                admin_roles: list[AdminRole]
                ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if invalid_req.has_errors():
            return invalid_req

        return DeleteGeneralTaskRequestObject(id=id, admin_roles=admin_roles)


class DeleteGeneralTaskUseCase(use_case.UseCase):
    def __init__(self,
                 general_task_repository: GeneralTaskRepository = Depends(GeneralTaskRepository)):
        self.general_task_repository = general_task_repository

    def process_request(self, req_object: DeleteGeneralTaskRequestObject):
        general_task: Optional[GeneralTaskModel] = self.general_task_repository.get_by_id(
            req_object.id)
        if not general_task:
            return response_object.ResponseFailure.build_not_found_error("Tài liệu không tồn tại")
        if general_task.role not in req_object.admin_roles and \
                not any(role in SUPER_ADMIN for role in req_object.admin_roles):
            return response_object.ResponseFailure.build_not_found_error("Bạn không có quyền")

        try:
            self.general_task_repository.delete(id=general_task.id)
            return {"success": True}
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went error.")
