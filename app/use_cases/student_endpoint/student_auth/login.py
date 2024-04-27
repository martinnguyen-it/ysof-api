from fastapi import Depends

from app.domain.auth.entity import LoginRequest, TokenData, AuthStudentInfoInResponse
from app.domain.student.entity import Student, StudentInDB
from app.models.student import StudentModel
from app.infra.security.security_service import verify_password, create_access_token
from app.infra.student.student_repository import StudentRepository
from app.shared import request_object, use_case, response_object


class LoginStudentRequestObject(request_object.ValidRequestObject):
    def __init__(self, login_payload: LoginRequest):
        self.login_payload = login_payload

    @classmethod
    def builder(cls, login_payload: LoginRequest):
        invalid_req = request_object.InvalidRequestObject()
        if not login_payload:
            invalid_req.add_error("login_payload", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return LoginStudentRequestObject(login_payload=login_payload)


class LoginStudentUseCase(use_case.UseCase):
    def __init__(
        self,
        student_repository: StudentRepository = Depends(StudentRepository),
    ):
        self.student_repository = student_repository

    def process_request(self, req_object: LoginStudentRequestObject):
        student: StudentModel = self.student_repository.get_by_email(req_object.login_payload.email)
        checker = False
        if student:
            checker = verify_password(req_object.login_payload.password, student.password)
        if not student or not checker:
            return response_object.ResponseFailure.build_parameters_error(message="Sai email hoặc mật khẩu")

        student_in_db = StudentInDB.model_validate(student)
        if student_in_db.disabled():
            return response_object.ResponseFailure.build_parameters_error(message="Tài khoản của bạn đã bị khóa")

        access_token = create_access_token(data=TokenData(email=student.email, id=str(student.id)))
        return AuthStudentInfoInResponse(access_token=access_token, user=Student(**student_in_db.model_dump()))
