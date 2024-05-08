from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pytz
from app.config import settings
from app.infra.logging import get_logger

logger = get_logger()


class EmailSMTPService:
    def _send(self, emails_to: list[str] | str, subject: str, plain_text: str, html: str | None = None):
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"YSOF <{settings.YSOF_EMAIL_SENDER}>"
            msg["To"] = emails_to
            msg["Subject"] = subject
            current_time = datetime.now(pytz.timezone(settings.CELERY_TIMEZONE))
            formatted_date = current_time.strftime("%a, %d %b %Y %H:%M:%S %z")

            msg["Date"] = formatted_date
            msg["reply-to"] = settings.YSOF_EMAIL_SENDER

            msg.attach(MIMEText(plain_text, "plain"))
            if html:
                msg.attach(MIMEText(html, "html"))

            service = smtplib.SMTP(host=settings.SMTP_MAIL_HOST, port=settings.SMTP_MAIL_PORT)
            service.starttls()
            service.login(user=settings.SMTP_MAIL_USER, password=settings.SMTP_MAIL_PASSWORD)

            res = service.send_message(msg)
            service.quit()
            return res
        except Exception as e:
            logger.exception(e)

    def send_email_welcome(self, email: str, plain_text: str):
        self._send(emails_to=email, subject="YSOF - Tài khoản truy cập", plain_text=plain_text)
