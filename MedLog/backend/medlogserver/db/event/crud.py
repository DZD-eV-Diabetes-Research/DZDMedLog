from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel

import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import Base, BaseTable
from medlogserver.db.event.model import Event, EventUpdate

# TODO: this generated a circular import we need to seperate model and crud classes
# from medlogserver.db.event_auth import EventAuthRefreshTokenCRUD


log = get_logger()
config = Config()


class EventCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        filter_by_study_id: UUID = None,
        hide_completed: bool = False,
    ) -> Sequence[Event]:
        query = select(Event)
        if filter_by_study_id:
            query = query.where(Event.study_id == filter_by_study_id)
        if hide_completed:
            query = query.where(Event.completed == True)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        event_id: str | UUID,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Event]:
        query = select(Event).where(Event.id == event_id)
        results = await self.session.exec(statement=query)
        event: Event | None = results.one_or_none()
        if event is None and raise_exception_if_none:
            raise raise_exception_if_none
        return event

    async def create(
        self,
        event: Event,
        raise_exception_if_exists: Exception = None,
    ) -> Event:
        log.debug(f"Create event: {event}")
        existing_events: Event = await self.list(
            filter_by_study_id=event.study_id, hide_completed=False
        )
        if existing_events and raise_exception_if_exists:
            raise raise_exception_if_exists
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def update(
        self,
        event_update: EventUpdate,
        event_id: str | UUID,
        raise_exception_if_not_exists=None,
    ) -> Event:
        event_from_db = await self.get(
            event_id=event_id, raise_exception_if_none=raise_exception_if_not_exists
        )
        for k, v in event_update.model_dump(exclude_unset=True).items():
            if k in EventUpdate.model_fields.keys():
                setattr(event_from_db, k, v)
        self.session.add(event_from_db)
        await self.session.commit()
        await self.session.refresh(event_from_db)
        return event_from_db

    async def delete(
        self,
        event_id: str | UUID,
        raise_exception_if_not_exists=None,
    ) -> Event:
        event = await self.get(
            event_id=event_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_deactivated=True,
        )
        if event is not None:
            delete(event).where(Event.id == event_id)
        return True


async def get_event_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[EventCRUD, None]:
    yield EventCRUD(session=session)


get_events_crud_context = contextlib.asynccontextmanager(get_event_crud)
