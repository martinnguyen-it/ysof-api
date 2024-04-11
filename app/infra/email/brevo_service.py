import sib_api_v3_sdk
from typing import Optional, Dict, Any, List, Union
from sib_api_v3_sdk.rest import ApiException
from pydantic import EmailStr
from app.config import settings

from app.infra.logging import get_logger

logger = get_logger()


class BrevoService:
    def __init__(self):
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY

        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
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
        try:
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
                    email_sender = sib_api_v3_sdk.SendSmtpEmailSender(email=settings.YSOF_EMAIL_SENDER, name=name)

            to = [sib_api_v3_sdk.SendSmtpEmailTo(email=to) for to in emails_to]
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                sender=email_sender,
                to=to,
                text_content=text_content,
                template_id=template_id,
                subject=subject,
                params=params,
                reply_to={"email": settings.YSOF_EMAIL_SENDER},
            )
            api_response = self.api_instance.send_transac_email(send_smtp_email)
            return api_response
        except ApiException as ex:
            raise ex

    def send_register_email(self, mail_to: EmailStr, password: str) -> Any:
        try:
            data = dict(password=password, url=settings.HOSTING_URL)
            resp = self._send(
                emails_to=[mail_to],
                template_id=settings.STUDENT_REGISTER_EMAIL_TEMPLATE,
                params=data,
            )
            return resp
        except Exception as ex:
            raise ex

    def send_forgot_email(self, mail_to: EmailStr, password: str) -> Any:
        try:
            data = dict(password=password, url=settings.HOSTING_URL)
            resp = self._send(
                emails_to=[mail_to],
                template_id=settings.STUDENT_FORGOT_PASSWORD_EMAIL_TEMPLATE,
                params=data,
            )
            return resp
        except Exception as ex:
            raise ex

    def send_welcome_email(
        self,
        email_to: str,
        data: dict,
    ) -> Any:
        try:
            resp = self._send(
                emails_to=[email_to],
                template_id=settings.STUDENT_WELCOME_EMAIL_TEMPLATE,
                params=data,
            )
            return resp
        except Exception as ex:
            logger.exception(ex)
            return None
