from app.config import settings
from celery_worker import celery_app
from static.email.email_template import EMAIL_TEMPLATE
from static.email.entity import Template, TemplateContent
from app.infra.email.email_smtp_service import EmailSMTPService

email_smtp_service = EmailSMTPService()


@celery_app.task
def send_email_welcome_task(email: str, password: str, full_name: str, is_admin: bool = False):
    plain_text = EMAIL_TEMPLATE[Template.WELCOME][TemplateContent.PLAIN_TEXT]
    plain_text = plain_text.replace("{{full_name}}", full_name)
    plain_text = plain_text.replace("{{password}}", password)
    plain_text = plain_text.replace("{{email}}", email)
    plain_text = plain_text.replace("{{url}}", settings.FE_ADMIN_BASE_URL if is_admin else settings.FE_STUDENT_BASE_URL)

    email_smtp_service.send_email_welcome(email=email, plain_text=plain_text)
