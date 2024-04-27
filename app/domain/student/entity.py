from datetime import datetime, date, timezone
from typing import Optional, List
from pydantic import ConfigDict, EmailStr, field_validator

from app.domain.shared.enum import AccountStatus
from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin, Pagination
from app.domain.student.enum import SexEnum
from app.shared.utils.general import convert_valid_date, get_current_season_value, transform_email


class StudentBase(BaseEntity):
    numerical_order: int
    group: int
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
    current_season: int
    password: str

    _convert_valid_date = field_validator("date_of_birth", mode="before")(convert_valid_date)

    def disabled(self):
        """
        Check user validity
        :return:
        """
        return self.status is AccountStatus.INACTIVE or self.status is AccountStatus.DELETED

    def active(self):
        """_summary_
        active when not disabled and is current season

        Returns:
            _type_: bool
        """
        return not self.disabled() and self.current_season == get_current_season_value()


class StudentInCreate(StudentBase):
    _extract_email = field_validator("email", mode="before")(transform_email)
    _convert_valid_date = field_validator("date_of_birth", mode="before")(convert_valid_date)


class Student(StudentBase, DateTimeModelMixin):
    """
    Student domain entity
    """

    id: str
    status: AccountStatus = AccountStatus.ACTIVE
    current_season: int


class ManyStudentsInResponse(BaseEntity):
    pagination: Optional[Pagination] = None
    data: Optional[List[Student]] = None


class StudentInUpdate(BaseEntity):
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
    status: Optional[AccountStatus] = None
    _extract_email = field_validator("email", mode="before")(transform_email)
    _convert_valid_date = field_validator("date_of_birth", mode="before")(convert_valid_date)


class StudentInUpdateTime(StudentInUpdate):
    updated_at: datetime = datetime.now(timezone.utc)


class ImportSpreadsheetsPayload(BaseEntity):
    url: str
    sheet_name: str | None = "main"


class ImportSpreadsheetsInResponse(BaseEntity):
    inserted_ids: list[str]
    errors: list


class ResetPasswordResponse(BaseEntity):
    email: str
    password: str
