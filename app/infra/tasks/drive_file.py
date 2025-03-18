from app.infra.services.google_drive_api import GoogleDriveAPIService
from celery_worker import celery_app
from app.infra.email.email_smtp_service import EmailSMTPService
from app.infra.email.brevo_service import BrevoService

email_smtp_service = EmailSMTPService()
brevo_service = BrevoService()
google_drive_api_service = GoogleDriveAPIService()


@celery_app.task
def delete_file_drive_task(file_id: str):
    google_drive_api_service.delete(file_id)
