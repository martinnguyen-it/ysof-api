from typing import Optional, List
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.subject.entity import Subject, SubjectInDB
from app.models.subject import SubjectModel
from app.infra.subject.subject_repository import SubjectRepository
from app.domain.lecturer.entity import Lecturer, LecturerInDB
from app.infra.season.season_repository import SeasonRepository
from app.models.season import SeasonModel


class ListSubjectsRequestObject(request_object.ValidRequestObject):
    def __init__(self,
                 search: Optional[str] = None,
                 subdivision: Optional[str] = None,
                 season: int | None = None,
                 sort: Optional[dict[str, int]] = None):
        self.search = search
        self.sort = sort
        self.season = season
        self.subdivision = subdivision

    @classmethod
    def builder(cls,
                search: Optional[str] = None,
                subdivision: Optional[str] = None,
                season: int | None = None,
                sort: Optional[dict[str, int]] = None):
        return ListSubjectsRequestObject(season=season, search=search, sort=sort, subdivision=subdivision)


class ListSubjectsUseCase(use_case.UseCase):
    def __init__(self, subject_repository: SubjectRepository = Depends(SubjectRepository),
                 season_repository: SeasonRepository = Depends(SeasonRepository)):
        self.season_repository = season_repository
        self.subject_repository = subject_repository

    def process_request(self, req_object: ListSubjectsRequestObject):
        current_season: SeasonModel = self.season_repository.get_current_season()
        match_pipeline = {
            "season": req_object.season if req_object.season else current_season.season
        }

        if isinstance(req_object.search, str):
            match_pipeline = {
                **match_pipeline,
                "$or": [
                    {"lecturer": {"$regex": req_object.search, "$options": "i"}},
                    {"code": {
                        "$regex": req_object.search, "$options": "i"}},

                ]
            }
        if isinstance(req_object.subdivision, str):
            match_pipeline = {
                **match_pipeline,
                "subdivision": req_object.subdivision
            }
        print(match_pipeline)

        subjects: List[SubjectModel] = self.subject_repository.list(
            sort=req_object.sort,
            match_pipeline=match_pipeline
        )

        return [Subject(**SubjectInDB.model_validate(subject).model_dump(exclude=({"lecturer"})),
                        lecturer=Lecturer(**LecturerInDB.model_validate(subject.lecturer).model_dump()))
                for subject in subjects]
