from fastapi import Depends
from app.domain.auth.entity import VerifyOTP, VerifyOTPResponse
from app.infra.admin.admin_repository import AdminRepository
from app.infra.reset_otp.reset_otp_repository import ResetOTPRepository
from app.shared import request_object, use_case, response_object
from app.shared.utils.otp_utils import generate_reset_token


class VerifyOTPRequestObject(request_object.ValidRequestObject):
    def __init__(self, payload: VerifyOTP):
        self.payload = payload

    @classmethod
    def builder(cls, payload: VerifyOTP):
        invalid_req = request_object.InvalidRequestObject()
        if not payload:
            invalid_req.add_error("payload", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return VerifyOTPRequestObject(payload=payload)


class VerifyOTPUseCase(use_case.UseCase):
    def __init__(
        self,
        admin_repository: AdminRepository = Depends(AdminRepository),
        reset_otp_repository: ResetOTPRepository = Depends(ResetOTPRepository),
    ):
        self.admin_repository = admin_repository
        self.reset_otp_repository = reset_otp_repository

    def process_request(self, req_object: VerifyOTPRequestObject):
        admin = self.admin_repository.get_by_email(req_object.payload.email)
        if not admin:
            return response_object.ResponseFailure.build_parameters_error(
                message="Email không tồn tại trong hệ thống"
            )

        # Get OTP from database
        reset_otp = self.reset_otp_repository.get_by_email_and_type(
            req_object.payload.email, "admin"
        )

        if not reset_otp:
            return response_object.ResponseFailure.build_parameters_error(
                message="Không tìm thấy mã OTP. Vui lòng yêu cầu lại"
            )

        if reset_otp.is_expired():
            return response_object.ResponseFailure.build_parameters_error(
                message="Mã OTP đã hết hạn. Vui lòng yêu cầu lại"
            )

        if reset_otp.is_used == 1:
            return response_object.ResponseFailure.build_parameters_error(
                message="Mã OTP đã được sử dụng"
            )

        if reset_otp.otp != req_object.payload.otp:
            return response_object.ResponseFailure.build_parameters_error(
                message="Mã OTP không đúng"
            )

        # Mark OTP as used
        self.reset_otp_repository.mark_as_used(req_object.payload.email, "admin")

        # Generate reset token
        reset_token = generate_reset_token(req_object.payload.email, "admin")

        return VerifyOTPResponse(reset_token=reset_token)
