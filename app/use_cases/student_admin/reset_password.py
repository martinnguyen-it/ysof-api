from fastapi import Depends, BackgroundTasks
import json
from typing import Optional
from app.shared import request_object, response_object, use_case
from app.domain.student.entity import ResetPasswordResponse
from app.infra.student.student_repository import StudentRepository
from app.models.student import StudentModel
from app.infra.season.season_repository import SeasonRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.models.admin import AdminModel
from app.infra.security.security_service import generate_random_password, get_password_hash


class ResetPasswordStudentRequestObject(request_object.ValidRequestObject):
    def __init__(self, student_id: str, current_admin: AdminModel):
        self.student_id = student_id
        self.current_admin = current_admin

    @classmethod
    def builder(cls, student_id: str, current_admin: AdminModel) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not id:
            invalid_req.add_error("id", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return ResetPasswordStudentRequestObject(student_id=student_id, current_admin=current_admin)


class ResetPasswordStudentUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        student_repository: StudentRepository = Depends(StudentRepository),
        season_repository: SeasonRepository = Depends(SeasonRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.student_repository = student_repository
        self.background_tasks = background_tasks
        self.season_repository = season_repository
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: ResetPasswordStudentRequestObject):
        student: Optional[StudentModel] = self.student_repository.get_by_id(student_id=req_object.student_id)
        if not student:
            return response_object.ResponseFailure.build_not_found_error(message="Học viên không tồn tại")
        current_season: int = self.season_repository.get_current_season().season

        password = generate_random_password()
        self.student_repository.update(id=student.id, data={"password": get_password_hash(password)})

        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.UPDATE,
                endpoint=Endpoint.STUDENT,
                season=current_season,
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps({"id": student.id, "message": "Updated password"}, default=str),
            ),
        )

        return ResetPasswordResponse(email=student.email, password=password)
