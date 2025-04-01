import math
from typing import Optional, List, Any
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.celery_result.entity import (
    ManyCeleryResultsInResponse,
    CeleryResultResponse,
)
from app.domain.shared.entity import Pagination
from app.models.celery_result import CeleryResultModel
from app.infra.celery_result.celery_result_repository import CeleryResultRepository
from app.domain.celery_result.enum import CeleryResultTag


class ListCeleryResultsRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        page_index: int,
        page_size: int,
        name: Optional[list[str]] = None,
        sort: Optional[dict[str, int]] = None,
        tag: Optional[CeleryResultTag] = None,
    ):
        self.page_index = page_index
        self.page_size = page_size
        self.sort = sort
        self.name = name
        self.tag = tag

    @classmethod
    def builder(
        cls,
        page_index: int,
        page_size: int,
        name: Optional[list[str]] = None,
        sort: Optional[dict[str, int]] = None,
        tag: Optional[CeleryResultTag] = None,
    ):
        return ListCeleryResultsRequestObject(
            page_index=page_index,
            page_size=page_size,
            sort=sort,
            tag=tag,
            name=name,
        )


class ListCeleryResultsUseCase(use_case.UseCase):
    def __init__(
        self,
        celery_result_repository: CeleryResultRepository = Depends(CeleryResultRepository),
    ):
        self.celery_result_repository = celery_result_repository

    def process_request(self, req_object: ListCeleryResultsRequestObject):
        match_pipeline: dict[str, Any] = {}

        if isinstance(req_object.tag, CeleryResultTag):
            match_pipeline = {**match_pipeline, "result.tag": req_object.tag}

        if isinstance(req_object.name, str):
            match_pipeline = {**match_pipeline, "result.name": {"$regex": req_object.name}}

        celery_results: List[CeleryResultModel] = self.celery_result_repository.list(
            page_size=req_object.page_size,
            page_index=req_object.page_index,
            sort=req_object.sort,
            match_pipeline=match_pipeline if bool(match_pipeline) else None,
        )

        total = self.celery_result_repository.count_list(
            match_pipeline=match_pipeline if bool(match_pipeline) else None
        )

        return ManyCeleryResultsInResponse(
            pagination=Pagination(
                total=total,
                page_index=req_object.page_index,
                total_pages=math.ceil(total / req_object.page_size),
            ),
            data=[
                CeleryResultResponse(
                    task_id=model.task_id,
                    tag=model.result.tag,
                    name=model.result.name,
                    description=model.result.description,
                    date_done=model.date_done,
                    traceback=model.result.traceback,
                )
                for model in celery_results
            ],
        )
