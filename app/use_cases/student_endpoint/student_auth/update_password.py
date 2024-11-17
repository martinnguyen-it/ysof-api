from datetime import datetime, timezone
from fastapi import Depends

from app.domain.auth.entity import UpdatePassword
from app.models.student import StudentModel
from app.infra.security.security_service import get_password_hash, verify_password
from app.infra.student.student_repository import StudentRepository
from app.shared import request_object, use_case, response_object


class UpdateStudentPasswordRequestObject(request_object.ValidRequestObject):
    def __init__(self, payload: UpdatePassword, current_student: StudentModel):
        self.payload = payload
        self.current_student = current_student

    @classmethod
    def builder(cls, payload: UpdatePassword, current_student: StudentModel):
        invalid_req = request_object.InvalidRequestObject()
        if not payload:
            invalid_req.add_error("payload", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateStudentPasswordRequestObject(payload=payload, current_student=current_student)


class UpdateStudentPasswordUseCase(use_case.UseCase):
    def __init__(
        self,
        student_repository: StudentRepository = Depends(StudentRepository),
    ):
        self.student_repository = student_repository

    def process_request(self, req_object: UpdateStudentPasswordRequestObject):
        checker = verify_password(
            req_object.payload.old_password, req_object.current_student.password
        )
        if not checker:
            return response_object.ResponseFailure.build_parameters_error(message="Sai mật khẩu")

        res = self.student_repository.update(
            id=req_object.current_student.id,
            data={
                "password": get_password_hash(req_object.payload.new_password),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        if res:
            return {"success": True}
        else:
            return response_object.ResponseFailure.build_system_error(
                message="Something went wrong"
            )
