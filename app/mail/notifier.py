import asyncio
import logging
from email.mime.text import MIMEText

import aiosmtplib

from config.config import config

logger = logging.getLogger(__name__)

smtp_client: aiosmtplib.SMTP | None = None
smtp_lock = asyncio.Lock()


STATUS_TEXT = {
    "error": "Error",
    "warning": "Warning",
    "good": "Success",
}


async def get_smtp_client() -> aiosmtplib.SMTP:
    global smtp_client
    if smtp_client is not None:
        try:
            await smtp_client.noop()
            return smtp_client
        except Exception:
            try:
                await smtp_client.quit()
            except Exception:
                pass
            smtp_client = None

    use_tls = config.smtp.PORT == 465
    smtp_client = aiosmtplib.SMTP(
        hostname=config.smtp.HOST,
        port=config.smtp.PORT,
        timeout=config.smtp.TIMEOUT,
        use_tls=use_tls,
    )
    await smtp_client.connect()
    if not use_tls:
        await smtp_client.starttls()
    await smtp_client.login(config.smtp.LOGIN, config.smtp.PASSWORD)
    logger.info(f"SMTP connected to {config.smtp.HOST}:{config.smtp.PORT}")
    return smtp_client


async def send_email(subject: str, body: str, recipients: list[str]):
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = config.smtp.LOGIN
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    async with smtp_lock:
        client = await get_smtp_client()
        await client.send_message(msg)
        logger.info(f"SMTP email sent to {recipients}")


async def check_and_notify(notification_data: dict):
    status_value = notification_data["status"].value
    notify_on = config.smtp.get_notify_on_list()

    if status_value not in notify_on:
        logger.debug(
            f"Skipping SMTP for client {notification_data['code']}: "
            f"status '{status_value}' not in notify_on {notify_on}"
        )
        return

    recipients = config.smtp.get_recipients_list()
    if not recipients:
        logger.warning("No recipients configured for SMTP notifications")
        return

    status_text = STATUS_TEXT.get(status_value, status_value)
    subject = f"[Backup] {status_text} - Client {notification_data['code']}"
    body = (
        f"Client: {notification_data['code']}\n"
        f"Machine: {notification_data['machine']}\n"
        f"Task: {notification_data['task']}\n"
        f"Location: {notification_data['location']}\n"
        f"Organization: {notification_data['organization']}\n"
        f"Index: {notification_data['index_code']}\n"
        f"Status: {status_text}\n"
    )

    try:
        await send_email(subject, body, recipients)
        logger.info(f"SMTP notification sent for client {notification_data['code']}")
    except Exception as e:
        logger.error(f"SMTP send error: {e}")
        global smtp_client
        if smtp_client is not None:
            try:
                await smtp_client.quit()
            except Exception:
                pass
        smtp_client = None
