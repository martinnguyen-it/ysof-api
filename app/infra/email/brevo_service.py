import sib_api_v3_sdk
from typing import Optional, Dict, Any, List, Union
from pydantic import EmailStr
from app.config import settings


class BrevoService:
    def __init__(self):
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY

        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        self.contact = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))

    def _send(
        self,
        emails_to: Union[List[str], str],
        sender: Optional[EmailStr] = None,
        text_content: Optional[str] = None,
        template_id: Optional[int] = None,
        subject: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
    ):
        if not template_id and not subject:
            raise Exception("Must have template_id or sender either")

        if isinstance(emails_to, str):
            emails_to = [emails_to]

        if len(emails_to) == 0:
            raise Exception("Must have email to")
        email_sender = None
        # we can get sender from template id
        if not template_id:
            if sender:
                email_sender = sib_api_v3_sdk.SendSmtpEmailSender(email=sender, name=name)
            else:
                email_sender = sib_api_v3_sdk.SendSmtpEmailSender(
                    email=settings.YSOF_EMAIL, name=name
                )

        to = [sib_api_v3_sdk.SendSmtpEmailTo(email=to) for to in emails_to]
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            sender=email_sender,
            to=to,
            text_content=text_content,
            template_id=template_id,
            subject=subject,
            params=params,
            reply_to={"email": settings.YSOF_EMAIL},
        )
        api_response = self.api_instance.send_transac_email(send_smtp_email)
        return api_response

    def send_student_notification_subject(self, email_to: str, params: dict) -> Any:
        resp = self._send(
            emails_to=email_to,
            template_id=settings.STUDENT_NOTIFICATION_SUBJECT,
            params=params,
        )
        return resp

    def send_student_evaluation_subject(self, email_to: str, params: dict) -> Any:
        resp = self._send(
            emails_to=email_to,
            template_id=settings.STUDENT_SUBJECT_EVALUATION_TEMPLATE,
            params=params,
        )
        return resp

    def send_register_email(self, mail_to: EmailStr, password: str) -> Any:
        data = dict(password=password, url=settings.FE_ADMIN_BASE_URL)
        resp = self._send(
            emails_to=[mail_to],
            template_id=settings.STUDENT_REGISTER_EMAIL_TEMPLATE,
            params=data,
        )
        return resp

    def send_forgot_email(self, mail_to: EmailStr, password: str) -> Any:
        data = dict(password=password, url=settings.FE_ADMIN_BASE_URL)
        resp = self._send(
            emails_to=[mail_to],
            template_id=settings.STUDENT_FORGOT_PASSWORD_EMAIL_TEMPLATE,
            params=data,
        )
        return resp

    def send_welcome_email(
        self,
        email_to: str,
        data: dict,
    ) -> Any:
        resp = self._send(
            emails_to=[email_to],
            template_id=settings.STUDENT_WELCOME_EMAIL_TEMPLATE,
            params=data,
        )
        return resp
