from app.config import settings
import math
from typing import Optional, List
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.general_task.entity import (AdminInGeneralTask, GeneralTask, GeneralTaskInDB,
                                            ManyGeneralTasksInResponse)
from app.domain.shared.entity import Pagination
from app.models.general_task import GeneralTaskModel
from app.infra.general_task.general_task_repository import GeneralTaskRepository
from app.models.admin import AdminModel
from app.domain.general_task.enum import GeneralTaskType
from app.domain.admin.entity import AdminInDB
from app.shared.constant import SUPER_ADMIN
from app.domain.document.entity import AdminInDocument, Document, DocumentInDB


class ListGeneralTasksRequestObject(request_object.ValidRequestObject):
    def __init__(self, author: AdminModel, page_index: int, page_size: int, search: Optional[str] = None,
                 label: Optional[list[str]] = None, sort: Optional[dict[str, int]] = None,
                 roles: Optional[list[str]] = None
                 ):
        self.page_index = page_index
        self.page_size = page_size
        self.search = search
        self.sort = sort
        self.label = label
        self.author = author
        self.roles = roles

    @classmethod
    def builder(cls, author: AdminModel, page_index: int, page_size: int, search: Optional[str] = None,
                label: Optional[list[str]] = None, sort: Optional[dict[str, int]] = None,
                roles: Optional[list[str]] = None
                ):
        return ListGeneralTasksRequestObject(author=author, page_index=page_index, label=label,
                                             page_size=page_size, search=search, sort=sort, roles=roles)


class ListGeneralTasksUseCase(use_case.UseCase):
    def __init__(self, general_task_repository: GeneralTaskRepository = Depends(GeneralTaskRepository)):
        self.general_task_repository = general_task_repository

    def process_request(self, req_object: ListGeneralTasksRequestObject):
        is_super_admin = False
        for role in req_object.author.roles:
            if role in SUPER_ADMIN:
                is_super_admin = True
                break

        match_pipeline = [
            {
                "$match": {
                    "$or": [
                        {"type": GeneralTaskType.ANNUAL},
                        {
                            "$and": [
                                {
                                    "$or": [
                                        {"type": GeneralTaskType.COMMON},
                                        {"type": GeneralTaskType.INTERNAL}
                                        if is_super_admin else
                                        {"$and": [
                                            {"type": GeneralTaskType.INTERNAL},
                                            {"role": {"$in": req_object.author.roles}}
                                        ]},
                                    ]
                                },
                                {"season": settings.CURRENT_SEASON}
                            ]
                        }
                    ]
                }
            }
        ]

        if isinstance(req_object.search, str):
            match_pipeline.append({
                "$match": {
                    "title": {"$regex": req_object.search, "$options": "i"},
                    "short_desc": {"$regex": req_object.search, "$options": "i"}
                }
            })

        if isinstance(req_object.label, list) and len(req_object.label) > 0:
            match_pipeline.append({
                "$match": {
                    "label": {"$in": req_object.label}
                }
            })

        if isinstance(req_object.roles, list) and len(req_object.roles) > 0:
            match_pipeline.append({
                "$match": {
                    "role": {"$in": req_object.roles}
                }
            })

        general_tasks: List[GeneralTaskModel] = self.general_task_repository.list(
            page_size=req_object.page_size,
            page_index=req_object.page_index,
            sort=req_object.sort,
            match_pipeline=match_pipeline
        )

        total = self.general_task_repository.count_list(
            match_pipeline=match_pipeline
        )

        data: Optional[list[GeneralTask]] = []
        for task in general_tasks:
            author: AdminInDB = AdminInDB.model_validate(
                task.author)
            data.append(GeneralTask(
                **GeneralTaskInDB.model_validate(task).model_dump(exclude=({"author", "attachments"})),
                author=AdminInGeneralTask(**author.model_dump()), active=not author.disabled(),
                attachments=[Document(**DocumentInDB.model_validate(doc).model_dump(exclude=({"author"})),
                                      author=AdminInDocument(
                                      **AdminInDB.model_validate(doc.author).model_dump()),
                                      active=not author.disabled())
                             for doc in task.attachments]
            ))

        return ManyGeneralTasksInResponse(
            pagination=Pagination(
                total=total, page_index=req_object.page_index, total_pages=math.ceil(
                    total / req_object.page_size)
            ),
            data=data,
        )
