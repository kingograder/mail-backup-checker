from datetime import datetime

from sqlalchemy import Enum, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.enums.enums import StatusesEnum
from app.database.models.base import Base


class NotificationsORM(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    code: Mapped[str] = mapped_column(String, nullable=False)
    machine: Mapped[str] = mapped_column(String, nullable=False)
    task: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    organization: Mapped[str] = mapped_column(String, nullable=False)
    index_code: Mapped[str] = mapped_column(String(2), nullable=False)
    status: Mapped[StatusesEnum] = mapped_column(
        Enum(StatusesEnum, name="status", native_enum=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP")
    )
    message_uid: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)


class ClientsORM(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    last_update: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP")
    )
    last_status: Mapped[StatusesEnum] = mapped_column(
        Enum(StatusesEnum, name="last_status", native_enum=True), nullable=False
    )
    last_task_title: Mapped[str] = mapped_column(String, nullable=False)


class SyncStateORM(Base):
    __tablename__ = "sync_state"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    last_uid: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
