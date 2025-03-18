import json
from typing import Optional
from fastapi import Depends, BackgroundTasks
from app.infra.tasks.drive_file import delete_file_drive_task
from app.models.document import DocumentModel
from app.shared import request_object, use_case, response_object

from app.domain.document.entity import (
    AdminInDocument,
    Document,
    DocumentInDB,
    DocumentInUpdate,
    DocumentInUpdateTime,
)
from app.infra.document.document_repository import DocumentRepository
from app.shared.constant import SUPER_ADMIN
from app.infra.services.google_drive_api import GoogleDriveAPIService
from app.domain.admin.entity import AdminInDB
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.domain.audit_log.entity import AuditLogInDB
from app.shared.common_exception import forbidden_exception
from app.shared.utils.general import get_current_season_value


class UpdateDocumentRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str, current_admin: AdminModel, obj_in: DocumentInUpdate) -> None:
        self.id = id
        self.obj_in = obj_in
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls, id: str, current_admin: AdminModel, payload: Optional[DocumentInUpdate] = None
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateDocumentRequestObject(id=id, obj_in=payload, current_admin=current_admin)


class UpdateDocumentUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        google_drive_api_service: GoogleDriveAPIService = Depends(GoogleDriveAPIService),
        document_repository: DocumentRepository = Depends(DocumentRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.google_drive_api_service = google_drive_api_service
        self.document_repository = document_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: UpdateDocumentRequestObject):
        document: Optional[DocumentModel] = self.document_repository.get_by_id(req_object.id)
        if not document:
            return response_object.ResponseFailure.build_not_found_error("Tài liệu không tồn tại")
        if document.role not in req_object.current_admin.roles and not any(
            role in SUPER_ADMIN for role in req_object.current_admin.roles
        ):
            return forbidden_exception

        if isinstance(req_object.obj_in.name, str) and req_object.obj_in.file_id is None:
            self.background_tasks.add_task(
                self.google_drive_api_service.update_file_name,
                document.file_id,
                req_object.obj_in.name,
            )

        if req_object.obj_in.file_id:
            delete_file_drive_task.delay(document.file_id)

        self.document_repository.update(
            id=document.id, data=DocumentInUpdateTime(**req_object.obj_in.model_dump())
        )
        document.reload()

        current_season = get_current_season_value()
        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.UPDATE,
                endpoint=Endpoint.DOCUMENT,
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

        author: AdminInDB = AdminInDB.model_validate(document.author)
        return Document(
            **DocumentInDB.model_validate(document).model_dump(exclude=({"author"})),
            author=AdminInDocument(**author.model_dump(), active=author.active()),
        )
