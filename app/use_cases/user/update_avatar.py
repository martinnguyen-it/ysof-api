from fastapi import Depends, UploadFile

from app.config import settings
from app.domain.admin.entity import AdminInUpdateTime
from app.domain.student.entity import StudentUpdateMeTime
from app.domain.upload.entity import GoogleDriveAPIRes
from app.infra.admin.admin_repository import AdminRepository
from app.infra.services.google_drive_api import GoogleDriveAPIService
from app.infra.student.student_repository import StudentRepository
from app.infra.tasks.drive_file import delete_file_drive_task
from app.models.admin import AdminModel
from app.models.student import StudentModel
from app.shared import request_object, response_object, use_case
import io
from PIL import Image


class UpdateAvatarRequestObject(request_object.ValidRequestObject):
    def __init__(self, user: AdminModel | StudentModel, image: UploadFile) -> None:
        self.image = image
        self.user = user

    @classmethod
    def builder(
        cls, user: AdminModel | StudentModel, image: UploadFile
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if image.size > 200 * 1024:  # 200 KB
            invalid_req.add_error("image", "Ảnh phải nhỏ hơn 200KB")

        contents = image.file.read()
        image.file.seek(0)  # Reset file pointer to the beginning
        try:
            img = Image.open(io.BytesIO(contents))
            width, height = img.size

            if width != height:
                invalid_req.add_error("image", "Ảnh đại diện phải là hình vuông.")
        except Exception:
            invalid_req.add_error("image", "Không đúng định dạng ảnh.")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateAvatarRequestObject(image=image, user=user)


class UpdateAvatarUseCase(use_case.UseCase):
    def __init__(
        self,
        admin_repository: AdminRepository = Depends(AdminRepository),
        student_repository: StudentRepository = Depends(StudentRepository),
        google_drive_service: GoogleDriveAPIService = Depends(GoogleDriveAPIService),
    ):
        self.admin_repository = admin_repository
        self.student_repository = student_repository
        self.google_drive_service = google_drive_service

    def process_request(self, req_object: UpdateAvatarRequestObject):
        res: GoogleDriveAPIRes = self.google_drive_service.create(
            req_object.image, folder_id=settings.FOLDER_GCLOUD_AVATAR_ID
        )

        old_avatar = req_object.user.avatar

        if isinstance(req_object.user, AdminModel):
            is_updated = self.admin_repository.update(
                id=req_object.user.id,
                data=AdminInUpdateTime(avatar=f"{settings.PREFIX_IMAGE_GCLOUD}{res.id}"),
            )
        else:
            is_updated = self.student_repository.update(
                id=req_object.user.id,
                data=StudentUpdateMeTime(
                    avatar=f"{settings.PREFIX_IMAGE_GCLOUD}{res.id}"
                ).model_dump(exclude_none=True),
            )

        if is_updated:
            if old_avatar:
                delete_file_drive_task.delay(old_avatar.replace(settings.PREFIX_IMAGE_GCLOUD, ""))
            return {"success": True}
        return response_object.ResponseFailure.build_system_error(
            message="Something went wrong, please try again."
        )
