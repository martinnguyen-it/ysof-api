import math
from typing import Optional, List, Dict, Any
from fastapi import Depends
from app.shared import request_object, use_case, response_object
from app.domain.admin.entity import Admin, AdminInDB, ManyAdminsInResponse
from app.domain.shared.entity import Pagination
from app.models.admin import AdminModel
from app.infra.admin.admin_repository import AdminRepository
from app.shared.constant import SUPER_ADMIN
from app.shared.utils.general import get_current_season_value
from app.domain.shared.enum import AdminRole


class ListAdminsRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        season: int | None = None,
        current_admin: AdminModel = None,
        sort: Optional[dict[str, int]] = None,
    ):
        self.page_index = page_index
        self.page_size = page_size
        self.search = search
        self.sort = sort
        self.season = season
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls,
        page_index: int,
        page_size: int,
        current_admin: AdminModel = None,
        search: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
        season: int | None = None,
    ):
        return ListAdminsRequestObject(
            page_index=page_index,
            page_size=page_size,
            search=search,
            current_admin=current_admin,
            season=season,
            sort=sort,
        )


class ListAdminsUseCase(use_case.UseCase):
    def __init__(self, admin_repository: AdminRepository = Depends(AdminRepository)):
        self.admin_repository = admin_repository

    def process_request(self, req_object: ListAdminsRequestObject):
        match_pipeline: Optional[Dict[str, Any]] = {}

        if isinstance(req_object.search, str):
            match_pipeline = {
                "$or": [
                    {"email": {"$regex": req_object.search, "$options": "i"}},
                    {"full_name": {"$regex": req_object.search, "$options": "i"}},
                    {"holy_name": {"$regex": req_object.search, "$options": "i"}},
                ]
            }

        current_season = get_current_season_value()
        is_super_admin = any(role in req_object.current_admin.roles for role in SUPER_ADMIN)

        if req_object.season is not None:
            if (is_super_admin and req_object.season != 0) or req_object.season in req_object.current_admin.seasons:
                match_pipeline = {**match_pipeline, "seasons": req_object.season}
            elif is_super_admin and req_object.season == 0:
                pass
            else:
                return response_object.ResponseFailure.build_parameters_error(
                    "Bạn không có quyền truy cập "
                    + (f"mùa {req_object.season}" if req_object.season != 0 else "tất cả mùa")
                )
        else:
            match_pipeline = {
                **match_pipeline,
                "seasons": (
                    req_object.current_admin.latest_season
                    if AdminRole.ADMIN not in req_object.current_admin.roles
                    else current_season
                ),
            }

        admins: List[AdminModel] = self.admin_repository.list(
            page_size=req_object.page_size,
            page_index=req_object.page_index,
            sort=req_object.sort,
            match_pipeline=match_pipeline,
        )

        total = self.admin_repository.count_list(match_pipeline=match_pipeline)
        data = [Admin(**AdminInDB.model_validate(model).model_dump()) for model in admins]
        return ManyAdminsInResponse(
            pagination=Pagination(
                total=total, page_index=req_object.page_index, total_pages=math.ceil(total / req_object.page_size)
            ),
            data=data,
        )
