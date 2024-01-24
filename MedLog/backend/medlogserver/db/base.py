from datetime import datetime
from pydantic import Field
from sqlalchemy import text
import uuid as uuid_pkg
import os

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker


from medlogserver.config import Config
from medlogserver.log import get_logger


log = get_logger()
config = Config()


db_engine = create_async_engine(config.SQL_DATABASE_URL, echo=False, future=True)


async def get_session() -> AsyncSession:
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


async def init_db():
    async with db_engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


class Base(SQLModel):
    # Abstaractiion layer for SQLModel to be able to introduce global changes later
    pass


class UUIDModel(Base):
    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        sa_column_kwargs={"server_default": text("gen_random_uuid()"), "unique": True},
    )


class TimestampModel(Base):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": text("current_timestamp(0)")},
    )

    updated_at: datetime = Field(
        default=None,
        nullable=False,
        sa_column_kwargs={
            "server_default": text("current_timestamp(0)"),
            "onupdate": text("current_timestamp(0)"),
        },
    )


class BaseTable(UUIDModel, TimestampModel, Base):
    pass


class HealthCheck(Base):
    name: str
    version: str
    description: str
