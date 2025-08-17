import random
import string
from datetime import timedelta
from app.infra.security.security_service import create_access_token
from app.domain.auth.entity import TokenData


def generate_otp(length: int = 6) -> str:
    """Generate OTP with default length of 6 characters"""
    return "".join(random.choices(string.digits, k=length))


def generate_reset_token(email: str, user_type: str) -> str:
    """Generate reset token for reset password"""
    # Create token with 10 minutes expiration
    expires_delta = timedelta(minutes=10)
    token_data = TokenData(email=email, id=user_type)
    return create_access_token(data=token_data, expires_delta=expires_delta)


def verify_reset_token(token: str) -> TokenData:
    """Verify reset token and return TokenData"""
    from app.infra.security.security_service import verify_token

    return verify_token(token)
