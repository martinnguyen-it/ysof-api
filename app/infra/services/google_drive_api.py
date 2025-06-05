from typing import Optional

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
import io
from fastapi import HTTPException, UploadFile
import logging

from app.config import settings
from app.domain.upload.entity import AddPermissionDriveFile, GoogleDriveAPIRes
from app.domain.upload.enum import RolePermissionGoogleEnum, TypePermissionGoogleEnum

logger = logging.getLogger(__name__)


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]


class GoogleDriveAPIService:
    def __init__(self):
        self._creds = self._get_oauth_token()
        self.service = build("drive", "v3", credentials=self._creds)

    def _get_oauth_token(self):
        creds = None
        try:
            creds, _ = google.auth.load_credentials_from_file(
                settings.KEY_PATH_GCLOUD, scopes=SCOPES
            )
        except Exception:
            logger.error("Failed to retrieve default credentials gcloud.")
            raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")

        if creds is None:
            raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")
        return creds

    def create(
        self, file: UploadFile, name: Optional[str] = None, folder_id: Optional[str] = None
    ) -> GoogleDriveAPIRes:
        try:
            # Creating file metadata
            file_metadata = {
                "name": name if name else file.filename,
                "parents": [settings.FOLDER_GCLOUD_ID if folder_id is None else folder_id],
            }

            # Creating media upload object
            media = MediaIoBaseUpload(
                io.BytesIO(file.file.read()), mimetype=file.content_type, resumable=True
            )

            # Uploading the file
            res = (
                self.service.files()
                .create(body=file_metadata, media_body=media, fields="id,mimeType,name")
                .execute()
            )
            data = GoogleDriveAPIRes.model_validate(res)

            # Add permission for file
            self.add_permission(
                file_id=data.id,
                role=RolePermissionGoogleEnum.READER,
                type=TypePermissionGoogleEnum.ANYONE,
            )

            return data

        except HttpError as error:
            if "File not found" in str(error):
                logger.error(f"Parent folder with ID {settings.FOLDER_GCLOUD_ID} not found.")
            else:
                logger.error(f"An error occurred when uploading the file: {error}")
            raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")

    def delete(self, file_id: str):
        try:
            self.service.files().delete(fileId=file_id).execute()

        except HttpError as error:
            if "File not found" in str(error):
                logger.error(
                    f"Parent folder with ID {settings.FOLDER_GCLOUD_ID} not found. >> {error}"
                )
                raise HTTPException(status_code=400, detail="Không tìm thấy file.")
            else:
                logger.error(f"An error occurred when deleting the file: {error}")
                raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")

    def update_file_name(self, file_id: str, new_name: str):
        try:
            # Replace "New_File_Name" with the desired new name
            updated_file_metadata = {"name": new_name}
            self.service.files().update(fileId=file_id, body=updated_file_metadata).execute()

        except HttpError as error:
            if "File not found" in str(error):
                logger.error(
                    f"Parent folder with ID {settings.FOLDER_GCLOUD_ID} not found. >> {error}"
                )
                raise HTTPException(status_code=400, detail="Không tìm thấy file.")
            else:
                logger.error(f"An error occurred when deleting the file: {error}")
                raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")

    def get(self, file_id: str, fields: str = "id,mimeType,name"):
        try:
            res = self.service.files().get(fileId=file_id, fields=fields).execute()
            return res

        except HttpError as error:
            if "File not found" in str(error):
                logger.error(
                    f"Parent folder with ID {settings.FOLDER_GCLOUD_ID} not found. >> {error}"
                )
                raise HTTPException(status_code=400, detail="Không tìm thấy file.")
            else:
                logger.error(f"An error occurred when get the file: {error}")
                raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")

    def change_file_folder_parents(
        self, file_id: str, previous_parents: list[str] | None = None, folder_id: str | None = None
    ):
        try:
            if previous_parents is None:
                file = self.get(file_id, "parents")
                previous_parents = ",".join(file.get("parents"))

            # Move the file to the new folder
            self.service.files().update(
                fileId=file_id,
                addParents=folder_id if folder_id else settings.FOLDER_GCLOUD_ID,
                removeParents=previous_parents,
                fields="parents",
            ).execute()
        except HttpError as error:
            if "File not found" in str(error):
                logger.error(f"Parent folder with ID {settings.FOLDER_GCLOUD_ID} not found.")
            else:
                logger.error(f"An error occurred when uploading the file: {error}")
            raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")

    def add_permission(
        self,
        file_id: str,
        type: TypePermissionGoogleEnum,
        role: RolePermissionGoogleEnum = RolePermissionGoogleEnum.READER,
        email_address: str | None = None,
    ):
        try:
            permission = {"role": role, "type": type}
            if email_address:
                permission = {**permission, "emailAddress": email_address}

            self.service.permissions().create(fileId=file_id, body=permission).execute()
        except HttpError as error:
            logger.error(f"An error occurred when change permission the file: {error}")
            raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")

    def add_multi_permissions(self, file_id: str, permissions: list[AddPermissionDriveFile]):
        try:

            def callback(_request_id, _response, exception):
                if exception:
                    # Handle error
                    logger.error(f"An error occurred when change permission the file: {exception}")

            batch = self.service.new_batch_http_request(callback=callback)
            for permission in permissions:
                data = {"role": permission.role, "type": permission.type}
                if permission.email_address:
                    data = {**data, "emailAddress": permission.email_address}
                batch.add(
                    self.service.permissions().create(
                        fileId=file_id,
                        body=data,
                        fields="id",
                    )
                )
            batch.execute()
        except HttpError as error:
            logger.error(f"An error occurred when change permission the file: {error}")
            raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")

    def duplicate_file(self, source_file_id: str, new_file_name: str):
        try:
            body = {"name": new_file_name}
            request = self.service.files().copy(fileId=source_file_id, body=body)
            response = request.execute()
            return response
        except HttpError as error:
            logger.error(f"An error occurred when duplicate the file: {error}")
            raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")
