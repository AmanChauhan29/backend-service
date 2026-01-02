import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from utils.logger import get_logger
from settings.config import settings

logger = get_logger("Email_Service")

SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
SMTP_USER = settings.SMTP_USER
SMTP_PASSWORD = settings.SMTP_PASSWORD
FROM_EMAIL = settings.FROM_EMAIL

def send_verification_email(to_email: str, verify_link: str):
    """
    Sends verification email
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = "Verify your email"

        body = f"""
        Hi,

        Please verify your email by clicking the link below:

        {verify_link}

        This link will expire in 15 minutes.

        If you did not sign up, ignore this email.
        """

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        server.quit()

        logger.info("Verification email sent", extra={"email": to_email})

    except Exception as e:
        logger.error("Failed to send verification email", exc_info=e)
