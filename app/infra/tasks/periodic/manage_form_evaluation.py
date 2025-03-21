from datetime import datetime, timezone

from app.domain.celery_result.enum import CeleryResultTag
from app.domain.manage_form.enum import FormStatus, FormType
from app.domain.subject.enum import StatusSubjectEnum
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.infra.subject.subject_repository import SubjectRepository
from app.models.manage_form import ManageFormModel
from app.models.subject import SubjectModel
from app.shared.utils.general import get_current_season_value
from celery_config import celery_app_with_error_handler
from celery_config.celery_worker import logger


@celery_app_with_error_handler(CeleryResultTag.MANAGE_FORM_PERIODIC)
def close_form_evaluation_task():
    logger.info("[close_form_evaluation_task] running...")

    manage_form_repository = ManageFormRepository()
    subject_repository = SubjectRepository()
    current_season = get_current_season_value()

    subjects: list[SubjectModel] | None = subject_repository.find(
        {"status": StatusSubjectEnum.SENT_EVALUATION, "season": current_season}
    )

    if isinstance(subjects, list) and len(subjects) > 0:
        subject_repository.bulk_update(
            data={
                "status": StatusSubjectEnum.CLOSE_EVALUATION,
                "updated_at": datetime.now(timezone.utc),
            },
            entities=subjects,
        )

    form: ManageFormModel | None = manage_form_repository.find_one(
        {"type": FormType.SUBJECT_EVALUATION}
    )
    if form and form.status == FormStatus.ACTIVE:
        manage_form_repository.update(
            id=form.id,
            data={"status": FormStatus.CLOSED, "updated_at": datetime.now(timezone.utc)},
        )
