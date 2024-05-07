from typing import Optional
from pydantic import BaseModel
from app.domain.upload.enum import RolePermissionGoogleEnum, TypePermissionGoogleEnum


class GoogleDriveAPIRes(BaseModel):
    id: str
    mimeType: str
    name: Optional[str] = None


class ImageRes(BaseModel):
    url: str


class AddPermissionDriveFile(BaseModel):
    type: TypePermissionGoogleEnum
    role: RolePermissionGoogleEnum = RolePermissionGoogleEnum.READER
    email_address: str | None = None
