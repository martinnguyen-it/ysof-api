from typing import Annotated, Optional

from fastapi import Body, Depends, APIRouter
from fastapi.params import Query

from app.domain.celery_result.entity import (
    ManyCeleryResultsInResponse,
    TaskIdsRequest,
)
from app.domain.celery_result.enum import CeleryResultTag
from app.domain.shared.enum import AdminRole, Sort
from app.infra.security.security_service import get_current_active_admin, authorization
from app.shared.decorator import response_decorator
from app.use_cases.celery_result.list import (
    ListCeleryResultsUseCase,
    ListCeleryResultsRequestObject,
)
from app.use_cases.celery_result.mark_resolved_failed import (
    MarkResolvedFailedRequestObject,
    MarkResolvedFailedUseCase,
)

router = APIRouter()


@router.get(
    "/failed",
    response_model=ManyCeleryResultsInResponse,
)
@response_decorator()
def get_list_celery_results_fail(
    list_celery_results_use_case: ListCeleryResultsUseCase = Depends(ListCeleryResultsUseCase),
    page_index: Annotated[int, Query(title="Page Index")] = 1,
    page_size: Annotated[int, Query(title="Page size", le=300)] = 20,
    name: Optional[str] = Query(None, title="Name"),
    sort: Optional[Sort] = Sort.DESC,
    sort_by: Optional[str] = "date_done",
    tag: Optional[CeleryResultTag] = None,
    current_admin=Depends(get_current_active_admin),
    resolved: Optional[bool] = None,
):
    authorization(current_admin, [AdminRole.ADMIN])
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListCeleryResultsRequestObject.builder(
        page_index=page_index,
        page_size=page_size,
        name=name,
        tag=tag,
        sort=sort_query,
        resolved=resolved,
    )
    response = list_celery_results_use_case.execute(request_object=req_object)
    return response


@router.post(
    "/mark-resolved-failed",
)
@response_decorator()
def mark_resolved_failed_celery_results(
    request: TaskIdsRequest = Body(...),
    mark_resolved_failed_use_case: MarkResolvedFailedUseCase = Depends(MarkResolvedFailedUseCase),
    current_admin=Depends(get_current_active_admin),
):
    authorization(current_admin, [AdminRole.ADMIN])

    req_object = MarkResolvedFailedRequestObject.builder(
        task_ids=request.task_ids, current_admin=current_admin
    )
    response = mark_resolved_failed_use_case.execute(request_object=req_object)
    return response


@router.post(
    "/undo-mark-resolved",
)
@response_decorator()
def undo_mark_resolved_celery_results(
    request: TaskIdsRequest = Body(...),
    mark_resolved_failed_use_case: MarkResolvedFailedUseCase = Depends(MarkResolvedFailedUseCase),
    current_admin=Depends(get_current_active_admin),
):
    authorization(current_admin, [AdminRole.ADMIN])

    req_object = MarkResolvedFailedRequestObject.builder(
        task_ids=request.task_ids, current_admin=current_admin, is_undo=True
    )
    response = mark_resolved_failed_use_case.execute(request_object=req_object)
    return response
