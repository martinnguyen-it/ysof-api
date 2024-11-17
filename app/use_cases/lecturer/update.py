import json
from typing import Optional
from fastapi import Depends, BackgroundTasks
from app.models.lecturer import LecturerModel
from app.shared import request_object, use_case, response_object

from app.domain.lecturer.entity import (
    Lecturer,
    LecturerInDB,
    LecturerInUpdate,
    LecturerInUpdateTime,
)
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.infra.document.document_repository import DocumentRepository
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.domain.audit_log.entity import AuditLogInDB
from app.shared.utils.general import get_current_season_value


class UpdateLecturerRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str, current_admin: AdminModel, obj_in: LecturerInUpdate) -> None:
        self.id = id
        self.obj_in = obj_in
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls, id: str, current_admin: AdminModel, payload: Optional[LecturerInUpdate] = None
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateLecturerRequestObject(id=id, obj_in=payload, current_admin=current_admin)


class UpdateLecturerUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        document_repository: DocumentRepository = Depends(DocumentRepository),
        lecturer_repository: LecturerRepository = Depends(LecturerRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.lecturer_repository = lecturer_repository
        self.document_repository = document_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: UpdateLecturerRequestObject):
        lecturer: Optional[LecturerModel] = self.lecturer_repository.get_by_id(req_object.id)
        if not lecturer:
            return response_object.ResponseFailure.build_not_found_error("Giảng viên không tồn tại")

        self.lecturer_repository.update(
            id=lecturer.id, data=LecturerInUpdateTime(**req_object.obj_in.model_dump())
        )
        lecturer.reload()

        current_season = get_current_season_value()
        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.UPDATE,
                endpoint=Endpoint.LECTURER,
                season=current_season,
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps(
                    LecturerInDB.model_validate(lecturer).model_dump(exclude_none=True),
                    default=str,
                    ensure_ascii=False,
                ),
            ),
        )

        return Lecturer(**LecturerInDB.model_validate(lecturer).model_dump())
