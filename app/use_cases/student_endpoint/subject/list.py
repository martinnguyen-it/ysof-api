from typing import Optional, List
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.subject.entity import SubjectInDB, SubjectInStudent
from app.models.subject import SubjectModel
from app.infra.subject.subject_repository import SubjectRepository
from app.domain.lecturer.entity import LecturerInDB, LecturerInStudent
from app.models.student import StudentModel


class ListSubjectsStudentRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        current_student: StudentModel,
        search: Optional[str] = None,
        subdivision: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
    ):
        self.search = search
        self.sort = sort
        self.subdivision = subdivision
        self.current_student = current_student

    @classmethod
    def builder(
        cls,
        current_student: StudentModel,
        search: Optional[str] = None,
        subdivision: Optional[str] = None,
        sort: Optional[dict[str, int]] = None,
    ):
        return ListSubjectsStudentRequestObject(
            search=search, sort=sort, subdivision=subdivision, current_student=current_student
        )


class ListSubjectsStudentUseCase(use_case.UseCase):
    def __init__(self, subject_repository: SubjectRepository = Depends(SubjectRepository)):
        self.subject_repository = subject_repository

    def process_request(self, req_object: ListSubjectsStudentRequestObject):
        match_pipeline = {"season": req_object.current_student.current_season}

        if isinstance(req_object.search, str):
            match_pipeline = {
                **match_pipeline,
                "$or": [
                    {"title": {"$regex": req_object.search, "$options": "i"}},
                    {"code": {"$regex": req_object.search, "$options": "i"}},
                ],
            }
        if isinstance(req_object.subdivision, str):
            match_pipeline = {**match_pipeline, "subdivision": req_object.subdivision}

        subjects: List[SubjectModel] = self.subject_repository.list(sort=req_object.sort, match_pipeline=match_pipeline)

        return [
            SubjectInStudent(
                **SubjectInDB.model_validate(subject).model_dump(exclude=({"lecturer"})),
                lecturer=LecturerInStudent(**LecturerInDB.model_validate(subject.lecturer).model_dump()),
            )
            for subject in subjects
        ]
