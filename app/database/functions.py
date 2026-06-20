from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.enums.enums import StatusesEnum
from app.database.models.models import ClientsORM, NotificationsORM, SyncStateORM


async def add_notification(session: AsyncSession, data: dict) -> bool:
    try:
        notification = NotificationsORM(**data)
        session.add(notification)
        await session.flush()
        return True
    except IntegrityError:
        await session.expunge_all()
        raise


async def get_notification_by_uid(session: AsyncSession, message_uid: int):
    result = await session.execute(
        select(NotificationsORM).where(NotificationsORM.message_uid == message_uid)
    )
    return result.scalar_one_or_none()


async def get_notifications(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    client_code: str | None = None,
    status: StatusesEnum | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    query = select(NotificationsORM)

    if date_from:
        query = query.where(NotificationsORM.created_at >= date_from)
    if date_to:
        query = query.where(NotificationsORM.created_at <= date_to)
    if client_code:
        query = query.where(NotificationsORM.code == client_code)
    if status:
        query = query.where(NotificationsORM.status == status)

    sort_column = getattr(NotificationsORM, sort_by, NotificationsORM.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def count_notifications(session: AsyncSession, **filters) -> int:
    query = select(func.count()).select_from(NotificationsORM)

    if filters.get("date_from"):
        query = query.where(NotificationsORM.created_at >= filters["date_from"])
    if filters.get("date_to"):
        query = query.where(NotificationsORM.created_at <= filters["date_to"])
    if filters.get("client_code"):
        query = query.where(NotificationsORM.code == filters["client_code"])
    if filters.get("status"):
        query = query.where(NotificationsORM.status == filters["status"])

    result = await session.execute(query)
    return result.scalar()


async def delete_notification(session: AsyncSession, message_uid: int) -> bool:
    result = await session.execute(
        select(NotificationsORM).where(NotificationsORM.message_uid == message_uid)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        return False
    await session.delete(notification)
    return True


async def get_last_uid(session: AsyncSession):
    result = await session.execute(
        select(SyncStateORM).where(SyncStateORM.id == 1)
    )
    state = result.scalar_one_or_none()
    if state:
        return state.last_uid
    return None


async def save_last_uid(session: AsyncSession, uid: int):
    state = SyncStateORM(id=1, last_uid=uid)
    await session.merge(state)


async def get_stats(session: AsyncSession) -> dict:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(
            func.count().label("total"),
            func.count().filter(NotificationsORM.created_at >= now - timedelta(days=1)).label("last_24h"),
            func.count().filter(NotificationsORM.created_at >= now - timedelta(weeks=1)).label("last_week"),
            func.count().filter(NotificationsORM.created_at >= now - timedelta(days=30)).label("last_month"),
            func.min(NotificationsORM.created_at).label("min_date"),
            func.max(NotificationsORM.created_at).label("max_date"),
        ).select_from(NotificationsORM)
    )
    row = result.one()
    return {
        "total": row.total,
        "last_24h": row.last_24h,
        "last_week": row.last_week,
        "last_month": row.last_month,
        "min_date": row.min_date,
        "max_date": row.max_date,
    }


async def upsert_client(
    session: AsyncSession,
    code: str,
    status: StatusesEnum,
    task_title: str,
):
    result = await session.execute(
        select(ClientsORM).where(ClientsORM.code == code)
    )
    client = result.scalar_one_or_none()
    if client:
        client.last_status = status
        client.last_update = datetime.now(timezone.utc)
        client.last_task_title = task_title
    else:
        client = ClientsORM(
            code=code,
            last_status=status,
            last_update=datetime.now(timezone.utc),
            last_task_title=task_title,
        )
        session.add(client)


async def get_client(session: AsyncSession, code: str):
    result = await session.execute(
        select(ClientsORM).where(ClientsORM.code == code)
    )
    return result.scalar_one_or_none()


async def get_all_clients(session: AsyncSession):
    result = await session.execute(
        select(ClientsORM).order_by(ClientsORM.code)
    )
    return list(result.scalars().all())
