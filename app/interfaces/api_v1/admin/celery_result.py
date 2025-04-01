from typing import Annotated, Optional

from fastapi import Depends, APIRouter
from fastapi.params import Query

from app.domain.celery_result.entity import ManyCeleryResultsInResponse
from app.domain.celery_result.enum import CeleryResultTag
from app.domain.shared.enum import Sort
from app.infra.security.security_service import get_current_active_admin, authorization
from app.shared.constant import SUPER_ADMIN
from app.shared.decorator import response_decorator
from app.use_cases.celery_result.list import (
    ListCeleryResultsUseCase,
    ListCeleryResultsRequestObject,
)

router = APIRouter()


@router.get(
    "",
    response_model=ManyCeleryResultsInResponse,
)
@response_decorator()
def get_list_celery_results(
    list_celery_results_use_case: ListCeleryResultsUseCase = Depends(ListCeleryResultsUseCase),
    page_index: Annotated[int, Query(title="Page Index")] = 1,
    page_size: Annotated[int, Query(title="Page size", le=300)] = 20,
    name: Optional[str] = Query(None, title="Name"),
    sort: Optional[Sort] = Sort.DESC,
    sort_by: Optional[str] = "date_done",
    tag: Optional[CeleryResultTag] = None,
    current_admin=Depends(get_current_active_admin),
):
    authorization(current_admin, SUPER_ADMIN)
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListCeleryResultsRequestObject.builder(
        page_index=page_index,
        page_size=page_size,
        name=name,
        tag=tag,
        sort=sort_query,
    )
    response = list_celery_results_use_case.execute(request_object=req_object)
    return response
