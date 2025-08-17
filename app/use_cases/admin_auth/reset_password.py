from fastapi import Depends
from app.domain.auth.entity import ResetPassword, ResetPasswordResponse
from app.infra.admin.admin_repository import AdminRepository
from app.infra.security.security_service import get_password_hash
from app.shared import request_object, use_case, response_object
from app.shared.utils.otp_utils import verify_reset_token
from app.infra.tasks.email import send_email_password_changed_task


class ResetPasswordRequestObject(request_object.ValidRequestObject):
    def __init__(self, payload: ResetPassword):
        self.payload = payload

    @classmethod
    def builder(cls, payload: ResetPassword):
        invalid_req = request_object.InvalidRequestObject()
        if not payload:
            invalid_req.add_error("payload", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return ResetPasswordRequestObject(payload=payload)


class ResetPasswordUseCase(use_case.UseCase):
    def __init__(
        self,
        admin_repository: AdminRepository = Depends(AdminRepository),
    ):
        self.admin_repository = admin_repository

    def process_request(self, req_object: ResetPasswordRequestObject):
        try:
            # Verify reset token
            token_data = verify_reset_token(req_object.payload.token)

            if token_data.id != "admin":
                return response_object.ResponseFailure.build_parameters_error(
                    message="Token không hợp lệ"
                )

            admin = self.admin_repository.get_by_email(token_data.email)
            if not admin:
                return response_object.ResponseFailure.build_parameters_error(
                    message="Email không tồn tại trong hệ thống"
                )

            # Update password
            admin.password = get_password_hash(req_object.payload.new_password)
            admin.save()

            # Send email notification password changed
            send_email_password_changed_task.delay(
                email=admin.email, full_name=admin.full_name, is_admin=True
            )

            return ResetPasswordResponse(message="Mật khẩu đã được thay đổi thành công")

        except Exception:
            return response_object.ResponseFailure.build_parameters_error(
                message="Token không hợp lệ hoặc đã hết hạn"
            )
