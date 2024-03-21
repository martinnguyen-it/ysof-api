from typing import Optional
from fastapi import Depends
from app.models.document import DocumentModel
from app.shared import request_object, use_case, response_object

from app.domain.document.entity import (AdminInDocument, Document, DocumentInDB, DocumentInUpdate,
                                        DocumentInUpdateTime)
from app.infra.document.document_repository import DocumentRepository
from app.domain.shared.enum import AdminRole
from app.shared.constant import SUPER_ADMIN
from app.infra.services.google_drive_api import GoogleDriveApiService
from app.domain.admin.entity import AdminInDB


class UpdateDocumentRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str,
                 admin_roles: list[AdminRole],
                 obj_in: DocumentInUpdate) -> None:
        self.id = id
        self.obj_in = obj_in
        self.admin_roles = admin_roles

    @classmethod
    def builder(cls, id: str,
                admin_roles: list[AdminRole],
                payload: Optional[DocumentInUpdate] = None
                ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateDocumentRequestObject(id=id, obj_in=payload, admin_roles=admin_roles)


class UpdateDocumentUseCase(use_case.UseCase):
    def __init__(self,
                 google_drive_api_service: GoogleDriveApiService = Depends(
                     GoogleDriveApiService),
                 document_repository: DocumentRepository = Depends(DocumentRepository)):
        self.google_drive_api_service = google_drive_api_service
        self.document_repository = document_repository

    def process_request(self, req_object: UpdateDocumentRequestObject):
        document: Optional[DocumentModel] = self.document_repository.get_by_id(
            req_object.id)
        if not document:
            return response_object.ResponseFailure.build_not_found_error("Tài liệu không tồn tại")
        if document.role not in req_object.admin_roles and \
                not any(role in SUPER_ADMIN for role in req_object.admin_roles):
            return response_object.ResponseFailure.build_not_found_error("Bạn không có quyền sửa")

        if isinstance(req_object.obj_in.name, str):
            self.google_drive_api_service.update(
                document.file_id, req_object.obj_in.name)

        self.document_repository.update(id=document.id, data=DocumentInUpdateTime(
            **req_object.obj_in.model_dump(exclude=({"updated_at"}))))
        document.reload()

        author: AdminInDB = AdminInDB.model_validate(document.author)
        return Document(**DocumentInDB.model_validate(document).model_dump(exclude=({"author"})),
                        author=AdminInDocument(**author.model_dump()), active=not author.disabled())
