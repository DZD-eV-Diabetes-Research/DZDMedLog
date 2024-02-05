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

# TODO: this generated a circular import we need to seperate model and crud classes
# from medlogserver.db.user_auth import UserAuthRefreshTokenCRUD


log = get_logger()
config = Config()


class StudyBase(Base, table=False):
    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, pattern=r"^[a-zA-Z0-9-]+$"),
    ] = Field(
        default=None,
        index=True,
        max_length=64,
        unique=True,
        schema_extra={"examples": ["PLIS", "BARIA"]},
    )

    display_name: Optional[str] = Field(
        default=None,
        index=True,
        max_length=128,
        schema_extra={
            "examples": [
                "Prädiabetes-Lebensstil-Interventions-Studie (PLIS)",
                "BARIA-DDZ-Studie",
            ]
        },
    )

    deactivated: bool = Field(default=False)

    no_permissions: bool = Field(
        default=False,
        description="If this is set to True all user have access as interviewers to the study. This can be utile when this MedLog instance only host one study.  Admin access still need to be allocated explicit.",
    )


class Study(StudyBase, BaseTable, table=True):
    __tablename__ = "study"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )


class StudyCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        show_deactivated: bool = False,
    ) -> Sequence[Study]:
        query = select(Study)
        if not show_deactivated:
            query = query.where(Study.deactivated == False)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        study_id: str | UUID,
        show_deactivated: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Study]:
        query = select(Study).where(Study.id == study_id)
        if not show_deactivated:
            query = query.where(Study.deactivated == False)

        results = await self.session.exec(statement=query)
        user: Study | None = results.one_or_none()
        if user is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user

    async def get_by_name(
        self,
        study_name: str,
        show_deactivated: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Study]:
        query = select(Study).where(Study.name == study_name)
        if not show_deactivated:
            query = query.where(Study.deactivated == False)

        results = await self.session.exec(statement=query)
        study: Study | None = results.one_or_none()
        if study is None and raise_exception_if_none:
            raise raise_exception_if_none
        return study

    async def create(
        self,
        study: Study,
        raise_exception_if_exists: Exception = None,
    ) -> Study:
        log.debug(f"Create study: {study}")
        if study.display_name is None:
            study.display_name = study.name
        existing_study: Study = await self.get_by_name(
            study.name, show_deactivated=True
        )
        if existing_study and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_study:
            return existing_study
        self.session.add(study)
        await self.session.commit()
        await self.session.refresh(study)
        return study

    async def disable(
        self,
        study_id: str | UUID,
        raise_exception_if_not_exists=None,
        raise_exception_if_allready_deactivated=None,
    ) -> bool:
        study = await self.get(
            study_id=study_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_deactivated=True,
        )
        if study.deactivated and raise_exception_if_allready_deactivated:
            raise raise_exception_if_allready_deactivated
        study.deactivated = True
        self.session.add(study)
        await self.session.commit()
        await self.session.refresh(study)
        return study

    async def update(
        self,
        user_update: Study,
        study_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> Study:
        study_id = study_id if study_id else user_update.id
        if study_id is None:
            raise ValueError(
                "Study update failed, uuid must be set in user_update or passed as argument `id`"
            )
        user_from_db = await self.get(
            study_id=study_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_deactivated=True,
        )
        for k, v in user_update.model_dump(exclude_unset=True).items():
            if k in Study.model_fields.keys():
                setattr(user_from_db, k, v)
        self.session.add(user_from_db)
        await self.session.commit()
        await self.session.refresh(user_from_db)
        return user_from_db

    async def delete(
        self,
        study_id: str | UUID,
        raise_exception_if_not_exists=None,
    ) -> Study:
        user = await self.get(
            study_id=study_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_deactivated=True,
        )
        if user is not None:
            delete(user).where(Study.pk == study_id)
        return True


async def get_study_crud(
    session: AsyncSession = Depends(get_async_session),
) -> StudyCRUD:
    yield StudyCRUD(session=session)


get_study_crud_context = contextlib.asynccontextmanager(get_study_crud)
