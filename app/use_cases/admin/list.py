import math
from typing import Optional, List, Dict, Any
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.admin.entity import Admin, AdminInDB, ManyAdminsInResponse
from app.domain.shared.entity import Pagination
from app.models.admin import AdminModel
from app.infra.admin.admin_repository import AdminRepository


class ListAdminsRequestObject(request_object.ValidRequestObject):
    def __init__(self, page_index: int, page_size: int, search: Optional[str] = None,
                 sort: Optional[dict[str, int]] = None):
        self.page_index = page_index
        self.page_size = page_size
        self.search = search
        self.sort = sort

    @classmethod
    def builder(cls, page_index: int, page_size: int, search: Optional[str] = None,
                sort: Optional[dict[str, int]] = None
                ):
        return ListAdminsRequestObject(page_index=page_index, page_size=page_size, search=search,
                                       sort=sort)


class ListAdminsUseCase(use_case.UseCase):
    def __init__(self, admin_repository: AdminRepository = Depends(AdminRepository)):
        self.admin_repository = admin_repository

    def process_request(self, req_object: ListAdminsRequestObject):
        match_pipeline: Optional[Dict[str, Any]] = None

        if isinstance(req_object.search, str):
            match_pipeline = {
                "$match": {
                    "$or": [
                        {"email": {"$regex": req_object.search, "$options": "i"}},
                        {"full_name": {"$regex": req_object.search, "$options": "i"}},
                        {"holy_name": {"$regex": req_object.search, "$options": "i"}}
                    ]
                }
            }

        admins: List[AdminModel] = self.admin_repository.list(page_size=req_object.page_size,
                                                              page_index=req_object.page_index,
                                                              sort=req_object.sort,
                                                              match_pipeline=match_pipeline
                                                              )

        total = self.admin_repository.count_list(match_pipeline=match_pipeline)
        data = [Admin(**AdminInDB.model_validate(model).model_dump())
                for model in admins]
        return ManyAdminsInResponse(
            pagination=Pagination(
                total=total, page_index=req_object.page_index, total_pages=math.ceil(
                    total / req_object.page_size)
            ),
            data=data,
        )
