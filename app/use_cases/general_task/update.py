import json
from typing import Optional
from fastapi import Depends, BackgroundTasks
from app.models.general_task import GeneralTaskModel
from app.shared import request_object, use_case, response_object

from app.domain.general_task.entity import (AdminInGeneralTask, GeneralTask, GeneralTaskInDB, GeneralTaskInUpdate,
                                            GeneralTaskInUpdateTime)
from app.infra.general_task.general_task_repository import GeneralTaskRepository
from app.shared.constant import SUPER_ADMIN
from app.domain.admin.entity import AdminInDB
from app.infra.document.document_repository import DocumentRepository
from app.domain.document.entity import AdminInDocument, Document, DocumentInDB
from app.models.admin import AdminModel
from app.infra.season.season_repository import SeasonRepository
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.domain.audit_log.entity import AuditLogInDB


class UpdateGeneralTaskRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str,
                 current_admin: AdminModel,
                 obj_in: GeneralTaskInUpdate) -> None:
        self.id = id
        self.obj_in = obj_in
        self.current_admin = current_admin

    @classmethod
    def builder(cls, id: str,
                current_admin: AdminModel,
                payload: Optional[GeneralTaskInUpdate] = None
                ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateGeneralTaskRequestObject(id=id, obj_in=payload, current_admin=current_admin)


class UpdateGeneralTaskUseCase(use_case.UseCase):
    def __init__(self,
                 background_tasks: BackgroundTasks,
                 document_repository: DocumentRepository = Depends(
                     DocumentRepository),
                 general_task_repository: GeneralTaskRepository = Depends(
                     GeneralTaskRepository),
                 season_repository: SeasonRepository = Depends(
                     SeasonRepository),
                 audit_log_repository: AuditLogRepository = Depends(AuditLogRepository)):
        self.general_task_repository = general_task_repository
        self.document_repository = document_repository
        self.background_tasks = background_tasks
        self.season_repository = season_repository
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: UpdateGeneralTaskRequestObject):
        if isinstance(req_object.obj_in.attachments, list):
            for doc_id in req_object.obj_in.attachments:
                doc = self.document_repository.get_by_id(doc_id)
                if doc is None:
                    return response_object.ResponseFailure.build_not_found_error(
                        message="Tài liệu đính kèm không tồn tại"
                    )

        general_task: Optional[GeneralTaskModel] = self.general_task_repository.get_by_id(
            req_object.id)
        if not general_task:
            return response_object.ResponseFailure.build_not_found_error("Công việc không tồn tại")
        if general_task.role not in req_object.current_admin.roles and \
                not any(role in SUPER_ADMIN for role in req_object.current_admin.roles):
            return response_object.ResponseFailure.build_not_found_error("Bạn không có quyền sửa")

        self.general_task_repository.update(id=general_task.id, data=GeneralTaskInUpdateTime(
            **req_object.obj_in.model_dump()))
        general_task.reload()

        self.background_tasks.add_task(self.audit_log_repository.create, AuditLogInDB(
            type=AuditLogType.UPDATE,
            endpoint=Endpoint.GENERAL_TASK,
            season=self.season_repository.get_current_season().season,
            author=req_object.current_admin,
            author_email=req_object.current_admin.email,
            author_name=req_object.current_admin.full_name,
            author_roles=req_object.current_admin.roles,
            description=json.dumps(
                req_object.obj_in.model_dump(exclude_none=True), default=str
            )
        ))

        author: AdminInDB = AdminInDB.model_validate(general_task.author)
        return GeneralTask(
            **GeneralTaskInDB.model_validate(general_task).model_dump(exclude=({"author", "attachments"})),
            author=AdminInGeneralTask(
                **author.model_dump(), active=author.active()),
            attachments=[Document(**DocumentInDB.model_validate(doc).model_dump(exclude=({"author"})),
                                  author=AdminInDocument(
                                      **AdminInDB.model_validate(doc.author).model_dump(),
                                  active=author.active()))
                         for doc in general_task.attachments]
        )
