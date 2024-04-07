import json
from typing import Optional
from fastapi import Depends, BackgroundTasks
from app.models.student import StudentModel
from app.shared import request_object, use_case, response_object

from app.domain.student.entity import Student, StudentInDB, StudentInUpdate, StudentInUpdateTime
from app.infra.student.student_repository import StudentRepository
from app.models.admin import AdminModel
from app.infra.season.season_repository import SeasonRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint


class UpdateStudentRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str, current_admin: AdminModel, obj_in: StudentInUpdate) -> None:
        self.id = id
        self.obj_in = obj_in
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls, id: str, current_admin: AdminModel, payload: Optional[StudentInUpdate] = None
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid id")

        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateStudentRequestObject(id=id, obj_in=payload, current_admin=current_admin)


class UpdateStudentUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        student_repository: StudentRepository = Depends(StudentRepository),
        season_repository: SeasonRepository = Depends(SeasonRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.student_repository = student_repository
        self.season_repository = season_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: UpdateStudentRequestObject):
        student: Optional[StudentModel] = self.student_repository.get_by_id(req_object.id)
        if not student:
            return response_object.ResponseFailure.build_not_found_error("Học viên không tồn tại")

        current_season: int = self.season_repository.get_current_season().season

        self.student_repository.update(id=student.id, data=StudentInUpdateTime(**req_object.obj_in.model_dump()))
        student.reload()

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
                description=json.dumps(req_object.obj_in.model_dump(exclude_none=True), default=str),
            ),
        )

        return Student(**StudentInDB.model_validate(student).model_dump())
