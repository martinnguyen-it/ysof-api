from typing import Optional
from fastapi import Depends

from app.models.admin import AdminModel
from app.shared import request_object, use_case, response_object
from app.infra.roll_call.roll_call_repository import RollCallRepository
from app.shared.utils.general import get_current_season_value
from app.domain.shared.enum import AdminRole


class GetRollCallResultsRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        current_admin: AdminModel,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
        group: int | None = None,
        season: int | None = None,
    ):
        self.page_index = page_index
        self.page_size = page_size
        self.search = search
        self.sort = sort
        self.group = group
        self.season = season
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls,
        current_admin: AdminModel,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
        group: int | None = None,
        season: int | None = None,
    ):
        return GetRollCallResultsRequestObject(
            page_index=page_index,
            page_size=page_size,
            search=search,
            sort=sort,
            group=group,
            season=season,
            current_admin=current_admin,
        )


class GetRollCallResultsUseCase(use_case.UseCase):
    def __init__(self, roll_call_repository: RollCallRepository = Depends(RollCallRepository)):
        self.roll_call_repository = roll_call_repository

    def process_request(self, req_object: GetRollCallResultsRequestObject):
        current_season = get_current_season_value()
        match_pipeline = {}

        # Handle season access control
        if (
            isinstance(req_object.season, int)
            and (
                req_object.season <= req_object.current_admin.latest_season
                or AdminRole.ADMIN in req_object.current_admin.roles
            )
        ) or req_object.season is None:
            match_pipeline = {
                **match_pipeline,
                "seasons_info.season": req_object.season if req_object.season else current_season,
            }
        else:
            return response_object.ResponseFailure.build_parameters_error(
                f"Bạn không có quyền truy cập mùa {req_object.season}"
            )

        # Handle search
        if isinstance(req_object.search, str):
            match_pipeline = {
                **match_pipeline,
                "$or": [
                    {"email": {"$regex": req_object.search, "$options": "i"}},
                    {"full_name": {"$regex": req_object.search, "$options": "i"}},
                    {"holy_name": {"$regex": req_object.search, "$options": "i"}},
                    {"diocese": {"$regex": req_object.search, "$options": "i"}},
                    {"numerical_order": req_object.search},
                ],
            }

        # Handle group filter
        if isinstance(req_object.group, int):
            match_pipeline = {**match_pipeline, "seasons_info.group": req_object.group}

        return self.roll_call_repository.get_roll_call_results(
            season=req_object.season if req_object.season else current_season,
            page_size=req_object.page_size,
            page_index=req_object.page_index,
            sort=req_object.sort,
            match_pipeline=match_pipeline,
        )
