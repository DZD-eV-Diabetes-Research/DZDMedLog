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
from medlogserver.db.event.model import Event, EventRead, EventUpdate, EventCreate
from medlogserver.db._base_crud import CRUDBase
from medlogserver.api.paginator import PageParams


log = get_logger()
config = Config()


class EventCRUD(CRUDBase[Event, EventRead, EventUpdate, EventCreate]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        filter_by_study_id: UUID = None,
        hide_completed: bool = False,
        pagination: PageParams = None,
    ) -> Sequence[Event]:
        log.info(f"Event.Config.order_by {Event.Config.order_by}")
        query = select(Event)
        if filter_by_study_id:
            query = query.where(Event.study_id == filter_by_study_id)
        if hide_completed:
            query = query.where(Event.completed == True)
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()
