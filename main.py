import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.routes import router
from app.database.models.base import Base
from app.database.session import engine, session_factory
from app.mail.monitor import monitor_mailbox
from config.config import config

logger = logging.getLogger(__name__)

monitor_task: asyncio.Task | None = None


async def init_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global monitor_task
    logging.basicConfig(
        level=logging.getLevelName(config.logging.LEVEL),
        format=config.logging.FORMAT,
    )
    logger.info("Application starting")
    Path(config.db.PATH).parent.mkdir(parents=True, exist_ok=True)
    await init_database()
    monitor_task = asyncio.create_task(monitor_mailbox(config, session_factory))
    yield
    logger.info("Application stopping")
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()


app = FastAPI(title="Mail Backup Checker", lifespan=lifespan)
app.include_router(router)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    uvicorn.run("main:app", host=config.api.HOST, port=config.api.PORT, reload=False)
