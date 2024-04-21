from fastapi import Depends, HTTPException
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.infra.services.google_drive_api import GoogleDriveAPIService
import logging
from app.domain.upload.enum import RolePermissionGoogleEnum
from app.domain.upload.entity import GoogleDriveAPIRes

logger = logging.getLogger(__name__)


class GoogleDocumentAPIService:
    def __init__(
        self,
        google_drive_api_service: GoogleDriveAPIService = Depends(GoogleDriveAPIService),
    ):
        self.google_drive_api_service = google_drive_api_service
        self.service = build("docs", "v1", credentials=self.google_drive_api_service._creds)

    def create(self, name: str, email_owner: str):
        try:
            document_meta = {"title": name}
            document = self.service.documents().create(body=document_meta, fields="documentId").execute()
        except HttpError as error:
            logger.error(f"An error occurred when create document: {error}")
            raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")

        file_id = document.get("documentId")

        file_info = self.google_drive_api_service.get(file_id=file_id, fields="id,mimeType,name,thumbnailLink,parents")
        previous_parents = ",".join(file_info.get("parents"))
        self.google_drive_api_service.change_file_folder_parents(file_id=file_id, previous_parents=previous_parents)

        self.google_drive_api_service.add_permission(
            file_id=file_id, email_address=email_owner, role=RolePermissionGoogleEnum.WRITER
        )
        return GoogleDriveAPIRes.model_validate(file_info)
