from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.params import Path

from app.domain.upload.entity import GoogleDriveAPIRes, ImageRes
from app.infra.services.google_drive_api import GoogleDriveApiService
from app.shared.decorator import response_decorator
from app.use_cases.upload.create_image import UploadImageRequestObject, UploadImageUseCase

router = APIRouter()


@router.post(
    "",
    response_model=GoogleDriveAPIRes
)
@response_decorator()
def upload_file(
        file: UploadFile = File(...),
        google_drive_service: GoogleDriveApiService = Depends(GoogleDriveApiService)
):
    response = google_drive_service.create(file=file)
    return response


@router.post(
    "/image",
    response_model=ImageRes
)
@response_decorator()
def upload_image(
        image: UploadFile = File(...),
        upload_image_use_case: UploadImageUseCase = Depends(
            UploadImageUseCase),
):
    req_object = UploadImageRequestObject.builder(image=image)
    response = upload_image_use_case.execute(request_object=req_object)
    return response


@router.delete(
    "/{file_id}",
)
@response_decorator()
def upload_image(
        file_id: str = Path(..., title="File id"),
        google_drive_service: GoogleDriveApiService = Depends(GoogleDriveApiService)
):
    google_drive_service.delete(file_id=file_id)
    return {"message": "Success"}
