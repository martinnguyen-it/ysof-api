from typing import Optional

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
import io
from fastapi import HTTPException, UploadFile
import logging

from app.config import settings
from app.domain.upload.entity import GoogleDriveAPIRes
from cachetools import TTLCache

logger = logging.getLogger(__name__)
cache = TTLCache(maxsize=1, ttl=60 * 5)  # Cache 1 item for 5 minutes


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]


class GoogleDriveApiService:
    def __init__(self):
        self.service = build("drive", "v3", credentials=self._get_oauth_token())

    def _get_oauth_token(self):
        creds = None
        try:
            creds, _ = google.auth.load_credentials_from_file(settings.KEY_PATH_GCLOUD, scopes=SCOPES)
        except Exception:
            logger.error("Failed to retrieve default credentials gcloud.")
            raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")

        if creds is None:
            raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")
        return creds

    def create(self, file: UploadFile, name: Optional[str] = None) -> GoogleDriveAPIRes:
        try:
            # Creating file metadata
            file_metadata = {"name": name if name else file.filename, "parents": [settings.FOLDER_GCLOUD_ID]}

            # Creating media upload object
            media = MediaIoBaseUpload(io.BytesIO(file.file.read()), mimetype=file.content_type, resumable=True)

            # Uploading the file
            res = (
                self.service.files()
                .create(body=file_metadata, media_body=media, fields="id,mimeType,name,thumbnailLink")
                .execute()
            )
            return GoogleDriveAPIRes.model_validate(res)

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
                logger.error(f"Parent folder with ID {settings.FOLDER_GCLOUD_ID} not found. >> {error}")
                raise HTTPException(status_code=400, detail="Không tìm thấy file.")
            else:
                logger.error(f"An error occurred when deleting the file: {error}")
                raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")

    def update(self, file_id: str, new_name: str):
        try:
            # Replace "New_File_Name" with the desired new name
            updated_file_metadata = {"name": new_name}
            self.service.files().update(fileId=file_id, body=updated_file_metadata).execute()

        except HttpError as error:
            if "File not found" in str(error):
                logger.error(f"Parent folder with ID {settings.FOLDER_GCLOUD_ID} not found. >> {error}")
                raise HTTPException(status_code=400, detail="Không tìm thấy file.")
            else:
                logger.error(f"An error occurred when deleting the file: {error}")
                raise HTTPException(status_code=400, detail="Hệ thống Cloud bị lỗi.")
