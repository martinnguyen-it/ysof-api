import math
from typing import Optional, List, Dict, Any
from fastapi import Depends
from app.shared import request_object, response_object, use_case
from app.domain.student.entity import (
    ManyStudentsInStudentRequestResponse,
    StudentInDB,
    StudentInStudentRequestResponse,
)
from app.domain.shared.entity import Pagination
from app.models.student import StudentModel
from app.infra.student.student_repository import StudentRepository


class ListStudentsInStudentRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        group: int | None = None,
        sort: Optional[dict[str, int]] = None,
        season: int | None = None,
        current_student: StudentModel | None = None,
    ):
        self.page_index = page_index
        self.page_size = page_size
        self.search = search
        self.sort = sort
        self.group = group
        self.season = season
        self.current_student = current_student

    @classmethod
    def builder(
        cls,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
        group: int | None = None,
        season: int | None = None,
        current_student: StudentModel | None = None,
    ):
        invalid_req = request_object.InvalidRequestObject()
        if not current_student:
            invalid_req.add_error("current_student", "Not found your info")

        if invalid_req.has_errors():
            return invalid_req

        return ListStudentsInStudentRequestObject(
            page_index=page_index,
            page_size=page_size,
            search=search,
            group=group,
            sort=sort,
            season=season,
            current_student=current_student,
        )


class ListStudentsInStudentRequestUseCase(use_case.UseCase):
    def __init__(
        self,
        student_repository: StudentRepository = Depends(StudentRepository),
    ):
        self.student_repository = student_repository

    def process_request(self, req_object: ListStudentsInStudentRequestObject):
        select_season = None

        if req_object.season:
            exists = any(
                season.season == req_object.season
                for season in req_object.current_student.seasons_info
            )
            if exists:
                select_season = req_object.season

            else:
                return response_object.ResponseFailure.build_parameters_error(
                    "Bạn không có quyền truy cập."
                )
        else:
            select_season = req_object.current_student.seasons_info[-1].season

        match_pipeline: Optional[Dict[str, Any]] = {"seasons_info.season": select_season}

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

        return ManyStudentsInStudentRequestResponse(
            pagination=Pagination(
                total=total,
                page_index=req_object.page_index,
                total_pages=math.ceil(total / req_object.page_size),
            ),
            data=[
                StudentInStudentRequestResponse(
                    **StudentInDB.model_validate(model).model_dump(exclude={"seasons_info"}),
                    season_info=next(
                        (item for item in model.seasons_info if item.season == select_season), None
                    ),
                )
                for model in students
            ],
        )
