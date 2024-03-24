from datetime import timedelta, datetime
from random import sample, choice
from string import ascii_letters, digits, ascii_uppercase, ascii_lowercase
from typing import Optional

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.domain.admin.entity import AdminInDB
from app.domain.auth.entity import TokenData
from app.domain.shared.enum import AdminRole
from app.infra.admin.admin_repository import AdminRepository
from app.models.admin import AdminModel
from app.shared.common_exception import forbidden_exception

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/admin/auth/login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Không thể xác thực thông tin đăng nhập",
    headers={"WWW-Authenticate": "Bearer"},
)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def verify_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, id=payload.get("id"))
        return token_data
    except JWTError:
        raise credentials_exception


def get_password_hash(password):
    return pwd_context.hash(password)


def _get_current_admin(
        token: str = Depends(oauth2_scheme),
        admin_repository: AdminRepository = Depends(AdminRepository),
) -> AdminModel:
    token_data = verify_token(token=token)
    admin: AdminModel = admin_repository.get_by_email(email=token_data.email)
    if admin is None:
        raise credentials_exception
    return admin


def get_current_active_admin(
        admin: AdminModel = Depends(_get_current_admin),
) -> AdminModel:
    current_user = AdminInDB.model_validate(admin)
    if current_user.disabled():
        raise HTTPException(
            status_code=400, detail="Tài khoản của bạn đã bị khóa"
        )
    return admin


def create_access_token(data: TokenData, expires_delta: timedelta = None) -> str:
    to_encode = data.model_dump()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    if isinstance(encoded_jwt, str):
        return encoded_jwt
    else:
        return encoded_jwt.decode("utf-8")


def authorization(admin: AdminModel, roles: list[AdminRole]):
    """_summary_

    Args:
        admin (AdminInDB): current user from token
        roles (list[AdminRole]): accept roles

    Raises:
        forbidden_exception: _description_
    """
    if not any(role in admin.roles for role in roles):
        raise forbidden_exception


def generate_random_password(length: int = 20) -> str:
    """_summary_

    Args:
        length (int, optional): length password defaults to 20.

    Returns:
        password: str
    """
    punctuation = "!@#$%^&*"
    alphabet = ascii_letters + digits + punctuation
    requirements = [
        ascii_uppercase,  # at least one uppercase letter
        ascii_lowercase,  # at least one lowercase letter
        digits,  # at least one digit
        punctuation,  # at least one symbol
        *(length - 4) * [alphabet],
    ]  # rest: letters digits and symbols
    return "".join(choice(req) for req in sample(requirements, length))
