import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
import io
from fastapi import HTTPException, UploadFile
import logging

from app.config import settings
from app.domain.upload.entity import GoogleDriveAPIRes

logger = logging.getLogger(__name__)


class GoogleDriveApiService:
    def __init__(self):
        self.service = build(
            "drive", "v3", credentials=self._get_oauth_token())

    def _get_oauth_token(self):
        creds = None
        try:
            creds, _ = google.auth.load_credentials_from_file(settings.KEY_PATH_GCLOUD,
                                                              scopes=['https://www.googleapis.com/auth/drive'])
        except Exception:
            logger.error("Failed to retrieve default credentials gcloud.")
            raise HTTPException(
                status_code=400, detail="Hệ thống Cloud bị lỗi."
            )

        if creds is None:
            raise HTTPException(
                status_code=400, detail="Hệ thống Cloud bị lỗi."
            )
        return creds

    def create(self, file: UploadFile) -> GoogleDriveAPIRes:
        try:
            # Creating file metadata
            file_metadata = {"name": file.filename,
                             "parents": [settings.FOLDER_GCLOUD_ID]}

            # Creating media upload object
            media = MediaIoBaseUpload(io.BytesIO(
                file.file.read()), mimetype=file.content_type, resumable=True)

            # Uploading the file
            res = (self.service.files()
                   .create(body=file_metadata, media_body=media,
                           fields="id,mimeType,name,thumbnailLink,webViewLink")
                   .execute())
            return GoogleDriveAPIRes.model_validate(res)

        except HttpError as error:
            if "File not found" in str(error):
                logger.error(
                    f"Parent folder with ID {settings.FOLDER_GCLOUD_ID} not found.")
            else:
                logger.error(
                    f"An error occurred when uploading the file: {error}")
            raise HTTPException(
                status_code=400, detail="Hệ thống Cloud bị lỗi."
            )

    def delete(self, file_id: str):
        try:
            # Uploading the file
            self.service.files().delete(fileId=file_id).execute()

        except HttpError as error:
            if "File not found" in str(error):
                logger.error(
                    f"Parent folder with ID {settings.FOLDER_GCLOUD_ID} not found.")
                raise HTTPException(
                    status_code=400, detail="Không tìm thấy file."
                )
            else:
                logger.error(
                    f"An error occurred when deleting the file: {error}")
                raise HTTPException(
                    status_code=400, detail="Hệ thống Cloud bị lỗi."
                )
