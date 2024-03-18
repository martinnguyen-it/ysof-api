from datetime import datetime
from typing import Optional, List
from pydantic import ConfigDict

from app.domain.admin.field import PydanticAdminType
from app.domain.document.enum import DocumentType
from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin, Pagination, PayloadWithFile


class AdminInDocument(BaseEntity):
    id: str
    full_name: str
    avatar: Optional[str] = None
    active: Optional[bool] = True


class DocumentBase(BaseEntity):
    file_id: str
    mimeType: Optional[str] = None
    name: str
    thumbnailLink: Optional[str] = None
    role: str
    type: DocumentType
    description: Optional[str] = None
    label: Optional[list[str]] = None


class DocumentInDB(IDModelMixin, DateTimeModelMixin, DocumentBase):
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    author: PydanticAdminType
    session: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class DocumentInCreatePayload(BaseEntity, PayloadWithFile):
    name: str
    type: DocumentType
    description: Optional[str] = None
    role: Optional[str] = None
    label: Optional[list[str]] = None


class DocumentInCreate(DocumentBase):
    """_summary_
        After upload file and get infor from gdrive
    Args:
        DocumentBase (_type_): _description_
    """
    author: PydanticAdminType


class Document(DocumentBase):
    """
    Admin domain entity
    """
    id: str
    author: AdminInDocument
    session: int
    created_at: datetime
    updated_at: datetime


class ManyDocumentsInResponse(BaseEntity):
    pagination: Optional[Pagination] = None
    data: Optional[List[Document]] = None


class DocumentInUpdate(BaseEntity, PayloadWithFile):
    name: Optional[str] = None
    type: Optional[DocumentType] = None
    description: Optional[str] = None
    role: Optional[str] = None
    label: Optional[list[str]] = None
