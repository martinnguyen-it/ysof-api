from fastapi import Depends
from app.domain.auth.entity import ForgotPassword, ForgotPasswordResponse
from app.infra.admin.admin_repository import AdminRepository
from app.infra.reset_otp.reset_otp_repository import ResetOTPRepository
from app.shared import request_object, use_case, response_object
from app.shared.utils.otp_utils import generate_otp
from app.infra.tasks.email import send_email_forgot_password_otp_task


class ForgotPasswordRequestObject(request_object.ValidRequestObject):
    def __init__(self, payload: ForgotPassword):
        self.payload = payload

    @classmethod
    def builder(cls, payload: ForgotPassword):
        invalid_req = request_object.InvalidRequestObject()
        if not payload:
            invalid_req.add_error("payload", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return ForgotPasswordRequestObject(payload=payload)


class ForgotPasswordUseCase(use_case.UseCase):
    def __init__(
        self,
        admin_repository: AdminRepository = Depends(AdminRepository),
        reset_otp_repository: ResetOTPRepository = Depends(ResetOTPRepository),
    ):
        self.admin_repository = admin_repository
        self.reset_otp_repository = reset_otp_repository

    def process_request(self, req_object: ForgotPasswordRequestObject):
        admin = self.admin_repository.get_by_email(req_object.payload.email)
        if not admin:
            return response_object.ResponseFailure.build_parameters_error(
                message="Email không tồn tại trong hệ thống"
            )

        if admin.status != "active":
            return response_object.ResponseFailure.build_parameters_error(
                message="Tài khoản của bạn đã bị khóa"
            )

        # Generate OTP
        otp = generate_otp()

        # Save OTP to database
        self.reset_otp_repository.create_otp(
            email=req_object.payload.email, otp=otp, user_type="admin"
        )

        # Send email OTP
        send_email_forgot_password_otp_task.delay(
            email=req_object.payload.email, otp=otp, full_name=admin.full_name, is_admin=True
        )

        return ForgotPasswordResponse(message="Mã OTP đã được gửi đến email của bạn")
