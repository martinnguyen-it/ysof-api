from app.domain.shared.entity import BaseEntity, DateTimeModelMixin, IDModelMixin
from app.domain.manage_form.enum import FormStatus, FormType
from datetime import datetime, timezone
from pydantic import ConfigDict


class SubjectRegistrationUpdate(BaseEntity):
    status: FormStatus


class CommonUpdate(BaseEntity):
    status: FormStatus = FormStatus.INACTIVE
    type: FormType
    data: dict | None = None


class CommonGet(BaseEntity):
    type: FormType


class ManageFormInDB(IDModelMixin, DateTimeModelMixin, CommonUpdate):
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class FormUpdateWithTime(CommonUpdate):
    updated_at: datetime = datetime.now(timezone.utc)


class CommonResponse(BaseEntity):
    status: FormStatus = FormStatus.INACTIVE
    model_config = ConfigDict(from_attributes=True)
