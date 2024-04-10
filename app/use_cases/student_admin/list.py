import math
from typing import Optional, List, Dict, Any
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.student.entity import Student, StudentInDB, ManyStudentsInResponse
from app.domain.shared.entity import Pagination
from app.models.student import StudentModel
from app.infra.student.student_repository import StudentRepository
from app.models.admin import AdminModel
from app.shared.utils.general import get_current_season_value


class ListStudentsRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        group: int | None = None,
        current_admin: AdminModel = None,
        sort: Optional[dict[str, int]] = None,
    ):
        self.page_index = page_index
        self.page_size = page_size
        self.search = search
        self.sort = sort
        self.group = group
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls,
        page_index: int,
        page_size: int,
        current_admin: AdminModel = None,
        search: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
        group: int | None = None,
    ):
        return ListStudentsRequestObject(
            page_index=page_index,
            page_size=page_size,
            search=search,
            current_admin=current_admin,
            group=group,
            sort=sort,
        )


class ListStudentsUseCase(use_case.UseCase):
    def __init__(
        self,
        student_repository: StudentRepository = Depends(StudentRepository),
    ):
        self.student_repository = student_repository

    def process_request(self, req_object: ListStudentsRequestObject):
        current_season = get_current_season_value()

        match_pipeline: Optional[Dict[str, Any]] = {"current_season": current_season}

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

        if isinstance(req_object.group, int):
            match_pipeline = {**match_pipeline, "group": req_object.group}

        students: List[StudentModel] = self.student_repository.list(
            page_size=req_object.page_size,
            page_index=req_object.page_index,
            sort=req_object.sort,
            match_pipeline=match_pipeline,
        )

        total = self.student_repository.count_list(match_pipeline=match_pipeline)
        data = [Student(**StudentInDB.model_validate(model).model_dump()) for model in students]

        return ManyStudentsInResponse(
            pagination=Pagination(
                total=total, page_index=req_object.page_index, total_pages=math.ceil(total / req_object.page_size)
            ),
            data=data,
        )
