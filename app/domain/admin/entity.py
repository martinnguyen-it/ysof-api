from datetime import datetime
from typing import Optional, List
from pydantic import ConfigDict, EmailStr, field_validator

from app.domain.shared.enum import AdminRole, AccountStatus
from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin, Pagination
from app.infra.season.season_repository import SeasonRepository


def transform_email(email: str | None = None) -> str | None:
    return email.lower().strip() if email else email


class Address(BaseEntity):
    current: Optional[str] = None
    original: Optional[str] = None
    diocese: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


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
    current_season: int | None = None
    seasons: list[int] | None = None
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
                )

    def active(self):
        """_summary_
        active when not disabled and is current season

        Returns:
            _type_: bool
        """
        return AdminRole.ADMIN in self.roles or \
            ((not self.disabled()) and self.current_season ==
             SeasonRepository().get_current_season().season)


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


class AdminInUpdateMe(BaseEntity):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    holy_name: Optional[str] = None
    phone_number: Optional[list[str]] = None
    address: Optional[Address] = None
    date_of_birth: Optional[datetime] = None
    facebook: Optional[str] = None
    status: Optional[AccountStatus] = None
    _extract_email = field_validator("email", mode="before")(transform_email)


class AdminInUpdate(AdminInUpdateMe):
    roles: Optional[list[AdminRole]] = None


class AdminInUpdateTime(BaseEntity):
    updated_at: datetime = datetime.now()
