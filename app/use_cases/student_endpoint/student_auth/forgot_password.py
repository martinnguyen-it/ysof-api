from fastapi import Depends
from app.domain.auth.entity import ForgotPassword, ForgotPasswordResponse
from app.infra.student.student_repository import StudentRepository
from app.infra.reset_otp.reset_otp_repository import ResetOTPRepository
from app.shared import request_object, use_case, response_object
from app.shared.utils.otp_utils import generate_otp
from app.infra.tasks.email import send_email_forgot_password_otp_task


class ForgotPasswordStudentRequestObject(request_object.ValidRequestObject):
    def __init__(self, payload: ForgotPassword):
        self.payload = payload

    @classmethod
    def builder(cls, payload: ForgotPassword):
        invalid_req = request_object.InvalidRequestObject()
        if not payload:
            invalid_req.add_error("payload", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return ForgotPasswordStudentRequestObject(payload=payload)


class ForgotPasswordStudentUseCase(use_case.UseCase):
    def __init__(
        self,
        student_repository: StudentRepository = Depends(StudentRepository),
        reset_otp_repository: ResetOTPRepository = Depends(ResetOTPRepository),
    ):
        self.student_repository = student_repository
        self.reset_otp_repository = reset_otp_repository

    def process_request(self, req_object: ForgotPasswordStudentRequestObject):
        student = self.student_repository.get_by_email(req_object.payload.email)
        if not student:
            return response_object.ResponseFailure.build_parameters_error(
                message="Email không tồn tại trong hệ thống"
            )

        if student.status != "active":
            return response_object.ResponseFailure.build_parameters_error(
                message="Tài khoản của bạn đã bị khóa"
            )

        # Generate OTP
        otp = generate_otp()

        # Save OTP to database
        self.reset_otp_repository.create_otp(
            email=req_object.payload.email, otp=otp, user_type="student"
        )

        # Send email OTP
        send_email_forgot_password_otp_task.delay(
            email=req_object.payload.email, otp=otp, full_name=student.full_name, is_admin=False
        )

        return ForgotPasswordResponse(message="Mã OTP đã được gửi đến email của bạn")
