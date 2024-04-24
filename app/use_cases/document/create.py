import json
from typing import Optional
from fastapi import Depends, BackgroundTasks

from app.domain.admin.entity import AdminInDB
from app.models.document import DocumentModel
from app.shared import request_object, use_case

from app.domain.document.entity import Document, DocumentInCreate, DocumentInDB, AdminInDocument
from app.infra.document.document_repository import DocumentRepository
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.domain.audit_log.entity import AuditLogInDB
from app.shared.utils.general import get_current_season_value


class CreateDocumentRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_admin: AdminModel, document_in: DocumentInCreate = None) -> None:
        self.document_in = document_in
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls, current_admin: AdminModel, payload: Optional[DocumentInCreate] = None
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if not payload.file_id:
            invalid_req.add_error("payload.file_id", "Lỗi khi upload file")

        if invalid_req.has_errors():
            return invalid_req

        return CreateDocumentRequestObject(document_in=payload, current_admin=current_admin)


class CreateDocumentUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        document_repository: DocumentRepository = Depends(DocumentRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.document_repository = document_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: CreateDocumentRequestObject):
        current_season = get_current_season_value()

        obj_in: DocumentInDB = DocumentInDB(
            **req_object.document_in.model_dump(), season=current_season, author=req_object.current_admin
        )
        document: DocumentModel = self.document_repository.create(document=obj_in)

        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.CREATE,
                endpoint=Endpoint.DOCUMENT,
                season=current_season,
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps(
                    req_object.document_in.model_dump(exclude_none=True), default=str, ensure_ascii=False
                ),
            ),
        )

        author: AdminInDB = AdminInDB.model_validate(document.author)
        return Document(
            **DocumentInDB.model_validate(document).model_dump(exclude=({"author"})),
            author=AdminInDocument(**author.model_dump(), active=author.active()),
        )
