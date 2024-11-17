import json
from typing import Optional

from fastapi import Depends, BackgroundTasks
from app.infra.document.document_repository import DocumentRepository
from app.shared import request_object, response_object, use_case
from app.shared.constant import SUPER_ADMIN
from app.models.document import DocumentModel
from app.infra.services.google_drive_api import GoogleDriveAPIService
from app.infra.general_task.general_task_repository import GeneralTaskRepository
from app.models.admin import AdminModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.domain.document.entity import DocumentInDB
from app.shared.utils.general import get_current_season_value
from app.infra.subject.subject_repository import SubjectRepository


class DeleteDocumentRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str, current_admin: AdminModel):
        self.id = id
        self.current_admin = current_admin

    @classmethod
    def builder(cls, id: str, current_admin: AdminModel) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if invalid_req.has_errors():
            return invalid_req

        return DeleteDocumentRequestObject(id=id, current_admin=current_admin)


class DeleteDocumentUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        google_drive_api_service: GoogleDriveAPIService = Depends(GoogleDriveAPIService),
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        document_repository: DocumentRepository = Depends(DocumentRepository),
        general_task_repository: GeneralTaskRepository = Depends(GeneralTaskRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.google_drive_api_service = google_drive_api_service
        self.document_repository = document_repository
        self.background_tasks = background_tasks
        self.general_task_repository = general_task_repository
        self.audit_log_repository = audit_log_repository
        self.subject_repository = subject_repository

    def process_request(self, req_object: DeleteDocumentRequestObject):
        document: Optional[DocumentModel] = self.document_repository.get_by_id(req_object.id)
        if not document:
            return response_object.ResponseFailure.build_not_found_error("Tài liệu không tồn tại")

        if document.role not in req_object.current_admin.roles and not any(
            role in SUPER_ADMIN for role in req_object.current_admin.roles
        ):
            return response_object.ResponseFailure.build_auth_error("Bạn không có quyền sửa")

        general_task = self.general_task_repository.find_one(
            conditions={"attachments": {"$in": [document.id]}}
        )
        subject = self.subject_repository.find_one(
            conditions={"attachments": {"$in": [document.id]}}
        )

        if general_task is not None:
            return response_object.ResponseFailure.build_parameters_error(
                "Không thể xóa tài liệu có công việc đang đính kèm."
            )
        if subject is not None:
            return response_object.ResponseFailure.build_parameters_error(
                "Không thể xóa tài liệu có môn học đang đính kèm."
            )

        try:
            self.document_repository.delete(id=document.id)
            self.background_tasks.add_task(self.google_drive_api_service.delete, document.file_id)

            current_season = get_current_season_value()
            self.background_tasks.add_task(
                self.audit_log_repository.create,
                AuditLogInDB(
                    type=AuditLogType.DELETE,
                    endpoint=Endpoint.DOCUMENT,
                    season=current_season,
                    author=req_object.current_admin,
                    author_email=req_object.current_admin.email,
                    author_name=req_object.current_admin.full_name,
                    author_roles=req_object.current_admin.roles,
                    description=json.dumps(
                        DocumentInDB.model_validate(document).model_dump(exclude_none=True),
                        default=str,
                        ensure_ascii=False,
                    ),
                ),
            )
            return {"success": True}
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went error.")
