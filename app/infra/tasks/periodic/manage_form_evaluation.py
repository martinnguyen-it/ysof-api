from celery_worker import celery_app, logger
from app.infra.subject.subject_repository import SubjectRepository
from datetime import datetime, timezone
from app.models.subject import SubjectModel
from app.infra.manage_form.manage_form_repository import ManageFormRepository
from app.domain.manage_form.enum import FormStatus, FormType
from app.models.manage_form import ManageFormModel
from app.domain.subject.enum import StatusSubjectEnum
from app.shared.utils.general import get_current_season_value


@celery_app.task
def close_form_evaluation_task():
    logger.info("[close_form_evaluation_task] running...")
    try:
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
    except Exception as ex:
        logger.exception(ex)
