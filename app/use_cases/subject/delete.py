import json
from typing import Optional

from fastapi import Depends, BackgroundTasks
from app.infra.subject.subject_repository import SubjectRepository
from app.shared import request_object, response_object, use_case
from app.models.subject import SubjectModel
from app.models.admin import AdminModel
from app.shared.constant import SUPER_ADMIN
from app.shared.common_exception import forbidden_exception
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.domain.subject.entity import SubjectInDB
from app.shared.utils.general import get_current_season_value
from app.infra.subject.subject_registration_repository import SubjectRegistrationRepository


class DeleteSubjectRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str, current_admin: AdminModel):
        self.id = id
        self.current_admin = current_admin

    @classmethod
    def builder(cls, id: str, current_admin: AdminModel) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid id")

        if invalid_req.has_errors():
            return invalid_req

        return DeleteSubjectRequestObject(id=id, current_admin=current_admin)


class DeleteSubjectUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        subject_registration_repository: SubjectRegistrationRepository = Depends(SubjectRegistrationRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.subject_repository = subject_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository
        self.subject_registration_repository = subject_registration_repository

    def process_request(self, req_object: DeleteSubjectRequestObject):
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(req_object.id)
        if not subject:
            return response_object.ResponseFailure.build_not_found_error("Môn học không tồn tại")

        subject_registration = self.subject_registration_repository.find_one({"subject": subject.id})
        if subject_registration:
            return response_object.ResponseFailure.build_parameters_error(
                "Không thể xóa môn học đã có học viên đăng ký"
            )

        current_season = get_current_season_value()
        if subject.season != current_season and not any(role in req_object.current_admin.roles for role in SUPER_ADMIN):
            raise forbidden_exception

        try:
            self.subject_repository.delete(id=subject.id)
            self.background_tasks.add_task(
                self.audit_log_repository.create,
                AuditLogInDB(
                    type=AuditLogType.DELETE,
                    endpoint=Endpoint.SUBJECT,
                    season=current_season,
                    author=req_object.current_admin,
                    author_email=req_object.current_admin.email,
                    author_name=req_object.current_admin.full_name,
                    author_roles=req_object.current_admin.roles,
                    description=json.dumps(
                        SubjectInDB.model_validate(subject).model_dump(exclude_none=True), default=str
                    ),
                ),
            )
            return {"success": True}
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went error.")
