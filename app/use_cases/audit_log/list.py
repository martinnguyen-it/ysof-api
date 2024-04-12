import math
from typing import Optional, List, Any
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.audit_log.entity import AuditLog, AuditLogInDB, ManyAuditLogsInResponse
from app.domain.shared.entity import Pagination
from app.models.audit_log import AuditLogModel
from app.infra.audit_log.audit_log_repository import AuditLogRepository
from app.domain.audit_log.enum import AuditLogType, Endpoint
from app.domain.admin.entity import Admin, AdminInDB


class ListAuditLogsRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
        type: Optional[AuditLogType] = None,
        endpoint: Optional[Endpoint] = None,
    ):
        self.page_index = page_index
        self.page_size = page_size
        self.search = search
        self.sort = sort
        self.endpoint = endpoint
        self.type = type

    @classmethod
    def builder(
        cls,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
        type: Optional[AuditLogType] = None,
        endpoint: Optional[Endpoint] = None,
    ):
        return ListAuditLogsRequestObject(
            page_index=page_index,
            page_size=page_size,
            search=search,
            sort=sort,
            type=type,
            endpoint=endpoint,
        )


class ListAuditLogsUseCase(use_case.UseCase):
    def __init__(
        self,
        audit_log_repository: AuditLogRepository = Depends(AuditLogRepository),
    ):
        self.audit_log_repository = audit_log_repository

    def process_request(self, req_object: ListAuditLogsRequestObject):
        match_pipeline: dict[str, Any] | None = {}

        if isinstance(req_object.search, str):
            match_pipeline = {
                **match_pipeline,
                "$or": [
                    {"author_name": {"$regex": req_object.search, "$options": "i"}},
                    {"author_email": {"$regex": req_object.search, "$options": "i"}},
                    {"description": {"$regex": req_object.search, "$options": "i"}},
                ],
            }
        if isinstance(req_object.type, AuditLogType):
            match_pipeline = {**match_pipeline, "type": req_object.type}
        if isinstance(req_object.endpoint, Endpoint):
            match_pipeline = {**match_pipeline, "endpoint": req_object.endpoint}

        audit_logs: List[AuditLogModel] = self.audit_log_repository.list(
            page_size=req_object.page_size,
            page_index=req_object.page_index,
            sort=req_object.sort,
            match_pipeline=match_pipeline,
        )

        total = self.audit_log_repository.count_list(match_pipeline=match_pipeline)

        data: Optional[list[AuditLog]] = []
        for log in audit_logs:
            author: AdminInDB | None = AdminInDB.model_validate(log.author) if log.author else None
            data.append(
                AuditLog(
                    **AuditLogInDB.model_validate(log).model_dump(exclude=({"author"})),
                    author=Admin(**author.model_dump(), active=author.active()),
                )
            )

        return ManyAuditLogsInResponse(
            pagination=Pagination(
                total=total, page_index=req_object.page_index, total_pages=math.ceil(total / req_object.page_size)
            ),
            data=data,
        )
