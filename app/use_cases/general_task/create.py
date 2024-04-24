import json
from typing import Optional
from fastapi import Depends, BackgroundTasks

from app.domain.admin.entity import AdminInDB
from app.models.general_task import GeneralTaskModel
from app.shared import request_object, use_case, response_object

from app.domain.general_task.entity import GeneralTask, GeneralTaskInCreate, GeneralTaskInDB, AdminInGeneralTask
from app.infra.general_task.general_task_repository import GeneralTaskRepository
from app.models.admin import AdminModel
from app.domain.document.entity import AdminInDocument, Document, DocumentInDB
from app.infra.document.document_repository import DocumentRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.entity import AuditLogInDB
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.shared.utils.general import get_current_season_value


class CreateGeneralTaskRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_admin: AdminModel, general_task_in: GeneralTaskInCreate) -> None:
        self.general_task_in = general_task_in
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls, current_admin: AdminModel, payload: Optional[GeneralTaskInCreate] = None
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return CreateGeneralTaskRequestObject(general_task_in=payload, current_admin=current_admin)


class CreateGeneralTaskUseCase(use_case.UseCase):
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        document_repository: DocumentRepository = Depends(DocumentRepository),
        general_task_repository: GeneralTaskRepository = Depends(GeneralTaskRepository),
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.general_task_repository = general_task_repository
        self.document_repository = document_repository
        self.background_tasks = background_tasks
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: CreateGeneralTaskRequestObject):
        if isinstance(req_object.general_task_in.attachments, list):
            for doc_id in req_object.general_task_in.attachments:
                doc = self.document_repository.get_by_id(doc_id)
                if doc is None:
                    return response_object.ResponseFailure.build_not_found_error(
                        message="Tài liệu đính kèm không tồn tại"
                    )

        current_season = get_current_season_value()
        obj_in: GeneralTaskInDB = GeneralTaskInDB(
            **req_object.general_task_in.model_dump(exclude={"attachments"}),
            season=current_season,
            author=req_object.current_admin,
        )
        general_task: GeneralTaskModel = self.general_task_repository.create(
            general_task=obj_in, attachments=req_object.general_task_in.attachments
        )

        self.background_tasks.add_task(
            self.audit_log_repository.create,
            AuditLogInDB(
                type=AuditLogType.CREATE,
                endpoint=Endpoint.GENERAL_TASK,
                season=current_season,
                author=req_object.current_admin,
                author_email=req_object.current_admin.email,
                author_name=req_object.current_admin.full_name,
                author_roles=req_object.current_admin.roles,
                description=json.dumps(
                    req_object.general_task_in.model_dump(exclude_none=True), default=str, ensure_ascii=False
                ),
            ),
        )

        author: AdminInDB = AdminInDB.model_validate(general_task.author)
        return GeneralTask(
            **GeneralTaskInDB.model_validate(general_task).model_dump(exclude=({"author", "attachments"})),
            author=AdminInGeneralTask(**author.model_dump(), active=author.active()),
            attachments=[
                Document(
                    **DocumentInDB.model_validate(doc).model_dump(exclude=({"author"})),
                    author=AdminInDocument(**AdminInDB.model_validate(doc.author).model_dump(), active=author.active()),
                )
                for doc in general_task.attachments
            ],
        )
