from typing import List, Dict, Optional
import datetime
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


from medlogserver.db.wido_gkv_arzneimittelindex.search_engines._base import (
    MedLogDrugSearchEngineBase,
    MedLogSearchEngineResult,
)
from medlogserver.db._session import AsyncSession, get_async_session
from medlogserver.db.wido_gkv_arzneimittelindex.model.stamm import (
    Stamm,
    DRUG_SEARCHFIELDS,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.view._base import DrugViewBase
from medlogserver.api.paginator import PageParams
from medlogserver.db.wido_gkv_arzneimittelindex.model.applikationsform import (
    Applikationsform,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.darrform import Darreichungsform
from medlogserver.db.wido_gkv_arzneimittelindex.model.hersteller import Hersteller
from medlogserver.db.wido_gkv_arzneimittelindex.model.normpackungsgroessen import (
    Normpackungsgroessen,
)
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class GenericSQLDrugSearchState(SQLModel):
    __tablename__ = "generic_sql_drug_search_state"
    index_build_up_in_process: bool = Field(default=False)
    last_index_build_at: Optional[datetime.datetime] = Field(default=None)
    index_item_count: Optional[int] = Field(default=False)
    last_error: Optional[str] = Field(default=None)


class GenericSQLDrugSearchCache(SQLModel):
    __tablename__ = "generic_sql_drug_search_cache"
    pzn: str = Field(
        description="The field that should be returned on a search match adn identify the result item. in our case always a PZN but maybe change at a later stage of MedLog.",
        primary_key=True,
    )
    index_content: str = Field(
        index=True,
        description="All fields of a drug(Table: Stamm) are concenated here to be searchable",
    )


class GenericSQLDrugSearchEngine(MedLogDrugSearchEngineBase):
    description: str = (
        "'Build-in' search engine. Works with every SQL Database. Does not need any additional setup. Maybe perfoms poor concerning speed and result quality."
    )

    def __init__(self, sql_session: AsyncSession, config: Dict = None):
        self.sql_session: AsyncSession = sql_session

    async def disable(self):
        """If we switch the search engine, we may need to tidy up some thing (e.g. Remove large indexed that are not needed anymore).
        # This func will be called on every MedLog boot for non-enabled search engines.
        """
        pass

    async def build_index(self, force_rebuild: bool = False):
        # tables will be created with build in MedLog/backend/medlogserver/db/_init_db.py -> init_db() we do not need to take care here.
        state = await self.get_state()
        if state.index_build_up_in_process:
            log.warning(
                "Cancel build_index for 'GenericSQLDrugSearchEngine'-Engine because build up is allready in progress"
            )
        state.index_build_up_in_process = True
        await self.save_state(state)
        try:
            self._build_index(force_rebuild=force_rebuild)
        except Exception as err:
            log.error("Building index for 'GenericSQLDrugSearchEngine'-Engine failed")
            state = await self.get_state()
            state.index_build_up_in_process = False
            state.last_error = repr(err)
            await self.save_state(state)
            raise err
        state = await self.get_state()
        state.index_build_up_in_process = False
        state.last_index_build_at = datetime.datetime(datetime.timezone.utc)
        await self.save_state(state)

    async def _build_index(self, force_rebuild: bool):
        stamm_search_fields = []
        for s_field in DRUG_SEARCHFIELDS:
            stamm_search_fields.append(getattr(Stamm, s_field))
        query_all = (
            select(
                *stamm_search_fields,
                Applikationsform.bedeutung,
                Hersteller.bedeutung,
                Normpackungsgroessen.bedeutung,
                Darreichungsform.bedeutung,
            )
            .join(Applikationsform)
            .join(Hersteller)
            .join(Normpackungsgroessen)
            .join(Darreichungsform)
        )
        # you are here

    # async def refresh_index(self, force_rebuild: bool = False):
    #    await self.build_index(force_rebuild=True)

    async def index_ready(self):
        """This should be a low cost function. It should return False if the index is not existent or in the process of build up."""
        pass

    async def search(self, search_term: str) -> List[MedLogSearchEngineResult]:
        pass

    async def get_state(self) -> GenericSQLDrugSearchState:
        query = select(GenericSQLDrugSearchState)
        res = await self.sql_session.exec(query)
        state = res.one_or_none()
        if state is None:
            new_state = GenericSQLDrugSearchState()
            await self.save_state(new_state)
            return new_state
        return state

    async def save_state(
        self, state: GenericSQLDrugSearchState
    ) -> GenericSQLDrugSearchState:
        self.sql_session.add(state)
        await self.sql_session.commit()
        await self.sql_session.refresh(state)
        return state
