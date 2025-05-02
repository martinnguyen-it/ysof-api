from datetime import timedelta

from bson import ObjectId
from celery import group

from app.config import settings
from app.domain.celery_result.enum import CeleryResultTag
from app.infra.admin.admin_repository import AdminRepository
from app.infra.email.brevo_service import BrevoService
from app.infra.email.email_smtp_service import EmailSMTPService
from app.infra.subject.subject_registration_repository import SubjectRegistrationRepository
from app.infra.subject.subject_repository import SubjectRepository
from app.models.admin import AdminModel
from app.models.student import StudentModel
from app.models.subject_registration import SubjectRegistrationModel
from app.shared.utils.general import get_current_season_value
from celery_config import celery_app_with_error_handler
from celery_config.celery_worker import logger
from static.email.email_template import EMAIL_TEMPLATE
from static.email.entity import Template, TemplateContent

email_smtp_service = EmailSMTPService()
brevo_service = BrevoService()


@celery_app_with_error_handler(CeleryResultTag.SEND_MAIL)
def send_email_welcome_task(email: str, password: str, full_name: str, is_admin: bool = False):
    plain_text = EMAIL_TEMPLATE[Template.WELCOME][TemplateContent.PLAIN_TEXT]
    plain_text = plain_text.replace("{{full_name}}", full_name)
    plain_text = plain_text.replace("{{password}}", password)
    plain_text = plain_text.replace("{{email}}", email)
    plain_text = plain_text.replace(
        "{{url}}", settings.FE_ADMIN_BASE_URL if is_admin else settings.FE_STUDENT_BASE_URL
    )
    email_smtp_service.send_email_welcome(email=email, plain_text=plain_text)


@celery_app_with_error_handler(CeleryResultTag.SEND_MAIL)
def send_email_welcome_with_exist_account_task(
    email: str, season: int, full_name: str, is_admin: bool = False
):
    plain_text = EMAIL_TEMPLATE[Template.WELCOME_WITH_EXIST_ACCOUNT][TemplateContent.PLAIN_TEXT]
    plain_text = plain_text.replace("{{full_name}}", full_name)
    plain_text = plain_text.replace("{{season}}", season)
    plain_text = plain_text.replace("{{email}}", email)
    plain_text = plain_text.replace(
        "{{url}}", settings.FE_ADMIN_BASE_URL if is_admin else settings.FE_STUDENT_BASE_URL
    )
    email_smtp_service.send_email_welcome(email=email, plain_text=plain_text)


@celery_app_with_error_handler(CeleryResultTag.SEND_MAIL)
def send_email_notification_subject_task(subject_id: str):
    admin_repository = AdminRepository()
    subject_repository = SubjectRepository()
    subject_registration_repository = SubjectRegistrationRepository()

    current_season = get_current_season_value()
    admins: list[AdminModel] = admin_repository.list(
        match_pipeline={"latest_season": current_season}
    )
    emails_admin = [admin.email for admin in admins]

    subject = subject_repository.get_by_id(subject_id)
    if not subject:
        raise Exception("Not found subject")

    lecturer = (
        (subject.lecturer.title + " " if subject.lecturer.title else "")
        + (subject.lecturer.holy_name + " " if subject.lecturer.holy_name else "")
        + (subject.lecturer.full_name)
    )

    documents: list[str] = []
    for attachment in subject.attachments:
        if attachment.mimeType == "application/vnd.google-apps.spreadsheet":
            documents.append(f"https://docs.google.com/spreadsheets/d/{attachment.file_id}")
        elif attachment.mimeType in [
            "application/vnd.google-apps.document",
            "application/vnd.google-apps.kix",
        ]:
            documents.append(f"https://docs.google.com/document/d/{attachment.file_id}")
        else:
            documents.append(
                f"https://drive.google.com/file/d/{attachment.file_id}/view?usp=drivesdk"
            )
    documents.extend(subject.documents_url)

    params = dict(
        code=subject.code,
        start_at=subject.start_at.strftime("%d.%m.%Y"),
        subdivision=subject.subdivision,
        title=subject.title,
        lecturer=lecturer,
        link=subject.zoom.link,
        meeting_id=subject.zoom.meeting_id,
        pass_code=subject.zoom.pass_code,
        question_url=subject.question_url,
        absent=settings.FE_STUDENT_BASE_URL + "/xin-nghi-phep",
        documents="\n".join(documents) if len(documents) > 0 else None,
    )
    docs: list[StudentModel] = subject_registration_repository.get_by_subject_id(
        subject_id=ObjectId(subject_id)
    )
    emails_to: list[str] = [doc.email for doc in docs]
    emails_to.extend(emails_admin)

    job = group(
        [send_email_notification_subject_to_user_task.s(email, params) for email in emails_to]
    )
    job.apply_async()


@celery_app_with_error_handler(CeleryResultTag.SEND_MAIL)
def send_email_notification_subject_to_user_task(email: str, params: dict):
    brevo_service.send_student_notification_subject(email_to=email, params=params)


@celery_app_with_error_handler(CeleryResultTag.SEND_MAIL)
def send_student_evaluation_subject_task(subject_id: str):
    logger.info(f"[send_student_evaluation_subject_task subject_id:{subject_id}] running...")
    admin_repository = AdminRepository()
    subject_repository = SubjectRepository()
    subject_registration_repository = SubjectRegistrationRepository()

    current_season = get_current_season_value()
    admins: list[AdminModel] = admin_repository.list(
        match_pipeline={"latest_season": current_season}
    )
    emails_admin = [admin.email for admin in admins]

    subject = subject_repository.get_by_id(subject_id)
    if not subject:
        raise Exception("Not found subject")

    lecturer = (
        (subject.lecturer.title + " " if subject.lecturer.title else "")
        + (subject.lecturer.holy_name + " " if subject.lecturer.holy_name else "")
        + (subject.lecturer.full_name)
    )

    params = dict(
        code=subject.code,
        end_at=(subject.start_at + timedelta(days=7)).strftime("%d.%m.%Y"),
        title=subject.title,
        lecturer=lecturer,
        url=settings.FE_STUDENT_BASE_URL + "/luong-gia",
    )
    docs: list[SubjectRegistrationModel] = subject_registration_repository.get_by_subject_id(
        subject_id=ObjectId(subject_id)
    )
    emails_to: list[str] = [doc.student.email for doc in docs]
    emails_to.extend(emails_admin)

    job = group(
        [send_student_evaluation_subject_to_user_task.s(email, params) for email in emails_to]
    )
    job.apply_async()


@celery_app_with_error_handler(CeleryResultTag.SEND_MAIL)
def send_student_evaluation_subject_to_user_task(email: str, params: dict):
    brevo_service.send_student_evaluation_subject(email_to=email, params=params)
