from typing import List, Dict
from typing_extensions import Unpack
from pydantic import BaseModel, Field
from medlogserver.db._session import AsyncSession, get_async_session
from medlogserver.api.paginator import QueryParamsInterface, PaginatedResponse
from medlogserver.model.wido_gkv_arzneimittelindex.stamm import StammRead
from medlogserver.model.drug_data.drug import Drug


class MedLogSearchEngineResult(BaseModel):
    drug_id: str = Field(examples=["ff16fc08-6484-4097-bd51-f8c17c640a06"])
    relevance_score: float = Field(examples=["1.4"])
    item: Drug


class MedLogDrugSearchEngineBase:
    description: str = (
        "A short descriptionn how this search engine works and what it needs to run"
    )
    user_hint: str = (
        "A hint for the user like 'You can quote string to find drugs with this exact quote: `'vitamin C' aspirin'`"
    )

    def __init__(self, sql_session: AsyncSession, config: Dict = None):
        self.sql_session = sql_session

    async def disable(self):
        """If we switch the search engine, we may need to tidy up some thing (e.g. Remove large indexed that are not needed anymore).
        # This func will be called on every MedLog boot for non-enabled search engines.
        """
        pass

    async def build_index(self, force_rebuild: bool = False):
        """This function need to take care of
        * Are all dependcies meet to build a search index (e.g. Server reachable, tables created, indexes created)
        * update the index if called
        * it must be idempotent. meaning if the index is allready in build-up or allready existent it should do nothing
        * force rebuild should only refresh the index if the index is ready (not in the process of a rebuild/refresh)
        """
        pass

    async def refresh_index(self, force_rebuild: bool = False):
        """This function is for engines where index build up and refresh follow different processes"""
        await self.build_index(force_rebuild=True)

    async def index_ready(self) -> bool:
        """This should be a low cost function. It should return False if the index is not existent or in the process of build up."""
        pass

    async def search(
        self,
        search_term: str = None,
        pagination: QueryParamsInterface = None,
        **filter_ref_vals: Unpack[int | str],
    ) -> PaginatedResponse[MedLogSearchEngineResult]:
        pass

    async def total_item_count(self) -> int:
        # count of all items that are in the index.
        pass
