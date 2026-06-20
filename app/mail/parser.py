import re
from email.header import decode_header

from app.database.enums.enums import StatusesEnum


STATUS_MAP = {
    "Успешно": StatusesEnum.good,
    "Предупреждение": StatusesEnum.warning,
    "Ошибка": StatusesEnum.error,
}

# Template: $code-machine-task-location-org-index, Result: status
# Example: $28-XPPSERVER-1CBOOK-D-XPP-AB, Result: Warning
HEADER_PATTERN = re.compile(
    r"\$(?P<code>\d+)"
    r"-(?P<machine>[^-]+)"
    r"-(?P<task>[^-]+)"
    r"-(?P<location>[^-]+)"
    r"-(?P<organization>[^-]+)"
    r"-(?P<index_code>[A-Za-z]{2})"
    r",\s*Результат:\s*(?P<status>.+)$"
)


def map_status(status_text: str) -> StatusesEnum:
    status_text = status_text.strip()
    for key, value in STATUS_MAP.items():
        if key in status_text:
            return value
    return StatusesEnum.warning


def decode_subject(subject: str) -> str:
    if not subject:
        return ""
    parts = decode_header(subject)
    decoded = []
    for data, charset in parts:
        if isinstance(data, bytes):
            decoded.append(data.decode(charset or "utf-8"))
        else:
            decoded.append(data)
    return "".join(decoded)


def parse_subject(subject: str) -> dict | None:
    subject = subject.strip()
    if "$" not in subject:
        return None

    match = HEADER_PATTERN.search(subject)
    if not match:
        return None

    return {
        "code": match.group("code"),
        "machine": match.group("machine"),
        "task": match.group("task"),
        "location": match.group("location"),
        "organization": match.group("organization"),
        "index_code": match.group("index_code"),
        "status": map_status(match.group("status")),
    }
