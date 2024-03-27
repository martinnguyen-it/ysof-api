from typing import Optional, List
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.subject.entity import Subject, SubjectInDB
from app.models.subject import SubjectModel
from app.infra.subject.subject_repository import SubjectRepository
from app.domain.lecturer.entity import Lecturer, LecturerInDB


class ListSubjectsRequestObject(request_object.ValidRequestObject):
    def __init__(self,  search: Optional[str] = None, sort: Optional[dict[str, int]] = None):
        self.search = search
        self.sort = sort

    @classmethod
    def builder(cls,  search: Optional[str] = None, sort: Optional[dict[str, int]] = None):
        return ListSubjectsRequestObject(search=search, sort=sort)


class ListSubjectsUseCase(use_case.UseCase):
    def __init__(self, subject_repository: SubjectRepository = Depends(SubjectRepository)):
        self.subject_repository = subject_repository

    def process_request(self, req_object: ListSubjectsRequestObject):
        match_pipeline = None

        if isinstance(req_object.search, str):
            match_pipeline = {
                "$match": {
                    "$or": [
                        {"lecturer": {"$regex": req_object.search, "$options": "i"}},
                        {"code": {
                            "$regex": req_object.search, "$options": "i"}},

                    ]
                }
            }

        subjects: List[SubjectModel] = self.subject_repository.list(
            sort=req_object.sort,
            match_pipeline=match_pipeline
        )

        return [Subject(**SubjectInDB.model_validate(subject).model_dump(exclude=({"lecturer"})),
                        lecturer=Lecturer(**LecturerInDB.model_validate(subject.lecturer).model_dump()))
                for subject in subjects]
