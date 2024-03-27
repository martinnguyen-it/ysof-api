from fastapi import Depends
from typing import Optional
from app.shared import request_object, response_object, use_case
from app.domain.subject.entity import Subject, SubjectInDB
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.domain.lecturer.entity import Lecturer, LecturerInDB


class GetSubjectRequestObject(request_object.ValidRequestObject):
    def __init__(self, subject_id: str):
        self.subject_id = subject_id

    @classmethod
    def builder(cls, subject_id: str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not id:
            invalid_req.add_error("id", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return GetSubjectRequestObject(subject_id=subject_id)


class GetSubjectCase(use_case.UseCase):
    def __init__(self, subject_repository: SubjectRepository = Depends(SubjectRepository)):
        self.subject_repository = subject_repository

    def process_request(self, req_object: GetSubjectRequestObject):
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(
            subject_id=req_object.subject_id)
        if not subject:
            return response_object.ResponseFailure.build_not_found_error(message="Môn học không tồn tại")

        return Subject(**SubjectInDB.model_validate(subject).model_dump(exclude=({"lecturer"})),
                       lecturer=Lecturer(**LecturerInDB.model_validate(subject.lecturer).model_dump()))
