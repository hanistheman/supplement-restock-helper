"""
Email sending via plain SMTP — works with any provider (Gmail app
password, a transactional provider's SMTP relay, Mailtrap for testing)
without locking the project into a specific vendor's API/SDK.

If SMTP isn't configured (no SMTP_HOST in the environment), emails are
printed to the console instead of sent. This means local development and
tests never need real credentials to exercise the notification flow.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@supplement-tracker.local")


def send_email(to_email: str, subject: str, body: str) -> None:
    """
    Sends a plain-text email. Falls back to printing the message to the
    console when SMTP_HOST isn't set, so this is always safe to call in
    dev/test environments.
    """
    if not SMTP_HOST:
        print(f"[email:console-fallback] To: {to_email} | Subject: {subject}\n{body}\n")
        return

    message = MIMEMultipart()
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, to_email, message.as_string())