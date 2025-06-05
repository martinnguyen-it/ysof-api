from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid, formataddr
import pytz
from app.config import settings
from app.infra.logging import get_logger
import ssl

logger = get_logger()


class EmailSMTPService:
    def _send(
        self, emails_to: list[str] | str, subject: str, plain_text: str, html: str | None = None
    ):
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr(("YSOF", settings.YSOF_EMAIL))
        msg["To"] = emails_to if isinstance(emails_to, str) else ", ".join(emails_to)
        msg["Subject"] = subject
        msg["Message-ID"] = make_msgid(domain=settings.SMTP_MAIL_HOST)
        current_time = datetime.now(pytz.timezone(settings.TIMEZONE))
        msg["Date"] = current_time.strftime("%a, %d %b %Y %H:%M:%S %z")
        msg["Reply-To"] = settings.YSOF_EMAIL
        msg["List-Unsubscribe"] = f"<mailto:{settings.YSOF_EMAIL}>"

        msg.attach(MIMEText(plain_text, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(host=settings.SMTP_MAIL_HOST, port=settings.SMTP_MAIL_PORT) as service:
            service.starttls(context=ssl.create_default_context())
            service.login(user=settings.SMTP_MAIL_USER, password=settings.SMTP_MAIL_PASSWORD)
            res = service.send_message(msg)
        return res

    def send_email_welcome(self, email: str, plain_text: str):
        self._send(emails_to=email, subject="YSOF - Tài khoản truy cập", plain_text=plain_text)
