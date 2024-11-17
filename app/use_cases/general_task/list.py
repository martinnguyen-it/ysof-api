import math
from typing import Optional, List, Any
from fastapi import Depends
from app.shared import request_object, use_case, response_object
from app.domain.general_task.entity import (
    AdminInGeneralTask,
    GeneralTask,
    GeneralTaskInDB,
    ManyGeneralTasksInResponse,
)
from app.domain.shared.entity import Pagination
from app.models.general_task import GeneralTaskModel
from app.infra.general_task.general_task_repository import GeneralTaskRepository
from app.models.admin import AdminModel
from app.domain.general_task.enum import GeneralTaskType
from app.domain.admin.entity import AdminInDB
from app.shared.constant import SUPER_ADMIN
from app.domain.document.entity import AdminInDocument, Document, DocumentInDB
from app.domain.shared.enum import AdminRole
from app.shared.utils.general import get_current_season_value


class ListGeneralTasksRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        current_admin: AdminModel,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        label: Optional[list[str]] = None,
        sort: Optional[dict[str, int]] = None,
        season: int | None = None,
        type: Optional[GeneralTaskType] = None,
        roles: Optional[list[str]] = None,
    ):
        self.page_index = page_index
        self.page_size = page_size
        self.search = search
        self.sort = sort
        self.label = label
        self.current_admin = current_admin
        self.roles = roles
        self.season = season
        self.type = type

    @classmethod
    def builder(
        cls,
        current_admin: AdminModel,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        label: Optional[list[str]] = None,
        sort: Optional[dict[str, int]] = None,
        season: int | None = None,
        type: Optional[GeneralTaskType] = None,
        roles: Optional[list[str]] = None,
    ):
        return ListGeneralTasksRequestObject(
            current_admin=current_admin,
            page_index=page_index,
            label=label,
            page_size=page_size,
            search=search,
            sort=sort,
            season=season,
            type=type,
            roles=roles,
        )


class ListGeneralTasksUseCase(use_case.UseCase):
    def __init__(
        self,
        general_task_repository: GeneralTaskRepository = Depends(GeneralTaskRepository),
    ):
        self.general_task_repository = general_task_repository

    def match_pipeline_helper(
        self,
        req_object: ListGeneralTasksRequestObject,
    ):
        current_season = get_current_season_value()

        match_pipeline: dict[str, Any] | None = {}
        is_super_admin = AdminInDB.model_validate(req_object.current_admin).active() and any(
            role in SUPER_ADMIN for role in req_object.current_admin.roles
        )
        # if season in query is None, then get season_default
        season_default = (
            req_object.current_admin.latest_season
            if AdminRole.ADMIN not in req_object.current_admin.roles
            else current_season
        )

        if not is_super_admin and req_object.season == 0:
            return response_object.ResponseFailure.build_parameters_error(
                "Bạn không có quyền truy cập tất cả mùa"
            )

        if isinstance(req_object.type, str):
            match_pipeline = {**match_pipeline, "type": req_object.type}

        if is_super_admin and req_object.season == 0:
            return match_pipeline

        if (
            is_super_admin
            or (
                isinstance(req_object.season, int)
                and req_object.season <= req_object.current_admin.latest_season
            )
            or req_object.season is None
        ):
            match_pipeline = {
                **match_pipeline,
                "$or": [
                    {
                        "$and": [
                            {"type": GeneralTaskType.ANNUAL},
                            {
                                "season": {
                                    "$lte": (
                                        req_object.season
                                        if req_object.season
                                        and (
                                            req_object.season
                                            <= req_object.current_admin.latest_season
                                            or is_super_admin
                                        )
                                        else season_default
                                    )
                                }
                            },
                        ]
                    },
                    {
                        "$and": [
                            {
                                "$or": [
                                    {"type": GeneralTaskType.COMMON},
                                    (
                                        {"type": GeneralTaskType.INTERNAL}
                                        if is_super_admin
                                        else {
                                            "$and": [
                                                {"type": GeneralTaskType.INTERNAL},
                                                {"role": {"$in": req_object.current_admin.roles}},
                                            ]
                                        }
                                    ),
                                ]
                            },
                            {
                                "season": (
                                    req_object.season if req_object.season else season_default
                                )
                            },
                        ]
                    },
                ],
            }
            return match_pipeline

        return response_object.ResponseFailure.build_parameters_error(
            "Bạn không có quyền truy cập " + (f"mùa {req_object.season}")
        )

    def process_request(self, req_object: ListGeneralTasksRequestObject):
        match_pipeline = self.match_pipeline_helper(
            req_object=req_object,
        )
        if isinstance(match_pipeline, response_object.ResponseFailure):
            return match_pipeline

        if isinstance(req_object.search, str):
            match_pipeline = {
                **match_pipeline,
                "title": {"$regex": req_object.search, "$options": "i"},
            }
        if isinstance(req_object.label, list) and len(req_object.label) > 0:
            match_pipeline = {**match_pipeline, "label": {"$in": req_object.label}}
        if isinstance(req_object.roles, list) and len(req_object.roles) > 0:
            match_pipeline = {**match_pipeline, "role": {"$in": req_object.roles}}

        print(match_pipeline)

        general_tasks: List[GeneralTaskModel] = self.general_task_repository.list(
            page_size=req_object.page_size,
            page_index=req_object.page_index,
            sort=req_object.sort,
            match_pipeline=match_pipeline,
        )

        total = self.general_task_repository.count_list(match_pipeline=match_pipeline)

        data: Optional[list[GeneralTask]] = []
        for task in general_tasks:
            author: AdminInDB = AdminInDB.model_validate(task.author)
            data.append(
                GeneralTask(
                    **GeneralTaskInDB.model_validate(task).model_dump(
                        exclude=({"author", "attachments"})
                    ),
                    author=AdminInGeneralTask(**author.model_dump(), active=author.active()),
                    attachments=[
                        Document(
                            **DocumentInDB.model_validate(doc).model_dump(exclude=({"author"})),
                            author=AdminInDocument(
                                **AdminInDB.model_validate(doc.author).model_dump(),
                                active=author.active(),
                            ),
                        )
                        for doc in task.attachments
                    ],
                )
            )

        return ManyGeneralTasksInResponse(
            pagination=Pagination(
                total=total,
                page_index=req_object.page_index,
                total_pages=math.ceil(total / req_object.page_size),
            ),
            data=data,
        )
