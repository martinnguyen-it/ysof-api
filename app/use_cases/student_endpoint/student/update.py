from typing import Optional
from fastapi import Depends
from app.domain.student.entity import (
    Student,
    StudentInDB,
    StudentUpdateMePayload,
    StudentUpdateMeTime,
)
from app.infra.student.student_repository import StudentRepository
from app.models.student import StudentModel
from app.shared import request_object, use_case


class UpdateStudentMeRequestObject(request_object.ValidRequestObject):
    def __init__(self, current_student: StudentModel, obj_in: StudentUpdateMePayload) -> None:
        self.obj_in = obj_in
        self.current_student = current_student

    @classmethod
    def builder(
        cls,
        current_student: StudentModel,
        payload: Optional[StudentUpdateMePayload] | None = None,
    ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateStudentMeRequestObject(obj_in=payload, current_student=current_student)


class UpdateStudentMeUseCase(use_case.UseCase):
    def __init__(
        self,
        student_repository: StudentRepository = Depends(StudentRepository),
    ):
        self.student_repository = student_repository

    def process_request(self, req_object: UpdateStudentMeRequestObject):
        self.student_repository.update(
            id=req_object.current_student.id,
            data=StudentUpdateMeTime(**req_object.obj_in.model_dump()).model_dump(
                exclude_none=True
            ),
        )
        req_object.current_student.reload()

        return Student(**StudentInDB.model_validate(req_object.current_student).model_dump())
