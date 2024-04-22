from datetime import datetime
from typing import Optional, List
from pydantic import ConfigDict, validator

from app.domain.admin.field import PydanticAdminType
from app.domain.document.enum import DocumentType, GoogleFileType
from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin, Pagination, PayloadWithFile
from app.domain.shared.enum import AdminRole


class AdminInDocument(BaseEntity):
    id: str
    full_name: str
    avatar: Optional[str] = None
    active: Optional[bool] = False


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
    season: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class DocumentInCreatePayloadBase(BaseEntity):
    name: str
    type: DocumentType
    description: Optional[str] = None
    role: AdminRole
    label: Optional[list[str]] = None


class DocumentFileInCreatePayload(DocumentInCreatePayloadBase, PayloadWithFile):
    pass


class DocumentGoogleInCreatePayload(DocumentInCreatePayloadBase):
    google_type_file: GoogleFileType


class DocumentInCreate(DocumentBase):
    """_summary_
        After upload file and get infor from gdrive
    Args:
        DocumentBase (_type_): _description_
    """

    pass


class Document(DocumentBase):
    """
    Admin domain entity
    """

    id: str
    author: AdminInDocument
    season: int
    created_at: datetime
    updated_at: datetime
    webViewLink: Optional[str] = None

    @validator("webViewLink", pre=True, always=True)
    def create_web_link(cls, v, values):
        if values["mimeType"] == "application/vnd.google-apps.spreadsheet":
            return f"https://docs.google.com/spreadsheets/d/{values['file_id']}"
        if values["mimeType"] in ["application/vnd.google-apps.document", "application/vnd.google-apps.kix"]:
            return f"https://docs.google.com/document/d/{values['file_id']}"
        return f"https://drive.google.com/file/d/{values['file_id']}/view?usp=drivesdk"


class ManyDocumentsInResponse(BaseEntity):
    pagination: Optional[Pagination] = None
    data: Optional[List[Document]] = None


class DocumentInUpdateBase(BaseEntity):
    name: Optional[str] = None
    type: Optional[DocumentType] = None
    description: Optional[str] = None
    role: Optional[str] = None
    label: Optional[list[str]] = None


class DocumentInUpdatePayload(DocumentInUpdateBase, PayloadWithFile):
    pass


class DocumentInUpdate(DocumentInUpdateBase):
    file_id: str | None = None
    mimeType: Optional[str] = None
    thumbnailLink: Optional[str] = None


class DocumentInUpdateTime(DocumentInUpdate):
    updated_at: datetime = datetime.now()
