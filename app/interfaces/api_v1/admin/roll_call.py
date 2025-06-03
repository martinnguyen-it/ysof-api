from typing import Annotated
from fastapi import APIRouter, Body, Depends, Query

from app.domain.roll_call.entity import StudentRollCallResultInResponse
from app.domain.rolll_call.entity import RollCallBulkSheet
from app.domain.shared.enum import AdminRole, Sort
from app.infra.security.security_service import authorization, get_current_active_admin
from app.models.admin import AdminModel
from app.shared.constant import SUPER_ADMIN
from app.shared.decorator import response_decorator
from app.use_cases.roll_call.bulk_by_sheet import (
    RollCallBySheetRequestObject,
    RollCallBySheetUseCase,
)
from app.use_cases.roll_call.get_results import (
    GetRollCallResultsRequestObject,
    GetRollCallResultsUseCase,
)


router = APIRouter()


@router.post("/by-sheet")
@response_decorator()
def roll_call_by_sheet(
    payload: RollCallBulkSheet = Body(...),
    roll_call_by_sheet_use_case: RollCallBySheetUseCase = Depends(RollCallBySheetUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL])
    req_object = RollCallBySheetRequestObject.builder(payload=payload, current_admin=current_admin)
    response = roll_call_by_sheet_use_case.execute(request_object=req_object)
    return response


@router.get("/results", response_model=StudentRollCallResultInResponse)
@response_decorator()
def get_roll_call_results(
    get_roll_call_results_use_case: GetRollCallResultsUseCase = Depends(GetRollCallResultsUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
    page_index: int = 1,
    page_size: Annotated[int, Query(title="Page size", le=500)] = 300,
    search: str | None = None,
    group: int | None = None,
    sort: Sort = Sort.ASCE,
    sort_by: str = "numerical_order",
    season: int | None = None,
):
    """
    Get roll call results for completed subjects.
    Returns a list of students with their roll call status for each subject.

    The result for each subject can be:
    - none: No registration
    - completed: Attended zoom and has evaluation, or attended zoom with NO_EVALUATION absent type
    - no_complete: Only has evaluation or attended zoom without evaluation
    - absent: Has NO_ATTEND absent type
    """
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BKL])
    if sort_by in ["numerical_order", "season", "group"]:
        sort_by = f"seasons_info.{sort_by}"
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}
    req_object = GetRollCallResultsRequestObject.builder(
        page_index=page_index,
        page_size=page_size,
        sort=sort_query,
        search=search,
        group=group,
        season=season,
        current_admin=current_admin,
    )
    response = get_roll_call_results_use_case.execute(request_object=req_object)
    return response
