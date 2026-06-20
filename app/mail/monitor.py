import asyncio
import logging
import ssl
from email import message_from_bytes

import aioimaplib
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.database.functions import (
    add_notification,
    get_last_uid,
    save_last_uid,
    upsert_client,
)
from app.mail.notifier import check_and_notify
from app.mail.parser import decode_subject, parse_subject
from config.config import Config

logger = logging.getLogger(__name__)

POLL_INTERVAL = 60
IMAP_TIMEOUT = 30


def _create_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


async def connect_to_imap(config: Config):
    ssl_context = None if config.mail.SSL_VERIFY else _create_ssl_context()
    imap_client = aioimaplib.IMAP4_SSL(
        host=config.mail.IMAP,
        port=config.mail.PORT,
        timeout=IMAP_TIMEOUT,
        ssl_context=ssl_context,
    )
    await imap_client.wait_hello_from_server()
    await imap_client.login(config.mail.LOGIN, config.mail.PASSWORD)
    await imap_client.select(config.mail.FOLDER)
    return imap_client


async def get_current_max_uid(imap_client) -> int | None:
    response = await imap_client.uid_search("ALL")
    if response.result != "OK":
        return None
    raw = b" ".join(response.lines).decode().strip()
    if not raw:
        return None
    uids = [int(u) for u in raw.split() if u.isdigit()]
    return max(uids) if uids else None


async def fetch_emails(imap_client, last_uid: int) -> list[dict]:
    response = await imap_client.uid_search(f"{last_uid + 1}:*")
    if response.result != "OK":
        return []

    raw = b" ".join(response.lines).decode().strip()
    if not raw:
        return []

    uids = [int(u) for u in raw.split() if u.isdigit() and int(u) > last_uid]
    if not uids:
        return []

    emails = []
    for uid in uids:
        try:
            fetch_resp = await imap_client.uid_fetch(str(uid), "(RFC822)")
        except Exception as e:
            logger.warning(f"Failed to fetch email UID={uid}: {e}")
            continue

        if fetch_resp.result != "OK":
            continue

        raw_email = None
        for line in fetch_resp.lines:
            if isinstance(line, (bytes, bytearray)) and line.startswith(b"From:"):
                continue
            if isinstance(line, (bytes, bytearray)) and b"Subject:" in line:
                continue
            if isinstance(line, (bytes, bytearray)) and len(line) > 50:
                raw_email = bytes(line)
                break

        if not raw_email:
            parts = []
            for line in fetch_resp.lines:
                if isinstance(line, (bytes, bytearray)):
                    parts.append(line)
            raw_email = b"\n".join(parts)

        try:
            msg = message_from_bytes(raw_email)
        except Exception as e:
            logger.warning(f"Failed to parse email UID={uid}: {e}")
            continue

        subject = decode_subject(msg.get("Subject", ""))
        logger.info(f"Fetched email UID={uid}, Subject={subject[:100]}")
        emails.append({"uid": uid, "subject": subject})

    return emails


async def process_emails(emails: list[dict], session) -> int:
    processed = 0
    for email_data in emails:
        parsed = parse_subject(email_data["subject"])
        if not parsed:
            logger.debug(f"Skipping UID={email_data['uid']}: does not match template")
            continue

        notification_data = {
            "code": parsed["code"],
            "machine": parsed["machine"],
            "task": parsed["task"],
            "location": parsed["location"],
            "organization": parsed["organization"],
            "index_code": parsed["index_code"],
            "status": parsed["status"],
            "message_uid": email_data["uid"],
        }

        try:
            added = await add_notification(session, notification_data)
            if added:
                await upsert_client(
                    session,
                    code=parsed["code"],
                    status=parsed["status"],
                    task_title=parsed["task"],
                )
                await check_and_notify(notification_data)
                logger.info(
                    f"Processed email UID={email_data['uid']}, client={parsed['code']}"
                )
                processed += 1
        except IntegrityError:
            await session.rollback()
            logger.warning(f"Duplicate email UID={email_data['uid']}, skipping")
            continue

    await session.commit()
    return processed


async def monitor_mailbox(config: Config, session_factory: async_sessionmaker):
    logger.info("Mailbox monitoring started")
    imap_client = None

    while True:
        try:
            if imap_client is None:
                imap_client = await connect_to_imap(config)

            async with session_factory() as session:
                last_uid = await get_last_uid(session)

                if last_uid is not None:
                    emails = await fetch_emails(imap_client, last_uid)
                else:
                    max_uid = await get_current_max_uid(imap_client)
                    if max_uid:
                        await save_last_uid(session, max_uid)
                        await session.commit()
                        logger.info(
                            f"DB is empty, recorded UID={max_uid}, waiting for new emails"
                        )
                    emails = []

                if emails:
                    processed = await process_emails(emails, session)
                    max_uid = max(e["uid"] for e in emails)
                    await save_last_uid(session, max_uid)
                    await session.commit()
                    if processed:
                        logger.info(f"Processed: {processed}, last_uid={max_uid}")

        except Exception as e:
            logger.error(f"Monitoring error: {e}", exc_info=True)
            if imap_client is not None:
                try:
                    await imap_client.logout()
                except Exception:
                    pass
            imap_client = None

        await asyncio.sleep(POLL_INTERVAL)
