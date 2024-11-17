from fastapi import Depends
from typing import Optional
from app.shared import request_object, response_object, use_case
from app.domain.student.entity import Student, StudentInDB
from app.infra.student.student_repository import StudentRepository
from app.models.student import StudentModel


class GetStudentRequestObject(request_object.ValidRequestObject):
    def __init__(self, student_id: str):
        self.student_id = student_id

    @classmethod
    def builder(cls, student_id: str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not id:
            invalid_req.add_error("id", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return GetStudentRequestObject(student_id=student_id)


class GetStudentCase(use_case.UseCase):
    def __init__(self, student_repository: StudentRepository = Depends(StudentRepository)):
        self.student_repository = student_repository

    def process_request(self, req_object: GetStudentRequestObject):
        student: Optional[StudentModel] = self.student_repository.get_by_id(
            student_id=req_object.student_id
        )
        if not student:
            return response_object.ResponseFailure.build_not_found_error(
                message="Học viên không tồn tại"
            )

        return Student(**StudentInDB.model_validate(student).model_dump())
