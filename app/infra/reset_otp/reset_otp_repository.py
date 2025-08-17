from datetime import datetime, timezone, timedelta
from typing import Optional
from app.models.reset_otp import ResetOTPModel


class ResetOTPRepository:
    def create_otp(
        self, email: str, otp: str, user_type: str, expires_in_minutes: int = 10
    ) -> ResetOTPModel:
        """Create new OTP for email"""
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

        # Delete old OTP if exists
        self.delete_by_email_and_type(email, user_type)

        reset_otp = ResetOTPModel(
            email=email, otp=otp, user_type=user_type, expires_at=expires_at, is_used=0
        )
        return reset_otp.save()

    def get_by_email_and_type(self, email: str, user_type: str) -> Optional[ResetOTPModel]:
        """Get OTP by email and user_type"""
        return ResetOTPModel.objects(email=email, user_type=user_type).first()

    def delete_by_email_and_type(self, email: str, user_type: str):
        """Delete OTP by email and user_type"""
        ResetOTPModel.objects(email=email, user_type=user_type).delete()

    def mark_as_used(self, email: str, user_type: str):
        """Mark OTP as used"""
        otp = self.get_by_email_and_type(email, user_type)
        if otp:
            otp.mark_as_used()

    def cleanup_expired_otps(self):
        """Delete expired OTPs"""
        ResetOTPModel.objects(expires_at__lt=datetime.now(timezone.utc)).delete()
