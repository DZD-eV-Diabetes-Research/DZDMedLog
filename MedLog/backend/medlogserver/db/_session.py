import os
from typing import AsyncGenerator
import contextlib

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from medlogserver.config import Config

config = Config()

# Global state
_db_engine: AsyncEngine | None = None
_async_session_factory: sessionmaker | None = None
_engine_pid: int | None = None


def _get_engine() -> AsyncEngine:
    global _db_engine, _engine_pid

    current_pid = os.getpid()
    if _db_engine is None or _engine_pid != current_pid:
        # We are in a new process or first initialization
        _db_engine = create_async_engine(
            config.SQL_DATABASE_URL,
            echo=config.DEBUG_SQL,
            future=True,
        )
        _engine_pid = current_pid
    return _db_engine


def _get_session_factory() -> sessionmaker:
    global _async_session_factory

    if _async_session_factory is None or _engine_pid != os.getpid():
        _async_session_factory = sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _async_session_factory


# FastAPI dependency
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = _get_session_factory()
    async with session_factory() as session:
        yield session


# Context manager for workers / scripts
@contextlib.asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    session_factory = _get_session_factory()
    async with session_factory() as session:
        yield session
        await session.close()
