from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config.config import config

engine = create_async_engine(
    f"sqlite+aiosqlite:///{config.db.PATH}",
    echo=False,
)

session_factory = async_sessionmaker(engine, expire_on_commit=False)
