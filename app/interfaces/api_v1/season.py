from fastapi import APIRouter, Body, Depends,  Query, HTTPException, Path
from typing import Annotated, Optional

from app.domain.season.entity import Season, SeasonInCreate, SeasonInUpdate
from app.domain.shared.enum import Sort
from app.infra.security.security_service import authorization, get_current_active_admin
from app.shared.decorator import response_decorator
from app.use_cases.season.create import (
    CreateSeasonRequestObject,
    CreateSeasonUseCase,
)
from app.models.admin import AdminModel
from app.shared.constant import SUPER_ADMIN
from app.use_cases.season.list import ListSeasonsUseCase, ListSeasonsRequestObject
from app.use_cases.season.update import UpdateSeasonUseCase, UpdateSeasonRequestObject
from app.use_cases.season.get import GetSeasonRequestObject, GetSeasonCase
from app.use_cases.season.delete import DeleteSeasonRequestObject, DeleteSeasonUseCase
from app.use_cases.season.get_current import GetCurrentSeasonCase
from app.use_cases.season.mark_current import (MarkCurrentSeasonRequestObject,
                                               MarkCurrentSeasonUseCase)

router = APIRouter()


@router.post(
    "",
    response_model=Season,
)
@response_decorator()
def create_season(
        payload: SeasonInCreate = Body(...,
                                       title="Season In Create payload"),
        create_season_use_case: CreateSeasonUseCase = Depends(
            CreateSeasonUseCase),
        current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, SUPER_ADMIN)
    req_object = CreateSeasonRequestObject.builder(payload=payload)
    response = create_season_use_case.execute(request_object=req_object)
    return response


@router.get(
    "",
    response_model=list[Season],
)
@response_decorator()
def get_list_seasons(
        list_seasons_use_case: ListSeasonsUseCase = Depends(
            ListSeasonsUseCase),
        page_index: Annotated[int, Query(title="Page Index")] = 1,
        page_size: Annotated[int, Query(title="Page size")] = 20,
        sort: Optional[Sort] = Sort.DESC,
        sort_by: Optional[str] = 'season',
):
    annotations = {}
    for base in reversed(Season.__mro__):
        annotations.update(getattr(base, '__annotations__', {}))
    if sort_by not in annotations:
        raise HTTPException(
            status_code=400, detail=f"Invalid sort_by: {sort_by}")
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListSeasonsRequestObject.builder(
        sort=sort_query, page_size=page_size, page_index=page_index)
    response = list_seasons_use_case.execute(request_object=req_object)
    return response


@router.get(
    "/current",
    response_model=Season,
)
@response_decorator()
def get_current_season(
        get_season_use_case: GetCurrentSeasonCase = Depends(
            GetCurrentSeasonCase),
):
    response = get_season_use_case.process_request()
    return response


@router.get(
    "/{season_id}",
    response_model=Season,
)
@response_decorator()
def get_season_by_id(
        season_id: str = Path(..., title="Season id"),
        get_season_use_case: GetSeasonCase = Depends(GetSeasonCase),
):
    get_season_request_object = GetSeasonRequestObject.builder(
        season_id=season_id)
    response = get_season_use_case.execute(
        request_object=get_season_request_object)
    return response


@router.put(
    "/{id}",
    response_model=Season,
)
@response_decorator()
def update_season(
        id: str = Path(..., title="Season Id"),
        payload: SeasonInUpdate = Body(...,
                                       title="Season updated payload"),
        update_season_use_case: UpdateSeasonUseCase = Depends(
            UpdateSeasonUseCase),
        current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, SUPER_ADMIN)
    req_object = UpdateSeasonRequestObject.builder(id=id, payload=payload)
    response = update_season_use_case.execute(request_object=req_object)
    return response


@router.put(
    "/{id}/current",
    response_model=Season,
)
@response_decorator()
def mark_season_current(
        id: str = Path(..., title="Season Id"),
        mark_current_season_use_case: MarkCurrentSeasonUseCase = Depends(
            MarkCurrentSeasonUseCase),
        current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, SUPER_ADMIN)
    req_object = MarkCurrentSeasonRequestObject.builder(id=id)
    response = mark_current_season_use_case.execute(request_object=req_object)
    return response


@router.delete("/{id}")
@response_decorator()
def delete_season(
        id: str = Path(..., title="Season Id"),
        delete_season_use_case: DeleteSeasonUseCase = Depends(
            DeleteSeasonUseCase),
        current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, SUPER_ADMIN)
    req_object = DeleteSeasonRequestObject.builder(id=id)
    response = delete_season_use_case.execute(request_object=req_object)
    return response
