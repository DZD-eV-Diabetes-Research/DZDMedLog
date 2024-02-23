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
from fastapi import Depends, HTTPException, status
import contextlib

from sqlmodel.ext.asyncio.session import AsyncSession


from medlogserver.db._session import get_async_session
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.wido_gkv_arzneimittelindex.view._base import DrugViewBase
from medlogserver.api.paginator import PageParams, PaginatedResponse

from medlogserver.db.wido_gkv_arzneimittelindex.drug_search._base import (
    MedLogDrugSearchEngineBase,
)
from medlogserver.db.wido_gkv_arzneimittelindex.drug_search.search_module_generic_sql import (
    GenericSQLDrugSearchEngine,
    MedLogSearchEngineResult,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.ai_data_version import (
    AiDataVersionCRUD,
    get_ai_data_version_crud,
    get_ai_data_version_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)

log = get_logger()
config = Config()


class SearchEngineNotReadyException(Exception):
    pass


class SearchEngineNotConfiguredException(Exception):
    pass


class DrugSearch(DrugViewBase):
    def __init__(self, session: AsyncSession):
        self.session = session
        self._current_ai_version: AiDataVersion = None
        self.search_engine: MedLogDrugSearchEngineBase = None

    async def _preflight(self):
        if self.search_engine is None:
            if config.DRUG_SEARCHENGINE_CLASS == "GenericSQLDrugSearch":
                search_engine = GenericSQLDrugSearchEngine(
                    await self._get_current_ai_version()
                )
                if search_engine.index_ready():
                    self.search_engine = search_engine
                    return
                else:
                    raise SearchEngineNotReadyException(
                        "The search index is in build up. Please try again later."
                    )
        raise SearchEngineNotConfiguredException(
            "Could not find a valid drug search engine configuration. Search will not work."
        )

    async def total_drug_count(self) -> int:
        self._preflight()
        return await self.search_engine.total_item_count()

    async def _get_current_ai_version(
        self,
    ) -> AiDataVersion:
        if self._current_ai_version is None:
            async with get_ai_data_version_crud_context(
                self.session
            ) as ai_version_crud:
                self._current_ai_version = await ai_version_crud.get_current()
        return self._current_ai_version

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
    ) -> PaginatedResponse[MedLogSearchEngineResult]:
        await self._preflight()
        return await self.search_engine.search(
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
            pagination=pagination,
        )


async def get_drug_search(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[DrugSearch, None]:
    yield DrugSearch(session=session)


get_drug_search_context = contextlib.asynccontextmanager(get_drug_search)
