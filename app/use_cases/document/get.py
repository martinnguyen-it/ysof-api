from fastapi import Depends
from typing import Optional
from app.shared import request_object, response_object, use_case
from app.domain.document.entity import AdminInDocument, Document, DocumentInDB
from app.infra.document.document_repository import DocumentRepository
from app.models.document import DocumentModel
from app.domain.admin.entity import AdminInDB


class GetDocumentRequestObject(request_object.ValidRequestObject):
    def __init__(self, document_id: str):
        self.document_id = document_id

    @classmethod
    def builder(cls, document_id: str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not id:
            invalid_req.add_error("id", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return GetDocumentRequestObject(document_id=document_id)


class GetDocumentCase(use_case.UseCase):
    def __init__(self, document_repository: DocumentRepository = Depends(DocumentRepository)):
        self.document_repository = document_repository

    def process_request(self, req_object: GetDocumentRequestObject):
        document: Optional[DocumentModel] = self.document_repository.get_by_id(
            document_id=req_object.document_id
        )
        if not document:
            return response_object.ResponseFailure.build_not_found_error(
                message="Tài liệu không tồn tại"
            )

        author: AdminInDB = AdminInDB.model_validate(document.author)
        return Document(
            **DocumentInDB.model_validate(document).model_dump(exclude=({"author"})),
            author=AdminInDocument(**author.model_dump(), active=author.active()),
        )
