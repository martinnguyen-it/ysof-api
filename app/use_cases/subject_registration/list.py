from fastapi import Depends
from typing import Optional, Any
from app.shared import request_object, use_case
from app.infra.student.student_repository import StudentRepository
from app.shared.utils.general import get_current_season_value


class ListSubjectRegistrationsRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
        group: int | None = None,
    ):
        self.page_index = page_index
        self.page_size = page_size
        self.search = search
        self.sort = sort
        self.search = search
        self.group = group

    @classmethod
    def builder(
        cls,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
        group: int | None = None,
    ):
        return ListSubjectRegistrationsRequestObject(
            page_index=page_index, group=group, page_size=page_size, search=search, sort=sort
        )


class ListSubjectRegistrationsUseCase(use_case.UseCase):
    def __init__(self, student_repository: StudentRepository = Depends(StudentRepository)):
        self.student_repository = student_repository

    def process_request(self, req_object: ListSubjectRegistrationsRequestObject):
        current_season = get_current_season_value()
        match_pipeline: Optional[dict[str, Any]] = {"seasons_info.season": current_season}

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
        data = self.student_repository.list_subject_registrations(
            page_size=req_object.page_size,
            page_index=req_object.page_index,
            sort=req_object.sort,
            match_pipeline=match_pipeline,
        )
        return data
