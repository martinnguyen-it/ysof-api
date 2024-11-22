from datetime import date
from typing import Optional, List
from pydantic import ConfigDict, EmailStr, field_validator

from app.domain.shared.enum import AccountStatus
from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin, Pagination
from app.domain.student.enum import SexEnum
from app.shared.utils.general import (
    convert_valid_date,
    get_current_season_value,
    mask_email,
    mask_phone_number,
    transform_email,
    validate_name,
)


class StudentSeason(BaseEntity):
    model_config = ConfigDict(from_attributes=True)
    numerical_order: int
    group: int
    season: int


class StudentBase(BaseEntity):
    holy_name: str
    full_name: str
    email: EmailStr
    sex: Optional[SexEnum] = None
    date_of_birth: Optional[date] = None
    origin_address: Optional[str] = None
    diocese: Optional[str] = None
    phone_number: Optional[str] = None
    avatar: Optional[str] = None
    education: Optional[str] = None
    job: Optional[str] = None
    note: Optional[str] = None


class StudentInDB(IDModelMixin, DateTimeModelMixin, StudentBase):
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)
    status: AccountStatus = AccountStatus.ACTIVE
    seasons_info: list[StudentSeason]
    password: str

    _convert_valid_date = field_validator("date_of_birth", mode="before")(convert_valid_date)
    _convert_valid_name = field_validator("full_name", mode="before")(validate_name)

    def disabled(self):
        """
        Check user validity
        :return:
        """
        return self.status is AccountStatus.INACTIVE

    def active(self):
        """_summary_
        active when not disabled and is current season

        Returns:
            _type_: bool
        """
        return (
            not self.disabled()
            and len(self.seasons_info) > 0
            and self.seasons_info[-1].season == get_current_season_value()
        )


class StudentInCreate(StudentBase):
    numerical_order: int
    group: int

    _extract_email = field_validator("email", mode="before")(transform_email)
    _convert_valid_date = field_validator("date_of_birth", mode="before")(convert_valid_date)


class Student(StudentBase, DateTimeModelMixin):
    """
    Student domain entity
    """

    id: str
    status: AccountStatus = AccountStatus.ACTIVE
    seasons_info: list[StudentSeason]


class ManyStudentsInResponse(BaseEntity):
    pagination: Optional[Pagination] = None
    data: Optional[List[Student]] = None


class StudentInStudentRequestResponse(BaseEntity):
    seasons_info: list[StudentSeason]
    holy_name: str
    full_name: str
    email: EmailStr
    sex: Optional[SexEnum] = None
    diocese: Optional[str] = None
    phone_number: Optional[str] = None
    avatar: Optional[str] = None
    _mask_email = field_validator("email", mode="before")(mask_email)
    _mask_phone_number = field_validator("phone_number", mode="before")(mask_phone_number)


class ManyStudentsInStudentRequestResponse(BaseEntity):
    pagination: Optional[Pagination] = None
    data: Optional[List[StudentInStudentRequestResponse]] = None


class StudentInUpdate(BaseEntity):
    numerical_order: int | None = None
    group: Optional[int] = None
    holy_name: Optional[str] = None
    full_name: Optional[str] = None
    sex: Optional[SexEnum] = None
    date_of_birth: Optional[date] = None
    origin_address: Optional[str] = None
    diocese: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
    education: Optional[str] = None
    job: Optional[str] = None
    note: Optional[str] = None
    _extract_email = field_validator("email", mode="before")(transform_email)
    _convert_valid_date = field_validator("date_of_birth", mode="before")(convert_valid_date)


class ImportSpreadsheetsPayload(BaseEntity):
    url: str
    sheet_name: str | None = "main"


class ErrorImport(BaseEntity):
    row: int
    detail: str


class AttentionImport(ErrorImport):
    pass


class ImportSpreadsheetsInResponse(BaseEntity):
    updated: list[str]
    inserteds: list[str]
    errors: list[ErrorImport]
    attentions: list[AttentionImport]


class ResetPasswordResponse(BaseEntity):
    email: str
    password: str
