import smtplib
import os
from email.message import EmailMessage
from utils.logger import logger

def send_email(to_email: str, subject: str, body: str, file_path: str):

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = to_email
    msg.set_content(body)

    # Attach file
    with open(file_path, "rb") as f:
        file_data = f.read()
        file_name = file_path.split("/")[-1]

    msg.add_attachment(
        file_data,
        maintype="application",
        subtype="octet-stream",
        filename=file_name
    )

    try:
        with smtplib.SMTP(...) as smtp:
            smtp.starttls()
            smtp.login(...)
            smtp.send_message(msg)

        logger.info("Email sent successfully")

    except Exception as e:
        logger.error(f"Email failed: {str(e)}")