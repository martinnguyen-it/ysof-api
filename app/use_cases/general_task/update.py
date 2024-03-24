from typing import Optional
from fastapi import Depends
from app.models.general_task import GeneralTaskModel
from app.shared import request_object, use_case, response_object

from app.domain.general_task.entity import (AdminInGeneralTask, GeneralTask, GeneralTaskInDB, GeneralTaskInUpdate,
                                            GeneralTaskInUpdateTime)
from app.infra.general_task.general_task_repository import GeneralTaskRepository
from app.domain.shared.enum import AdminRole
from app.shared.constant import SUPER_ADMIN
from app.domain.admin.entity import AdminInDB
from app.infra.document.document_repository import DocumentRepository
from app.domain.document.entity import AdminInDocument, Document, DocumentInDB


class UpdateGeneralTaskRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str,
                 admin_roles: list[AdminRole],
                 obj_in: GeneralTaskInUpdate) -> None:
        self.id = id
        self.obj_in = obj_in
        self.admin_roles = admin_roles

    @classmethod
    def builder(cls, id: str,
                admin_roles: list[AdminRole],
                payload: Optional[GeneralTaskInUpdate] = None
                ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateGeneralTaskRequestObject(id=id, obj_in=payload, admin_roles=admin_roles)


class UpdateGeneralTaskUseCase(use_case.UseCase):
    def __init__(self,
                 document_repository: DocumentRepository = Depends(
                     DocumentRepository),
                 general_task_repository: GeneralTaskRepository = Depends(GeneralTaskRepository)):
        self.general_task_repository = general_task_repository
        self.document_repository = document_repository

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
        if general_task.role not in req_object.admin_roles and \
                not any(role in SUPER_ADMIN for role in req_object.admin_roles):
            return response_object.ResponseFailure.build_not_found_error("Bạn không có quyền sửa")

        self.general_task_repository.update(id=general_task.id, data=GeneralTaskInUpdateTime(
            **req_object.obj_in.model_dump()))

        general_task.reload()

        author: AdminInDB = AdminInDB.model_validate(general_task.author)
        return GeneralTask(
            **GeneralTaskInDB.model_validate(general_task).model_dump(exclude=({"author", "attachments"})),
            author=AdminInGeneralTask(**author.model_dump()), active=not author.disabled(),
            attachments=[Document(**DocumentInDB.model_validate(doc).model_dump(exclude=({"author"})),
                                  author=AdminInDocument(
                                      **AdminInDB.model_validate(doc.author).model_dump()),
                                  active=not author.disabled())
                         for doc in general_task.attachments]
        )
