from typing import (
    AsyncGenerator,
    List,
    Optional,
    Literal,
    Sequence,
    Annotated,
    Dict,
    Tuple,
)
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import (
    Field,
    select,
    delete,
    Column,
    JSON,
    SQLModel,
    column,
    or_,
    col,
    funcfilter,
)
from sqlalchemy import func
import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.wido_gkv_arzneimittelindex.view._base import DrugViewBase
from medlogserver.api.paginator import PageParams

from medlogserver.db.wido_gkv_arzneimittelindex.search_engines._base import (
    MedLogDrugSearchEngineBase,
)
from medlogserver.db.wido_gkv_arzneimittelindex.search_engines.sql import (
    GenericSQLDrugSearchEngine,
    MedLogSearchEngineResult,
)


log = get_logger()
config = Config()


class StammJoinedView(DrugViewBase):

    async def search(
        self,
        search_term: str = None,
        pzn_contains: str = None,
        filter_packgroesse: str = None,
        filter_darrform: str = None,
        filter_appform: str = None,
        filter_normpackungsgroeße_zuzahlstufe: str = None,
        filter_atc_level2: str = None,
        filter_generikakenn: str = None,
        filter_apopflicht: int = None,
        filter_preisart_neu: str = None,
        only_current_medications: bool = False,
        pagination: PageParams = None,
    ) -> Sequence[MedLogSearchEngineResult]:
        search_engine: MedLogDrugSearchEngineBase = None
        if config.DRUG_SEARCHENGINE_CLASS == "GenericSQLDrugSearch":
            search_engine = GenericSQLDrugSearchEngine(
                await self._get_current_ai_version()
            )
        return await search_engine.search(
            search_term=search_term,
            pzn_contains=pzn_contains,
            filter_packgroesse=filter_packgroesse,
            filter_darrform=filter_darrform,
            filter_appform=filter_appform,
            filter_normpackungsgroeße_zuzahlstufe=filter_normpackungsgroeße_zuzahlstufe,
            filter_atc_level2=filter_atc_level2,
            filter_generikakenn=filter_generikakenn,
            filter_apopflicht=filter_apopflicht,
            filter_preisart_neu=filter_preisart_neu,
            only_current_medications=only_current_medications,
        )


async def get_stamm_joined_view(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[StammJoinedView, None]:
    yield StammJoinedView(session=session)


get_stamm_joined_view_context = contextlib.asynccontextmanager(get_stamm_joined_view)
