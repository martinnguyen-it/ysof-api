from datetime import datetime, timezone
from pydantic import ConfigDict

from app.domain.shared.entity import BaseEntity, IDModelMixin, DateTimeModelMixin


class SeasonBase(BaseEntity):
    title: str
    season: int
    description: str | None = None
    academic_year: str | None = None


class SeasonInDB(IDModelMixin, DateTimeModelMixin, SeasonBase):
    is_current: bool = False
    # https://docs.pydantic.dev/2.4/concepts/models/#arbitrary-class-instances
    model_config = ConfigDict(from_attributes=True)


class SeasonInCreate(SeasonBase):
    pass


class Season(SeasonBase, DateTimeModelMixin):
    id: str
    is_current: bool


class SeasonInUpdate(BaseEntity):
    title: str | None = None
    description: str | None = None
    academic_year: str | None = None


class SeasonInUpdateTime(SeasonInUpdate):
    updated_at: datetime = datetime.now(timezone.utc)
    is_current: bool | None = None
