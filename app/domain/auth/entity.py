from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

from app.domain.admin.entity import Admin
from app.domain.shared.entity import BaseEntity
from app.domain.student.entity import Student
from app.shared.utils.general import transform_email


class Token(BaseModel):
    access_token: Optional[str] = None


class TokenData(BaseModel):
    email: str
    id: str = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    _extract_email = field_validator("email", mode="before")(transform_email)


class AuthAdminInfoInResponse(BaseEntity, Token):
    user: Admin


class AuthStudentInfoInResponse(BaseEntity, Token):
    user: Student


class UpdatePassword(BaseEntity):
    old_password: str
    new_password: str


class ForgotPassword(BaseEntity):
    email: str
