from datetime import datetime

from app.domain.celery_result.enum import CeleryResultTag
from app.domain.shared.entity import BaseEntity, Pagination


class CeleryResultResponse(BaseEntity):
    task_id: str
    tag: CeleryResultTag
    name: str
    description: str | None = None
    traceback: str | None = None
    date_done: datetime

    resolved: bool | None = False
    updated_at: datetime | None = None


class ManyCeleryResultsInResponse(BaseEntity):
    pagination: Pagination
    data: list[CeleryResultResponse]
