from fastapi import Depends
from typing import Optional
from app.shared import request_object, use_case, response_object
from app.infra.subject.subject_registration_repository import SubjectRegistrationRepository
from app.infra.subject.subject_repository import SubjectRepository
from app.models.subject import SubjectModel
from app.domain.subject.entity import StudentInSubject
from app.domain.student.entity import StudentInDB
from app.models.subject_registration import SubjectRegistrationModel


class ListSubjectRegistrationsBySubjectIdRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        subject_id=str,
    ):
        self.subject_id = subject_id

    @classmethod
    def builder(cls, subject_id=str):
        return ListSubjectRegistrationsBySubjectIdRequestObject(subject_id=subject_id)


class ListSubjectRegistrationsBySubjectIdUseCase(use_case.UseCase):
    def __init__(
        self,
        subject_repository: SubjectRepository = Depends(SubjectRepository),
        subject_registration_repository: SubjectRegistrationRepository = Depends(SubjectRegistrationRepository),
    ):
        self.subject_repository = subject_repository
        self.subject_registration_repository = subject_registration_repository

    def process_request(self, req_object: ListSubjectRegistrationsBySubjectIdRequestObject):
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(subject_id=req_object.subject_id)
        if not subject:
            return response_object.ResponseFailure.build_not_found_error(message="Môn học không tồn tại")
        docs: list[SubjectRegistrationModel] = self.subject_registration_repository.get_by_subject_id(
            subject_id=subject.id
        )

        return [StudentInSubject(**StudentInDB.model_validate(doc.student).model_dump()) for doc in docs]
