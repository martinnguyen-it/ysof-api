from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Annotated, Optional

from app.domain.audit_log.entity import (
    AuditLog,
    ManyAuditLogsInResponse,
)
from app.domain.shared.enum import AdminRole, Sort
from app.infra.security.security_service import authorization, get_current_admin
from app.shared.decorator import response_decorator
from app.use_cases.audit_log.list import ListAuditLogsUseCase, ListAuditLogsRequestObject

from app.models.admin import AdminModel
from app.domain.audit_log.enum import AuditLogType, Endpoint

router = APIRouter()


@router.get(
    "",
    response_model=ManyAuditLogsInResponse,
)
@response_decorator()
def get_list_audit_logs(
    list_audit_logs_use_case: ListAuditLogsUseCase = Depends(ListAuditLogsUseCase),
    page_index: Annotated[int, Query(title="Page Index")] = 1,
    page_size: Annotated[int, Query(title="Page size")] = 100,
    search: Optional[str] = Query(None, title="Search"),
    sort: Optional[Sort] = Sort.DESC,
    sort_by: Optional[str] = "created_at",
    type: Optional[AuditLogType] = None,
    endpoint: Optional[Endpoint] = None,
    current_admin: AdminModel = Depends(get_current_admin),
):
    authorization(current_admin, [AdminRole.ADMIN])
    annotations = {}
    for base in reversed(AuditLog.__mro__):
        annotations.update(getattr(base, "__annotations__", {}))
    if sort_by not in annotations:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by: {sort_by}")
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListAuditLogsRequestObject.builder(
        page_index=page_index,
        page_size=page_size,
        search=search,
        endpoint=endpoint,
        type=type,
        sort=sort_query,
    )
    response = list_audit_logs_use_case.execute(request_object=req_object)
    return response
