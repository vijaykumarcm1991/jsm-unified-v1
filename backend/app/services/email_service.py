import smtplib
import os
import time
from email.message import EmailMessage
from utils.logger import logger


def send_email(
    to_emails: list,
    subject: str,
    body: str,
    file_path: str,
    cc_emails: list = None
):

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = ", ".join(to_emails)

    if cc_emails:
        msg["Cc"] = ", ".join(cc_emails)

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
        logger.error(f"❌ Attachment failed: {str(e)}")
        raise

    # 📧 SMTP config
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    username = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    recipients = to_emails + (cc_emails if cc_emails else [])

    # 🔁 RETRY LOGIC
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"📧 Attempt {attempt}: Connecting to SMTP {smtp_server}:{smtp_port}")

            with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                smtp.starttls()
                smtp.login(username, password)
                smtp.send_message(msg, from_addr=username, to_addrs=recipients)

            logger.info(f"✅ Email sent successfully on attempt {attempt}")
            return

        except Exception as e:
            logger.error(f"❌ Attempt {attempt} failed: {str(e)}")

            if attempt < max_retries:
                time.sleep(3)  # wait before retry
            else:
                logger.error("🚨 All email attempts failed")
                raise