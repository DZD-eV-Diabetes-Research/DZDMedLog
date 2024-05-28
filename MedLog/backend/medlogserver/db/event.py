from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Tuple
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, func, col

import uuid
from uuid import UUID


from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.event import (
    Event,
    EventRead,
    EventUpdate,
    EventCreate,
    EventReadPerProband,
)
from medlogserver.db._base_crud import create_crud_base
from medlogserver.db.interview import Interview
from medlogserver.api.paginator import QueryParamsInterface


log = get_logger()
config = Config()


class EventCRUD(
    create_crud_base(
        table_model=Event,
        read_model=EventRead,
        create_model=EventCreate,
        update_model=EventUpdate,
    )
):
    async def count(
        self,
        filter_study_id: uuid.UUID | str = None,
        hide_completed: bool = False,
    ) -> int:
        query = select(func.count()).select_from(Event)
        if filter_study_id:
            query = query.where(Event.study_id == filter_study_id)
        if hide_completed:
            query = query.where(Event.completed == True)
        results = await self.session.exec(statement=query)
        return results.first()

    async def list(
        self,
        filter_study_id: UUID = None,
        hide_completed: bool = False,
        pagination: QueryParamsInterface = None,
    ) -> Sequence[Event]:
        if isinstance(filter_study_id, str):
            filter_study_id: UUID = UUID(filter_study_id)
        log.info(f"Event.Config.order_by {Event.Config.order_by}")
        query = select(Event)
        if filter_study_id:
            # query = query.where(Event.study_id == prep_uuid_for_qry(filter_study_id))
            query = query.where(Event.study_id == filter_study_id)
        if hide_completed:
            query = query.where(Event.completed == True)
        if pagination:
            query = pagination.append_to_query(query)
        log.debug(f"List Event query: {query}")
        results = await self.session.exec(statement=query)
        return results.all()

    async def list_by_proband(
        self,
        proband_id: UUID = None,
        exlude_empty_events: bool = False,
        filter_study_id: UUID = None,
        hide_completed: bool = False,
        pagination: QueryParamsInterface = None,
    ) -> Sequence[EventReadPerProband]:
        """List all events that a proband participated"""
        if isinstance(filter_study_id, str):
            filter_study_id: UUID = UUID(filter_study_id)
        query = (
            select(Event, func.count(Event.id))
            .join(Interview)
            .where(Interview.proband_external_id == proband_id)
        )

        if filter_study_id:
            # query = query.where(Event.study_id == prep_uuid_for_qry(filter_study_id))
            query = query.where(Event.study_id == filter_study_id)
        if hide_completed:
            query = query.where(Event.completed == True)
        if pagination:
            query = pagination.append_to_query(query)
        query = query.group_by(Event)

        log.debug(f"List Event query: {query}")
        query_result = await self.session.exec(statement=query)
        event_obj_with_proband_count: List[Tuple[Event, int]] = query_result.all()
        if not exlude_empty_events:
            #  we need to include event with no interview for this proband
            all_study_events: List[Event] = await self.list(
                filter_study_id=filter_study_id, hide_completed=hide_completed
            )
            for event in all_study_events:
                if event not in [res[0] for res in event_obj_with_proband_count]:
                    event_obj_with_proband_count.append((event, 0))

        # cast from Event to EventReadPerProband.
        # todo: this is a little bit awkward/hard-to-read. Maybe there is a better option
        results = [
            EventReadPerProband(
                proband_id=proband_id,
                proband_interview_count=res[1],
                **res[0].model_dump(),
            )
            for res in event_obj_with_proband_count
        ]
        log.debug(results)
        return results

    async def reorder_events(self, ids: List[uuid.UUID]) -> List[EventRead]:
        query = select(Event).where(col(Interview.id).in_(ids))
        sequence = 10
        query_result = await self.session.exec(statement=query)
        event_objs: List[Event] = query_result.all()
        for event_id in ids:
            next_event = next((e for e in event_objs if e.id == event_id), None)
            # maybe event was deleted in the background by other user. therefore we catch if id is not existent in event list
            if next_event is not None:
                next_event.order_position = sequence
                sequence += 10
        # save/commit new event order
        self.session.add_all(event_objs)
        await self.session.commit()
