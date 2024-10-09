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
from typing_extensions import Unpack
from fastapi import Depends, HTTPException, status
import contextlib

from sqlmodel.ext.asyncio.session import AsyncSession


from medlogserver.db._session import get_async_session
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.api.paginator import QueryParamsInterface, PaginatedResponse

from medlogserver.db.drug_data.drug_search._base import (
    MedLogDrugSearchEngineBase,
)
from medlogserver.db.drug_data.drug_search.search_module_generic_sql import (
    GenericSQLDrugSearchEngine,
    MedLogSearchEngineResult,
)
from medlogserver.db.drug_data.drug_dataset_version import (
    DrugDataSetVersionCRUD,
)

from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion

log = get_logger()
config = Config()


class SearchEngineNotReadyException(Exception):
    pass


class SearchEngineNotConfiguredException(Exception):
    pass


class DrugSearch:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._current_dataset_version: DrugDataSetVersion = None
        self.search_engine: MedLogDrugSearchEngineBase = None

    async def get_current_dataset_version(
        self,
    ) -> DrugDataSetVersion:
        if self._current_dataset_version is None:
            async with DrugDataSetVersionCRUD.crud_context(
                self.session
            ) as dataset_version_crud:
                dataset_version_crud: DrugDataSetVersionCRUD = dataset_version_crud
                self._current_dataset_version = await dataset_version_crud.get_current()

        return self._current_dataset_version

    async def _preflight(self):
        if self.search_engine is None:
            # if alternative search engines are implemented later, this is the place where to enable them. At the moment there is only "GenericSQLDrugSearch"
            if config.DRUG_SEARCHENGINE_CLASS == "GenericSQLDrugSearch":
                search_engine = GenericSQLDrugSearchEngine(
                    await self.get_current_dataset_version()
                )
                index_ready = await search_engine.index_ready()
                if index_ready:
                    self.search_engine = search_engine
                    return
                else:
                    raise SearchEngineNotReadyException(
                        "The search index is still building or warming up. Please try again in a little bit."
                    )
        raise SearchEngineNotConfiguredException(
            "Could not find a valid drug search engine configuration. Search will not work."
        )

    async def total_drug_count(self) -> int:
        await self._preflight()
        return await self.search_engine.total_item_count()

    async def healthy(self) -> bool:
        try:
            await self._preflight()
            await self.search_engine.total_item_count()
            return True
        except Exception as e:
            log.debug(f"Drug search healthcheck was negative with error: {e}")
            return False

    async def get_current_dataset_version(
        self,
    ) -> DrugDataSetVersion:
        if self._current_dataset_version is None:
            async with DrugDataSetVersionCRUD.crud_context(
                self.session
            ) as dataset_version_crud:
                dataset_version_crud: DrugDataSetVersionCRUD = dataset_version_crud
                self._current_dataset_version = await dataset_version_crud.get_current()
        return self._current_dataset_version

    async def search(
        self,
        search_term: str = None,
        pagination: QueryParamsInterface = None,
        **filter_ref_vals: int | str | bool,
    ) -> PaginatedResponse[MedLogSearchEngineResult]:
        await self._preflight()
        return await self.search_engine.search(
            search_term=search_term,
            filter_ref_vals=filter_ref_vals,
            pagination=pagination,
        )


async def get_drug_search(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[DrugSearch, None]:

    yield DrugSearch(session=session)


get_drug_search_context = contextlib.asynccontextmanager(get_drug_search)
