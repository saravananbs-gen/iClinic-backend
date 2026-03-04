import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.config.settings import settings

SMTP_SERVER = settings.SMTP_SERVER
SMTP_PORT = settings.SMTP_PORT
EMAIL_ADDRESS = settings.SMTP_EMAIL
EMAIL_PASSWORD = settings.SMTP_APP_PASSWORD


async def send_email(to_email: str, subject: str, body: str):

    message = MIMEMultipart()
    message["From"] = EMAIL_ADDRESS
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()

    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())
    server.quit()
