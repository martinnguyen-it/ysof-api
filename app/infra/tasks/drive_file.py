from app.domain.celery_result.enum import CeleryResultTag
from app.infra.email.brevo_service import BrevoService
from app.infra.email.email_smtp_service import EmailSMTPService
from app.infra.services.google_drive_api import GoogleDriveAPIService
from celery_config import celery_app_with_error_handler

email_smtp_service = EmailSMTPService()
brevo_service = BrevoService()
google_drive_api_service = GoogleDriveAPIService()


@celery_app_with_error_handler(CeleryResultTag.DRIVE_FILE)
def delete_file_drive_task(file_id: str):
    google_drive_api_service.delete(file_id)
