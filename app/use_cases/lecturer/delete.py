import json
from typing import Optional

from fastapi import Depends, BackgroundTasks
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.shared import request_object, response_object, use_case
from app.models.lecturer import LecturerModel
from app.infra.subject.subject_repository import SubjectRepository
from app.models.admin import AdminModel
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.lecturer.entity import LecturerInDB
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.shared.utils.general import get_current_season_value


class DeleteLecturerRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_admin: AdminModel, id: str):
        self.id = id
        self.current_admin = current_admin

    @classmethod
    def builder(cls, id: str, current_admin: AdminModel) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if invalid_req.has_errors():
            return invalid_req

        return DeleteLecturerRequestObject(id=id, current_admin=current_admin)


class DeleteLecturerUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        lecturer_repository: LecturerRepository = Depends(LecturerRepository),
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.lecturer_repository = lecturer_repository
        self.subject_repository = subject_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: DeleteLecturerRequestObject):
        lecturer: Optional[LecturerModel] = self.lecturer_repository.get_by_id(req_object.id)
        if not lecturer:
            return response_object.ResponseFailure.build_not_found_error("Giảng viên không tồn tại")

        subject = self.subject_repository.find_one(conditions={"lecturer": lecturer.id})

        if subject is not None:
            return response_object.ResponseFailure.build_parameters_error(
                "Không thể xóa giảng viên có liên kết với môn học"
            )
        try:
            self.lecturer_repository.delete(id=lecturer.id)

            current_season = get_current_season_value()
            self.background_tasks.add_task(
                self.audit_log_repository.create,
                AuditLogInDB(
                    type=AuditLogType.DELETE,
                    endpoint=Endpoint.LECTURER,
                    season=current_season,
                    author=req_object.current_admin,
                    author_email=req_object.current_admin.email,
                    author_name=req_object.current_admin.full_name,
                    author_roles=req_object.current_admin.roles,
                    description=json.dumps(
                        LecturerInDB.model_validate(lecturer).model_dump(exclude_none=True), default=str
                    ),
                ),
            )
            return {"success": True}
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went error.")
