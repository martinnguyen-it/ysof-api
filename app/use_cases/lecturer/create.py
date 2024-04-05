import json
from typing import Optional
from fastapi import Depends, BackgroundTasks

from app.models.lecturer import LecturerModel
from app.shared import request_object, use_case

from app.domain.lecturer.entity import Lecturer, LecturerInCreate, LecturerInDB
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.models.admin import AdminModel
from app.infra.season.season_repository import SeasonRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint


class CreateLecturerRequestObject(request_object.ValidRequestObject):
    def __init__(self,
                 current_admin: AdminModel,
                 lecturer_in: LecturerInCreate) -> None:
        self.lecturer_in = lecturer_in
        self.current_admin = current_admin

    @classmethod
    def builder(cls,
                current_admin: AdminModel,
                payload: Optional[LecturerInCreate] = None
                ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return CreateLecturerRequestObject(lecturer_in=payload, current_admin=current_admin)


class CreateLecturerUseCase(use_case.UseCase):
    def __init__(self,
                 background_tasks: BackgroundTasks,
                 lecturer_repository: LecturerRepository = Depends(
                     LecturerRepository),
                 season_repository: SeasonRepository = Depends(
                     SeasonRepository),
                 audit_log_repository: AuditLogRepository = Depends(AuditLogRepository)):
        self.lecturer_repository = lecturer_repository
        self.background_tasks = background_tasks
        self.season_repository = season_repository
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: CreateLecturerRequestObject):
        lecturer: LecturerModel = self.lecturer_repository.create(
            lecturer=LecturerInDB(
                **req_object.lecturer_in.model_dump(),
            ))

        self.background_tasks.add_task(self.audit_log_repository.create, AuditLogInDB(
            type=AuditLogType.CREATE,
            endpoint=Endpoint.LECTURER,
            season=self.season_repository.get_current_season().season,
            author=req_object.current_admin,
            author_email=req_object.current_admin.email,
            author_name=req_object.current_admin.full_name,
            author_roles=req_object.current_admin.roles,
            description=json.dumps(
                req_object.lecturer_in.model_dump(exclude_none=True), default=str)
        ))

        return Lecturer(**LecturerInDB.model_validate(lecturer).model_dump())
