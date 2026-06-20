from datetime import datetime

from pydantic import BaseModel

from app.database.enums.enums import StatusesEnum


class NotificationRead(BaseModel):
    id: int
    code: str
    machine: str
    task: str
    location: str
    organization: str
    index_code: str
    status: StatusesEnum
    created_at: datetime
    message_uid: int

    model_config = {"from_attributes": True}


class ClientRead(BaseModel):
    id: int
    code: str
    last_update: datetime | None
    last_status: StatusesEnum
    last_task_title: str

    model_config = {"from_attributes": True}


class PaginatedNotifications(BaseModel):
    items: list[NotificationRead]
    total: int
    page: int
    size: int


class StatsResponse(BaseModel):
    total: int
    last_24h: int
    last_week: int
    last_month: int
    min_date: datetime | None
    max_date: datetime | None
