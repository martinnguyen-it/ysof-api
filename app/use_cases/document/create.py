from typing import Optional
from fastapi import Depends

from app.config import settings
from app.domain.admin.entity import AdminInDB
from app.infra.security.security_service import get_password_hash, generate_random_password
from app.models.document import DocumentModel
from app.shared import request_object, use_case, response_object

from app.domain.document.entity import Document, DocumentInCreate, DocumentInDB, AdminInDocument
from app.infra.document.document_repository import DocumentRepository


class CreateDocumentRequestObject(request_object.ValidRequestObject):
    def __init__(self, document_in: DocumentInCreate = None) -> None:
        self.document_in = document_in

    @classmethod
    def builder(cls, payload: Optional[DocumentInCreate] = None) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if not payload.file_id:
            invalid_req.add_error("payload.file_id", "Lỗi khi upload file")

        if invalid_req.has_errors():
            return invalid_req

        return CreateDocumentRequestObject(document_in=payload)


class CreateDocumentUseCase(use_case.UseCase):
    def __init__(self, document_repository: DocumentRepository = Depends(DocumentRepository)):
        self.document_repository = document_repository

    def process_request(self, req_object: CreateDocumentRequestObject):
        document_in: DocumentInCreate = req_object.document_in
        obj_in: DocumentInDB = DocumentInDB(
            **document_in.model_dump(),
            season=settings.CURRENT_SEASON,
        )
        document: DocumentModel = self.document_repository.create(
            document=obj_in)
        author: AdminInDB = AdminInDB.model_validate(document.author)

        return Document(**DocumentInDB.model_validate(document).model_dump(exclude=({"author"})),
                        author=AdminInDocument(**author.model_dump()), active=not author.disabled())
