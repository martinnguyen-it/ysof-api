from app.config import settings
import math
from typing import Optional, List, Dict, Any
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.document.entity import (AdminInDocument, Document, DocumentInDB,
                                        ManyDocumentsInResponse)
from app.domain.shared.entity import Pagination
from app.models.document import DocumentModel
from app.infra.document.document_repository import DocumentRepository
from app.models.admin import AdminModel
from app.domain.document.enum import DocumentType
from app.domain.admin.entity import AdminInDB
from app.domain.shared.enum import AdminRole
from app.shared.constant import SUPER_ADMIN


class ListDocumentsRequestObject(request_object.ValidRequestObject):
    def __init__(self, author: AdminModel, page_index: int, page_size: int, search: Optional[str] = None,
                 label: Optional[list[str]] = None, sort: Optional[dict[str, int]] = None):
        self.page_index = page_index
        self.page_size = page_size
        self.search = search
        self.sort = sort
        self.label = label
        self.author = author

    @classmethod
    def builder(cls, author: AdminModel, page_index: int, page_size: int, search: Optional[str] = None,
                label: Optional[list[str]] = None, sort: Optional[dict[str, int]] = None
                ):
        return ListDocumentsRequestObject(author=author, page_index=page_index, label=label,
                                          page_size=page_size, search=search, sort=sort)


class ListDocumentsUseCase(use_case.UseCase):
    def __init__(self, document_repository: DocumentRepository = Depends(DocumentRepository)):
        self.document_repository = document_repository

    def process_request(self, req_object: ListDocumentsRequestObject):
        is_super_admin = False
        for role in req_object.author.roles:
            if role in SUPER_ADMIN:
                is_super_admin = True
                break

        match_pipeline = [
            {
                "$match": {
                    "$or": [
                        {"type": DocumentType.ANNUAL},
                        {
                            "$and": [
                                {
                                    "$or": [
                                        {"type": DocumentType.COMMON},
                                        {"type": DocumentType.INTERNAL}
                                        if is_super_admin else
                                        {"$and": [
                                            {"type": DocumentType.INTERNAL},
                                            {"role": {"$in": req_object.author.roles}}
                                        ]},
                                    ]
                                },
                                {"session": settings.CURRENT_SEASON}
                            ]
                        }
                    ]
                }
            }
        ]

        if isinstance(req_object.search, str):
            match_pipeline.append({
                "$match": {
                    "name": {"$regex": req_object.search, "$options": "i"}
                }
            })

        if isinstance(req_object.label, list) and len(req_object.label) > 0:
            match_pipeline.append({
                "$match": {
                    "label": {"$in": req_object.label}
                }
            })

        documents: List[DocumentModel] = self.document_repository.list(
            page_size=req_object.page_size,
            page_index=req_object.page_index,
            sort=req_object.sort,
            match_pipeline=match_pipeline
        )

        total = self.document_repository.count_list(
            match_pipeline=match_pipeline
        )

        data: Optional[list[Document]] = []
        for doc in documents:
            author: AdminInDB = AdminInDB.model_validate(
                doc.author)
            data.append(Document(**DocumentInDB.model_validate(doc).model_dump(exclude=({"author"})),
                                 author=AdminInDocument(**author.model_dump()),
                                 active=not author.disabled()))

        return ManyDocumentsInResponse(
            pagination=Pagination(
                total=total, page_index=req_object.page_index, total_pages=math.ceil(
                    total / req_object.page_size)
            ),
            data=data,
        )
