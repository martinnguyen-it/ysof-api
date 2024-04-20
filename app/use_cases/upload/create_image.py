from fastapi import Depends, UploadFile

from app.config import settings
from app.domain.upload.entity import GoogleDriveAPIRes, ImageRes
from app.infra.services.google_drive_api import GoogleDriveAPIService
from app.shared import request_object, use_case


class UploadImageRequestObject(request_object.ValidRequestObject):
    def __init__(self, image: UploadFile) -> None:
        self.image = image

    @classmethod
    def builder(cls, image: UploadFile) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()

        if image.content_type not in ["image/jpeg", "image/png"]:
            invalid_req.add_error("image", "Không đúng định dạng ảnh.")

        if invalid_req.has_errors():
            return invalid_req

        return UploadImageRequestObject(image=image)


class UploadImageUseCase(use_case.UseCase):
    def __init__(self, google_drive_service: GoogleDriveAPIService = Depends(GoogleDriveAPIService)):
        self.google_drive_service = google_drive_service

    def process_request(self, req_object: UploadImageRequestObject):
        res: GoogleDriveAPIRes = self.google_drive_service.create(req_object.image)
        return ImageRes(url=f"{settings.PREFIX_IMAGE_GCLOUD}{res.id}")
