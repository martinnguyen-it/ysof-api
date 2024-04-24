import json
from typing import Optional

from fastapi import Depends, BackgroundTasks
from app.infra.student.student_repository import StudentRepository
from app.shared import request_object, response_object, use_case
from app.models.student import StudentModel
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.domain.student.entity import StudentInDB
from app.shared.utils.general import get_current_season_value


class DeleteStudentRequestObject(request_object.ValidRequestObject):
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

        return DeleteStudentRequestObject(id=id, current_admin=current_admin)


class DeleteStudentUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        student_repository: StudentRepository = Depends(StudentRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.student_repository = student_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: DeleteStudentRequestObject):
        student: Optional[StudentModel] = self.student_repository.get_by_id(req_object.id)
        if not student:
            return response_object.ResponseFailure.build_not_found_error("Môn học không tồn tại")

        current_season = get_current_season_value()
        try:
            self.student_repository.delete(id=req_object.id)
            self.background_tasks.add_task(
                self.audit_log_repository.create,
                AuditLogInDB(
                    type=AuditLogType.DELETE,
                    endpoint=Endpoint.STUDENT,
                    season=current_season,
                    author=req_object.current_admin,
                    author_email=req_object.current_admin.email,
                    author_name=req_object.current_admin.full_name,
                    author_roles=req_object.current_admin.roles,
                    description=json.dumps(
                        StudentInDB.model_validate(student).model_dump(exclude_none=True),
                        default=str,
                        ensure_ascii=False,
                    ),
                ),
            )
            return {"success": True}
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went error.")
