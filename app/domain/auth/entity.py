from typing import Optional
from pydantic import BaseModel, EmailStr

from app.domain.admin.entity import Admin
from app.domain.shared.entity import BaseEntity
from app.domain.student.entity import Student


class Token(BaseModel):
    access_token: Optional[str] = None


class TokenData(BaseModel):
    email: str
    id: str = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthAdminInfoInResponse(BaseEntity, Token):
    user: Admin


class AuthStudentInfoInResponse(BaseEntity, Token):
    user: Student
