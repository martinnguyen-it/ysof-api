from fastapi import Depends
from typing import Optional
from app.shared import request_object, response_object, use_case
from app.domain.general_task.entity import AdminInGeneralTask, GeneralTask, GeneralTaskInDB
from app.infra.general_task.general_task_repository import GeneralTaskRepository
from app.models.general_task import GeneralTaskModel
from app.domain.admin.entity import AdminInDB
from app.domain.document.entity import AdminInDocument, Document, DocumentInDB


class GetGeneralTaskRequestObject(request_object.ValidRequestObject):
    def __init__(self, general_task_id: str):
        self.general_task_id = general_task_id

    @classmethod
    def builder(cls, general_task_id: str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not id:
            invalid_req.add_error("id", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return GetGeneralTaskRequestObject(general_task_id=general_task_id)


class GetGeneralTaskCase(use_case.UseCase):
    def __init__(
        self, general_task_repository: GeneralTaskRepository = Depends(GeneralTaskRepository)
    ):
        self.general_task_repository = general_task_repository

    def process_request(self, req_object: GetGeneralTaskRequestObject):
        general_task: Optional[GeneralTaskModel] = self.general_task_repository.get_by_id(
            general_task_id=req_object.general_task_id
        )
        if not general_task:
            return response_object.ResponseFailure.build_not_found_error(
                message="Công việc không tồn tại"
            )

        author: AdminInDB = AdminInDB.model_validate(general_task.author)
        return GeneralTask(
            **GeneralTaskInDB.model_validate(general_task).model_dump(
                exclude=({"author", "attachments"})
            ),
            author=AdminInGeneralTask(**author.model_dump(), active=author.active()),
            attachments=[
                Document(
                    **DocumentInDB.model_validate(doc).model_dump(exclude=({"author"})),
                    author=AdminInDocument(
                        **AdminInDB.model_validate(doc.author).model_dump(), active=author.active()
                    ),
                )
                for doc in general_task.attachments
            ],
        )
