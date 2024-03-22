from typing import Optional
from fastapi import Depends

from app.config import settings
from app.domain.admin.entity import AdminInDB
from app.models.general_task import GeneralTaskModel
from app.shared import request_object, use_case, response_object

from app.domain.general_task.entity import GeneralTask, GeneralTaskInCreate, GeneralTaskInDB, AdminInGeneralTask
from app.infra.general_task.general_task_repository import GeneralTaskRepository
from app.models.admin import AdminModel
from app.domain.document.entity import AdminInDocument, Document, DocumentInDB
from app.infra.document.document_repository import DocumentRepository


class CreateGeneralTaskRequestObject(request_object.ValidRequestObject):
    def __init__(self, author: AdminModel,
                 general_task_in: GeneralTaskInCreate) -> None:
        self.general_task_in = general_task_in
        self.author = author

    @classmethod
    def builder(cls, author: Optional[AdminModel] = None,
                payload: Optional[GeneralTaskInCreate] = None
                ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return CreateGeneralTaskRequestObject(general_task_in=payload, author=author)


class CreateGeneralTaskUseCase(use_case.UseCase):
    def __init__(self,
                 document_repository: DocumentRepository = Depends(
                     DocumentRepository),
                 general_task_repository: GeneralTaskRepository = Depends(GeneralTaskRepository)):
        self.general_task_repository = general_task_repository
        self.document_repository = document_repository

    def process_request(self, req_object: CreateGeneralTaskRequestObject):
        if isinstance(req_object.general_task_in.attachments, list):
            for doc_id in req_object.general_task_in.attachments:
                doc = self.document_repository.get_by_id(doc_id)
                if doc is None:
                    return response_object.ResponseFailure.build_not_found_error(
                        message="Tài liệu đính kèm không tồn tại"
                    )

        obj_in: GeneralTaskInDB = GeneralTaskInDB(
            **req_object.general_task_in.model_dump(exclude={"attachments"}),
            session=settings.CURRENT_SEASON,
            author=req_object.author
        )
        general_task: GeneralTaskModel = self.general_task_repository.create(
            general_task=obj_in, attachments=req_object.general_task_in.attachments)
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
