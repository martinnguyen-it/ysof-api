from datetime import datetime
from typing import Optional, List
from pydantic import ConfigDict, EmailStr, field_validator, BaseModel

from app.config import settings
from app.domain.shared.enum import AdminRole, AccountStatus
from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin, Pagination


def transform_email(email: str) -> str:
    return email.lower().strip()


class Address(BaseModel):
    current: Optional[str] = None
    original: Optional[str] = None
    diocese: Optional[str] = None


class AdminBase(BaseEntity):
    email: EmailStr
    status: AccountStatus = AccountStatus.ACTIVE
    roles: list[AdminRole]
    full_name: str
    holy_name: str
    phone_number: Optional[list[str]] = None
    address: Optional[Address] = None
    date_of_birth: Optional[datetime] = None
    facebook: Optional[str] = None
    current_season: int
    seasons: list[int]
    avatar: Optional[str] = None


class AdminInDB(IDModelMixin, DateTimeModelMixin, AdminBase):
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)

    password: Optional[str] = None

    def disabled(self):
        """
        Check user validity
        :return:
        """
        return (self.status is AccountStatus.INACTIVE
                or self.status is AccountStatus.DELETED
                or self.current_season != settings.CURRENT_SEASON)


class AdminInCreate(BaseEntity):
    email: EmailStr
    roles: list[AdminRole]
    full_name: str
    holy_name: str
    phone_number: Optional[list[str]] = None
    address: Optional[Address] = None
    date_of_birth: Optional[datetime] = None
    facebook: Optional[str] = None
    _extract_email = field_validator("email", mode="before")(transform_email)


class Admin(AdminBase):
    """
    Admin domain entity
    """
    id: str
    created_at: datetime
    updated_at: datetime


class ManyAdminsInResponse(BaseEntity):
    pagination: Optional[Pagination] = None
    data: Optional[List[Admin]] = None


class AdminInUpdate(BaseEntity):
    email: Optional[EmailStr] = None
    roles: Optional[list[AdminRole]] = None
    full_name: Optional[str] = None
    holy_name: Optional[str] = None
    phone_number: Optional[list[str]] = None
    address: Optional[Address] = None
    date_of_birth: Optional[datetime] = None
    facebook: Optional[str] = None
    status: Optional[AccountStatus] = None
    _extract_email = field_validator("email", mode="before")(transform_email)


class AdminInUpdateTime(BaseEntity):
    updated_at: datetime = datetime.now()
