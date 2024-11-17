from celery_worker import celery_app, logger
from app.infra.subject.subject_repository import SubjectRepository
from datetime import datetime, timedelta, timezone
from app.models.subject import SubjectModel
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.domain.manage_form.enum import FormStatus, FormType
from app.domain.manage_form.entity import ManageFormInDB, ManageFormUpdateWithTime
from app.models.manage_form import ManageFormModel


@celery_app.task
def open_form_absent_task():
    logger.info("[open_form_absent_task] running...")
    today = datetime.now()
    try:
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

    except Exception as ex:
        logger.exception(ex)


@celery_app.task
def close_form_absent_task():
    logger.info("[close_form_absent_task] running...")
    try:
        manage_form_repository = ManageFormRepository()
        form: ManageFormModel | None = manage_form_repository.find_one(
            {"type": FormType.SUBJECT_ABSENT}
        )
        if form and form.status == FormStatus.ACTIVE:
            manage_form_repository.update(
                id=form.id,
                data={"status": FormStatus.CLOSED, "updated_at": datetime.now(timezone.utc)},
            )
    except Exception as ex:
        logger.exception(ex)
