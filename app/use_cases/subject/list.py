from typing import Optional, List
from fastapi import Depends
from app.shared import request_object, use_case, response_object
from app.domain.subject.entity import Subject, SubjectInDB
from app.models.subject import SubjectModel
from app.infra.subject.subject_repository import SubjectRepository
from app.domain.lecturer.entity import Lecturer, LecturerInDB
from app.shared.utils.general import get_current_season_value
from app.models.admin import AdminModel


class ListSubjectsRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        current_admin: AdminModel,
        search: Optional[str] = None,
        subdivision: Optional[str] = None,
        season: int | None = None,
        sort: Optional[dict[str, int]] = None,
    ):
        self.search = search
        self.sort = sort
        self.season = season
        self.subdivision = subdivision
        self.current_admin = current_admin

    @classmethod
    def builder(
        cls,
        current_admin: AdminModel,
        search: Optional[str] = None,
        subdivision: Optional[str] = None,
        season: int | None = None,
        sort: Optional[dict[str, int]] = None,
    ):
        return ListSubjectsRequestObject(
            season=season, search=search, sort=sort, subdivision=subdivision, current_admin=current_admin
        )


class ListSubjectsUseCase(use_case.UseCase):
    def __init__(self, subject_repository: SubjectRepository = Depends(SubjectRepository)):
        self.subject_repository = subject_repository

    def process_request(self, req_object: ListSubjectsRequestObject):
        current_season = get_current_season_value()
        match_pipeline = {}

        if (
            isinstance(req_object.season, int) and req_object.season <= req_object.current_admin.current_season
        ) or req_object.season is None:
            match_pipeline = {**match_pipeline, "season": req_object.season if req_object.season else current_season}
        else:
            return response_object.ResponseFailure.build_parameters_error(
                "Bạn không có quyền truy cập "
                + (f"mùa {req_object.season}" if req_object.season != 0 else "tất cả mùa")
            )

        if isinstance(req_object.search, str):
            match_pipeline = {
                **match_pipeline,
                "$or": [
                    {"lecturer": {"$regex": req_object.search, "$options": "i"}},
                    {"code": {"$regex": req_object.search, "$options": "i"}},
                ],
            }
        if isinstance(req_object.subdivision, str):
            match_pipeline = {**match_pipeline, "subdivision": req_object.subdivision}
        print(match_pipeline)

        subjects: List[SubjectModel] = self.subject_repository.list(sort=req_object.sort, match_pipeline=match_pipeline)

        return [
            Subject(
                **SubjectInDB.model_validate(subject).model_dump(exclude=({"lecturer"})),
                lecturer=Lecturer(**LecturerInDB.model_validate(subject.lecturer).model_dump()),
            )
            for subject in subjects
        ]
