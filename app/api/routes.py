from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.enums.enums import StatusesEnum
from app.database.functions import (
    count_notifications,
    get_all_clients,
    get_client,
    get_notification_by_uid,
    get_notifications,
    get_stats,
)
from app.database.session import session_factory
from app.schemas.schemas import (
    ClientRead,
    NotificationRead,
    PaginatedNotifications,
    StatsResponse,
)

router = APIRouter(prefix="/api")

ALLOWED_SORT_COLUMNS = {"id", "code", "machine", "task", "status", "created_at", "message_uid"}


async def get_session() -> AsyncSession:
    async with session_factory() as session:
        yield session


@router.get("/notifications", response_model=PaginatedNotifications)
async def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    client: str | None = Query(None),
    status: StatusesEnum | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    session: AsyncSession = Depends(get_session),
):
    if sort_by not in ALLOWED_SORT_COLUMNS:
        sort_by = "created_at"

    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "client_code": client,
        "status": status,
    }

    total = await count_notifications(session, **filters)
    items = await get_notifications(
        session,
        limit=limit,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        client_code=client,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    page = offset // limit + 1 if limit else 1

    return PaginatedNotifications(
        items=[NotificationRead.model_validate(i) for i in items],
        total=total,
        page=page,
        size=limit,
    )


@router.get("/notifications/stats", response_model=StatsResponse)
async def notification_stats(
    session: AsyncSession = Depends(get_session),
):
    stats = await get_stats(session)
    return StatsResponse(**stats)


@router.get("/notifications/{message_uid}", response_model=NotificationRead)
async def get_notification(
    message_uid: int,
    session: AsyncSession = Depends(get_session),
):
    notification = await get_notification_by_uid(session, message_uid)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationRead.model_validate(notification)


@router.get("/clients", response_model=list[ClientRead])
async def list_clients(
    session: AsyncSession = Depends(get_session),
):
    clients = await get_all_clients(session)
    return [ClientRead.model_validate(c) for c in clients]


@router.get("/clients/{code}", response_model=ClientRead)
async def get_client_by_code(
    code: str,
    session: AsyncSession = Depends(get_session),
):
    client = await get_client(session, code)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientRead.model_validate(client)
