from typing import List, Dict
from pydantic import BaseModel
from medlogserver.db._session import AsyncSession, get_async_session
from medlogserver.db.wido_gkv_arzneimittelindex.model.stamm import StammRead


class MedLogSearchEngineResult(BaseModel):
    pzn: str
    item: StammRead
    score: int


class MedLogDrugSearchEngineBase:
    description: str = (
        "A short descriptionn how this search engine works and what it need to run"
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

    async def index_ready(self):
        """This should be a low cost function. It should return False if the index is not existent or in the process of build up."""
        pass

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
    ) -> List[MedLogSearchEngineResult]:
        pass

    async def item_count(self):
        # count of all items that are in the index.
        pass
