from typing import Optional
from fastapi import Depends

from app.config import settings
from app.models.subject import SubjectModel
from app.shared import request_object, use_case, response_object

from app.domain.subject.entity import Subject, SubjectInCreate, SubjectInDB
from app.infra.subject.subject_repository import SubjectRepository
from app.domain.lecturer.entity import Lecturer, LecturerInDB
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.models.lecturer import LecturerModel


class CreateSubjectRequestObject(request_object.ValidRequestObject):
    def __init__(self, subject_in: SubjectInCreate) -> None:
        self.subject_in = subject_in

    @classmethod
    def builder(cls, payload: Optional[SubjectInCreate] = None) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return CreateSubjectRequestObject(subject_in=payload)


class CreateSubjectUseCase(use_case.UseCase):
    def __init__(self, subject_repository: SubjectRepository = Depends(SubjectRepository),
                 lecturer_repository: LecturerRepository = Depends(LecturerRepository)):
        self.subject_repository = subject_repository
        self.lecturer_repository = lecturer_repository

    def process_request(self, req_object: CreateSubjectRequestObject):
        lecturer: Optional[LecturerModel] = self.lecturer_repository.get_by_id(
            req_object.subject_in.lecturer)
        if not lecturer:
            return response_object.ResponseFailure.build_not_found_error("Giảng viên không tồn tại")

        subject_in: SubjectInCreate = req_object.subject_in
        obj_in: SubjectInDB = SubjectInDB(
            **subject_in.model_dump(exclude={"lecturer"}),
            lecturer=lecturer,
            session=settings.CURRENT_SEASON,
        )
        subject: SubjectModel = self.subject_repository.create(
            subject=obj_in)

        return Subject(**SubjectInDB.model_validate(subject).model_dump(exclude=({"lecturer"})),
                       lecturer=Lecturer(**LecturerInDB.model_validate(subject.lecturer).model_dump()))
