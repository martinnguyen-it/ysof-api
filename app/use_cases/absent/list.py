from bson import ObjectId
from fastapi import Depends
from app.shared import request_object, use_case
from app.domain.subject.entity import SubjectInDB, SubjectInStudent
from app.domain.lecturer.entity import LecturerInDB, LecturerInStudent
from app.infra.absent.absent_repository import AbsentRepository
from app.models.absent import AbsentModel
from app.domain.absent.entity import AbsentInDB, AdminAbsentInResponse
from app.domain.student.entity import Student, StudentInDB
from app.infra.subject.subject_repository import SubjectRepository


class ListAbsentRequestObject(request_object.ValidRequestObject):
    def __init__(self, subject_id: str):
        self.subject_id = subject_id

    @classmethod
    def builder(cls, subject_id: str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not subject_id:
            invalid_req.add_error("subject_id", "Miss subject id")

        if invalid_req.has_errors():
            return invalid_req

        return ListAbsentRequestObject(subject_id=subject_id)


class ListAbsentUseCase(use_case.UseCase):
    def __init__(
        self,
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        absent_repository: AbsentRepository = Depends(AbsentRepository),
    ):
        self.absent_repository = absent_repository
        self.subject_repository = subject_repository

    def process_request(self, req_object: ListAbsentRequestObject):
        absents: list[AbsentModel] = self.absent_repository.list(
            match_pipeline={"subject": ObjectId(req_object.subject_id)}
        )

        return [
            AdminAbsentInResponse(
                **AbsentInDB.model_validate(absent).model_dump(exclude={"student", "subject"}),
                subject=SubjectInStudent(
                    **SubjectInDB.model_validate(absent.subject).model_dump(exclude=({"lecturer"})),
                    lecturer=LecturerInStudent(**LecturerInDB.model_validate(absent.subject.lecturer).model_dump()),
                ),
                student=Student(**StudentInDB.model_validate(absent.student).model_dump()),
            )
            for absent in absents
        ]
