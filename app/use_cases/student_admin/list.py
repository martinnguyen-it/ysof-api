import math
from typing import Optional, List, Dict, Any
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.student.entity import (
    ManyStudentsInResponse,
    ManyStudentsInStudentRequestResponse,
    Student,
    StudentInDB,
    StudentInStudentRequestResponse,
)
from app.domain.shared.entity import Pagination
from app.models.student import StudentModel
from app.infra.student.student_repository import StudentRepository
from app.shared.utils.general import get_current_season_value


class ListStudentsRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        group: int | None = None,
        sort: Optional[dict[str, int]] = None,
        is_student_request: bool = False,
    ):
        self.page_index = page_index
        self.page_size = page_size
        self.search = search
        self.sort = sort
        self.group = group
        self.is_student_request = is_student_request

    @classmethod
    def builder(
        cls,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
        group: int | None = None,
        is_student_request: bool = False,
    ):
        return ListStudentsRequestObject(
            page_index=page_index,
            page_size=page_size,
            search=search,
            group=group,
            sort=sort,
            is_student_request=is_student_request,
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
            num = None
            try:
                num = int(req_object.search)
            except Exception:
                pass
            match_pipeline = {
                **match_pipeline,
                "$or": [
                    {"email": {"$regex": req_object.search, "$options": "i"}},
                    {"full_name": {"$regex": req_object.search, "$options": "i"}},
                    {"holy_name": {"$regex": req_object.search, "$options": "i"}},
                    {"diocese": {"$regex": req_object.search, "$options": "i"}},
                    {"numerical_order": num},
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

        return (
            ManyStudentsInStudentRequestResponse(
                pagination=Pagination(
                    total=total, page_index=req_object.page_index, total_pages=math.ceil(total / req_object.page_size)
                ),
                data=[
                    StudentInStudentRequestResponse(**StudentInDB.model_validate(model).model_dump())
                    for model in students
                ],
            )
            if req_object.is_student_request
            else ManyStudentsInResponse(
                pagination=Pagination(
                    total=total, page_index=req_object.page_index, total_pages=math.ceil(total / req_object.page_size)
                ),
                data=[Student(**StudentInDB.model_validate(model).model_dump()) for model in students],
            )
        )
