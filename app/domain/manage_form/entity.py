from app.domain.shared.entity import BaseEntity, DateTimeModelMixin, IDModelMixin
from app.domain.manage_form.enum import FormStatus, FormType
from datetime import datetime, timezone
from pydantic import ConfigDict


class ManageFormBase(BaseEntity):
    status: FormStatus = FormStatus.INACTIVE
    type: FormType
    data: dict | None = None


class ManageFormInDB(IDModelMixin, DateTimeModelMixin, ManageFormBase):
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class ManageFormUpdateWithTime(ManageFormBase):
    updated_at: datetime = datetime.now(timezone.utc)


class CommonResponse(BaseEntity):
    type: FormType | None = None
    status: FormStatus = FormStatus.INACTIVE
    data: dict | None = None
    model_config = ConfigDict(from_attributes=True)


class ManageFormSubjectData(BaseEntity):
    subject_id: str


class ManageFormEvaluationOrAbsentInPayload(BaseEntity):
    """_summary_

    Args:
        data (str): ID subject
    """

    type: FormType
    status: FormStatus = FormStatus.INACTIVE
    data: ManageFormSubjectData


class ManageFormEvaluationOrAbsent(ManageFormEvaluationOrAbsentInPayload):
    model_config = ConfigDict(from_attributes=True)
