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

    # 📎 Attach file
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(file_path)

        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="octet-stream",
            filename=file_name
        )

    except Exception as e:
        logger.error(f"Attachment failed: {str(e)}")
        raise

    # 📧 SMTP Config
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    username = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    try:
        logger.info(f"📧 Connecting to SMTP: {smtp_server}:{smtp_port}")

        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(msg)

        logger.info("📧 Email sent successfully")

    except Exception as e:
        logger.error(f"❌ Email failed: {str(e)}")
        raise