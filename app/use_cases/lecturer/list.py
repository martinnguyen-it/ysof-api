import math
from typing import Optional, List
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.lecturer.entity import Lecturer, LecturerInDB, ManyLecturersInResponse
from app.domain.shared.entity import Pagination
from app.models.lecturer import LecturerModel
from app.infra.lecturer.lecturer_repository import LecturerRepository


class ListLecturersRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
    ):
        self.page_index = page_index
        self.page_size = page_size
        self.search = search
        self.sort = sort

    @classmethod
    def builder(
        cls,
        page_index: int,
        page_size: int,
        search: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
    ):
        return ListLecturersRequestObject(
            page_index=page_index, page_size=page_size, search=search, sort=sort
        )


class ListLecturersUseCase(use_case.UseCase):
    def __init__(self, lecturer_repository: LecturerRepository = Depends(LecturerRepository)):
        self.lecturer_repository = lecturer_repository

    def process_request(self, req_object: ListLecturersRequestObject):
        match_pipeline = None
        if isinstance(req_object.search, str):
            match_pipeline = {
                "$match": {
                    "$or": [
                        {"full_name": {"$regex": req_object.search, "$options": "i"}},
                        {"holy_name": {"$regex": req_object.search, "$options": "i"}},
                    ]
                }
            }
        lecturers: List[LecturerModel] = self.lecturer_repository.list(
            page_size=req_object.page_size,
            page_index=req_object.page_index,
            sort=req_object.sort,
            match_pipeline=match_pipeline,
        )

        total = self.lecturer_repository.count_list(match_pipeline=match_pipeline)

        return ManyLecturersInResponse(
            pagination=Pagination(
                total=total,
                page_index=req_object.page_index,
                total_pages=math.ceil(total / req_object.page_size),
            ),
            data=[Lecturer(**LecturerInDB.model_validate(doc).model_dump()) for doc in lecturers],
        )
