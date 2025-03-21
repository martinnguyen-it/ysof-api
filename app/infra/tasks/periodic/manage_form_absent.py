from datetime import datetime, timedelta, timezone

from app.domain.celery_result.enum import CeleryResultTag
from app.domain.manage_form.entity import ManageFormInDB, ManageFormUpdateWithTime
from app.domain.manage_form.enum import FormStatus, FormType
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.infra.subject.subject_repository import SubjectRepository
from app.models.manage_form import ManageFormModel
from app.models.subject import SubjectModel
from celery_config import celery_app_with_error_handler
from celery_config.celery_worker import logger


@celery_app_with_error_handler(CeleryResultTag.MANAGE_FORM_PERIODIC)
def open_form_absent_task():
    logger.info("[open_form_absent_task] running...")
    today = datetime.now()
    subject_repository = SubjectRepository()
    manage_form_repository = ManageFormRepository()

    subject: SubjectModel | None = subject_repository.find_one(
        {"start_at": {"$gt": today, "$lt": today + timedelta(days=7)}}
    )
    if subject:
        form = manage_form_repository.find_one({"type": FormType.SUBJECT_ABSENT})
        if form:
            manage_form_repository.update(
                id=form.id,
                data=ManageFormUpdateWithTime(
                    data={"subject_id": str(subject.id)},
                    status=FormStatus.ACTIVE,
                    type=FormType.SUBJECT_ABSENT,
                ),
            )
        else:
            manage_form_repository.create(
                ManageFormInDB(
                    data={"subject_id": str(subject.id)},
                    status=FormStatus.ACTIVE,
                    type=FormType.SUBJECT_ABSENT,
                )
            )


@celery_app_with_error_handler(CeleryResultTag.MANAGE_FORM_PERIODIC)
def close_form_absent_task():
    logger.info("[close_form_absent_task] running...")
    manage_form_repository = ManageFormRepository()
    form: ManageFormModel | None = manage_form_repository.find_one(
        {"type": FormType.SUBJECT_ABSENT}
    )
    if form and form.status == FormStatus.ACTIVE:
        manage_form_repository.update(
            id=form.id,
            data={"status": FormStatus.CLOSED, "updated_at": datetime.now(timezone.utc)},
        )
