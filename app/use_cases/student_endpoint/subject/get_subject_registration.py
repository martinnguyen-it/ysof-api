from bson import ObjectId
from fastapi import Depends
from app.shared import request_object, use_case
from app.infra.subject.subject_registration_repository import SubjectRegistrationRepository


class GetSubjectRegistrationStudentRequestObject(request_object.ValidRequestObject):
    def __init__(self, student_id: ObjectId):
        self.student_id = student_id

    @classmethod
    def builder(cls, student_id: ObjectId) -> request_object.RequestObject:
        return GetSubjectRegistrationStudentRequestObject(student_id=student_id)


class GetSubjectRegistrationStudentCase(use_case.UseCase):
    def __init__(
        self,
        subject_registration_repository: SubjectRegistrationRepository = Depends(
            SubjectRegistrationRepository
        ),
    ):
        self.subject_registration_repository = subject_registration_repository

    def process_request(self, req_object: GetSubjectRegistrationStudentRequestObject):
        res = self.subject_registration_repository.get_by_student_id(
            student_id=req_object.student_id
        )
        return res
