from typing import Optional

from fastapi import Depends, BackgroundTasks
from app.infra.document.document_repository import DocumentRepository
from app.shared import request_object, response_object, use_case
from app.domain.shared.enum import AdminRole
from app.shared.constant import SUPER_ADMIN
from app.models.document import DocumentModel
from app.infra.services.google_drive_api import GoogleDriveApiService
from app.infra.general_task.general_task_repository import GeneralTaskRepository


class DeleteDocumentRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str,
                 admin_roles: list[AdminRole]):
        self.id = id
        self.admin_roles = admin_roles

    @classmethod
    def builder(cls, id: str,
                admin_roles: list[AdminRole]
                ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if invalid_req.has_errors():
            return invalid_req

        return DeleteDocumentRequestObject(id=id, admin_roles=admin_roles)


class DeleteDocumentUseCase(use_case.UseCase):
    def __init__(self,
                 background_tasks: BackgroundTasks,
                 google_drive_api_service: GoogleDriveApiService = Depends(
                     GoogleDriveApiService),
                 document_repository: DocumentRepository = Depends(
                     DocumentRepository),
                 general_task_repository: GeneralTaskRepository = Depends(GeneralTaskRepository)):
        self.google_drive_api_service = google_drive_api_service
        self.document_repository = document_repository
        self.background_tasks = background_tasks
        self.general_task_repository = general_task_repository

    def process_request(self, req_object: DeleteDocumentRequestObject):
        document: Optional[DocumentModel] = self.document_repository.get_by_id(
            req_object.id)
        if not document:
            return response_object.ResponseFailure.build_not_found_error("Tài liệu không tồn tại")

        if document.role not in req_object.admin_roles and \
                not any(role in SUPER_ADMIN for role in req_object.admin_roles):
            return response_object.ResponseFailure.build_auth_error("Bạn không có quyền sửa")

        general_task = self.general_task_repository.find_one(
            conditions={"attachments": {
                "$in": [document.id]}}
        )

        if general_task is not None:
            return response_object.ResponseFailure.build_parameters_error(
                "Không thể xóa tài liệu có công việc đang đính kèm."
            )

        self.background_tasks.add_task(
            self.google_drive_api_service.delete, document.file_id)
        try:
            self.document_repository.delete(id=document.id)
            return {"success": True}
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went error.")
