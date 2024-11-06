from typing import List, Dict, Optional
from typing_extensions import Unpack
import uuid
from pydantic import BaseModel, Field
from medlogserver.db._session import AsyncSession, get_async_session
from medlogserver.api.paginator import QueryParamsInterface, PaginatedResponse
from medlogserver.model.drug_data.drug import DrugData
from medlogserver.model.drug_data.api_drug_model_factory import (
    drug_api_read_class_factory,
)

DrugRead = drug_api_read_class_factory()


class MedLogSearchEngineResult(BaseModel):
    drug_id: uuid.UUID = Field(examples=["ff16fc08-6484-4097-bd51-f8c17c640a06"])
    relevance_score: float = Field(examples=["1.4"])
    drug: DrugRead


class MedLogDrugSearchEngineBase:
    description: str = (
        "A short descriptionn how this search engine works and what it needs to run"
    )
    user_hint: str = (
        "A hint for the user like 'You can quote string to find drugs with this exact quote: `'vitamin C' aspirin'`"
    )

    def __init__(self, engine_config: Dict = None):
        self.engine_config = engine_config

    async def disable(self):
        """If we switch the search engine, we may need to tidy up some thing (e.g. Remove large indexed that are not needed anymore).
        # This func will be called on every MedLog boot for non-enabled search engines.
        """
        raise NotImplementedError()

    async def build_index(self, force_rebuild: bool = False):
        """This function need to take care of
        * Are all dependcies meet to build a search index (e.g. Server reachable, tables created, indexes created)
        * update the index if called
        * it must be idempotent. meaning if the index is allready in build-up or allready existent it should do nothing
        * force rebuild should only refresh the index if the index is ready (not in the process of a rebuild/refresh)
        """
        raise NotImplementedError()

    async def refresh_index(self, force_rebuild: bool = False):
        """This function is for engines where index build up and refresh follow different processes"""
        await self.build_index(force_rebuild=True)

    async def insert_drug_to_index(self, drug: DrugData):
        """Adhoc insert a single drug into the index. this is needed for user defined custom drugs.

        Args:
            drug (Drug): _description_

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError()

    async def index_ready(self) -> bool:
        """This should be a low cost function. It should return False if the index is not existent or in the process of build up."""
        raise NotImplementedError()

    async def search(
        self,
        search_term: str = None,
        only_market_accessable: Optional[bool] = None,
        pagination: QueryParamsInterface = None,
        **filter_ref_vals: Unpack[int | str],
    ) -> PaginatedResponse[MedLogSearchEngineResult]:
        raise NotImplementedError()

    async def total_item_count(self) -> int:
        # count of all items that are in the index.
        raise NotImplementedError()
