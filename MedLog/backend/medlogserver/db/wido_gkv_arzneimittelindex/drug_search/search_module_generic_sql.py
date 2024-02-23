from typing import List, Dict, Optional
import shlex
import traceback
import datetime
import uuid
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, delete, desc
from sqlalchemy.sql.operators import (
    is_not,
    is_,
    contains,
    in_op,
    icontains_op,
    contains_op,
    istartswith_op,
    op,
)
from sqlalchemy import case, func
from medlogserver.db._session import get_async_session_context
from medlogserver.db.wido_gkv_arzneimittelindex.drug_search._base import (
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

from medlogserver.api.paginator import PageParams, PaginatedResponse
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
from medlogserver.db.wido_gkv_arzneimittelindex.crud.stamm import get_stamm_crud_context
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class GenericSQLDrugSearchState(SQLModel, table=True):
    __tablename__ = "generic_sql_drug_search_state"
    dummy_pk: int = Field(default=1, primary_key=True)
    index_build_up_in_process: bool = Field(default=False)
    last_index_build_at: Optional[datetime.datetime] = Field(default=None)
    last_index_build_based_on_ai_version_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="ai_dataversion.id"
    )
    index_item_count: Optional[int] = Field(default=False)
    last_error: Optional[str] = Field(default=None)


class GenericSQLDrugSearchCache(SQLModel, table=True):
    __tablename__ = "generic_sql_drug_search_cache"
    pzn: str = Field(
        description="The field that should be returned on a search match adn identify the result item. in our case always a PZN but maybe change at a later stage of MedLog.",
        primary_key=True,
    )
    darrform: str
    appform: str
    atc_code: Optional[str]
    normpackungsgroeße_zuzahlstufe: str
    packungsgroesse: int
    ahdatum: Optional[str]
    generikakenn: int
    preisart_neu: Optional[str]
    apopflicht: int
    index_content: str = Field(
        index=True,
        description="All fields of a drug(Table: Stamm) are concenated here to be searchable",
    )


class GenericSQLDrugSearchEngine(MedLogDrugSearchEngineBase):
    description: str = (
        "'Build-in' search engine. Works with every SQL Database. Does not need any additional setup. Maybe perfoms poor concerning speed and result quality."
    )

    def __init__(
        self,
        target_ai_data_version: AiDataVersion,
        config: Dict = None,
    ):
        self.target_ai_data_version: AiDataVersion = target_ai_data_version

    async def disable(self):
        """If we switch the search engine, we may need to tidy up some thing (e.g. Remove large indexed that are not needed anymore).
        # This func will be called on every MedLog boot for non-enabled search engines.
        """
        pass

    async def build_index(self, force_rebuild: bool = False):
        # tables will be created with build in MedLog/backend/medlogserver/db/_init_db.py -> init_db() we do not need to take care here.
        state = await self._get_state()
        log.debug(f"Build index called. Before state {state}")
        if state.index_build_up_in_process:
            log.warning(
                "Cancel build_index for 'GenericSQLDrugSearchEngine'-Engine because build up is allready in progress"
            )
            return
        if (
            state.last_index_build_based_on_ai_version_id
            == self.target_ai_data_version.id
            and not force_rebuild
        ):
            log.warning(
                "Skip build_index for 'GenericSQLDrugSearchEngine'-Engine because search index is up 2 date"
            )
            return

        state.index_build_up_in_process = True
        index_item_count = None
        await self._save_state(state)
        try:
            log.info("Build drug search index...")
            async with get_async_session_context() as session:
                await self._clear_cache(session=session)
                await self._build_index(session=session)
                index_item_count = await self._count_cache_items(session=session)
                session.commit()
            log.info("...building drug search index done.")
        except Exception as err:
            log.error("Building index for 'GenericSQLDrugSearchEngine'-Engine failed")
            # ToDo. We need an extra session here. when there is an sql error the state read/write will be prevented
            state = await self._get_state()
            state.index_build_up_in_process = False
            state.last_error = repr(traceback.format_exc())
            await self._save_state(state)
            raise err
        state = await self._get_state()
        state.index_build_up_in_process = False
        state.last_index_build_at = datetime.datetime.now(tz=datetime.timezone.utc)
        state.last_index_build_based_on_ai_version_id = self.target_ai_data_version.id
        state.index_item_count = index_item_count
        state.last_error = None
        await self._save_state(state)

    async def _clear_cache(self, session: AsyncSession, skip_commit: bool = True):
        statement = delete(GenericSQLDrugSearchCache)
        await session.exec(statement)
        if not skip_commit:
            session.commit()

    async def _count_cache_items(self, session: AsyncSession) -> int:
        query = select(func.count(GenericSQLDrugSearchCache.pzn))
        results = await session.exec(statement=query)
        return results.first()

    async def _build_index(self, session: AsyncSession, skip_commit: bool = True):

        stamm_search_fields = []
        for s_field in DRUG_SEARCHFIELDS:
            stamm_search_fields.append(getattr(Stamm, s_field))
        query_all = (
            select(
                *stamm_search_fields,
                Stamm.ahdatum,
                Stamm.generikakenn,
                Stamm.preisart_neu,
                Stamm.apopflicht,
                Applikationsform.appform.label("appform"),
                Applikationsform.bedeutung.label("appform_bedeutung"),
                Hersteller.herstellercode.label("herstellercode"),
                Hersteller.bedeutung.label("hersteller_bedeutung"),
                Normpackungsgroessen.zuzahlstufe.label(
                    "normpackungsgroeße_zuzahlstufe"
                ),
                Normpackungsgroessen.bedeutung.label("normpackungsgroeße_bedeutung"),
                Darreichungsform.darrform.label("darrform"),
                Darreichungsform.bedeutung.label("darrform_bedeutung"),
            )
            .join(Applikationsform)
            .join(Hersteller)
            .join(Normpackungsgroessen)
            .join(Darreichungsform)
            .where(Stamm.ai_version_id == self.target_ai_data_version.id)
        )

        res = await session.exec(query_all)
        cache_entries: List[GenericSQLDrugSearchCache] = []
        for row in res.all():
            index_content = " ".join(
                [
                    str(getattr(row, attr))
                    for attr in DRUG_SEARCHFIELDS
                    if getattr(row, attr) is not None
                ]
            )
            index_content = f"{index_content} {row.appform_bedeutung} {row.hersteller_bedeutung} {row.normpackungsgroeße_zuzahlstufe} {row.normpackungsgroeße_bedeutung} {row.darrform_bedeutung}"
            cache_entries.append(
                GenericSQLDrugSearchCache(
                    pzn=row.pzn,
                    darrform=row.darrform,
                    appform=row.appform,
                    atc_code=row.atc_code,
                    normpackungsgroeße_zuzahlstufe=row.normpackungsgroeße_zuzahlstufe,
                    packungsgroesse=row.packgroesse,
                    ahdatum=row.ahdatum,
                    generikakenn=row.generikakenn,
                    preisart_neu=row.preisart_neu,
                    apopflicht=row.apopflicht,
                    index_content=index_content,
                )
            )
        session.add_all(cache_entries)
        if not skip_commit:
            await session.commit()
        # print(type(first), dict(zip(res.keys(), first)))

    # async def refresh_index(self, force_rebuild: bool = False):
    #    await self.build_index(force_rebuild=True)

    async def index_ready(self) -> bool:
        state = await self._get_state()
        return (
            not state.index_build_up_in_process
            and state.last_index_build_at is not None
        )

    async def total_item_count(self) -> int:
        # count of all items that are in the index.
        state = await self._get_state()
        return state.index_item_count

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
        only_current_medications: bool = True,
        pagination: PageParams = None,
    ) -> PaginatedResponse[MedLogSearchEngineResult]:
        search_term = (
            search_term.replace("'", '"')
            .replace("`", '"')
            .replace("´", '"')
            .replace("„", '"')
            .replace("“", '"')
            .replace("‘", '"')
        )
        search_term_tokens = shlex.split(search_term)

        # if a name starts with the exact search term we add 1.2 to the score
        # if the drug contains the whole search term cohesive it adds 1.1 to the search score.
        # if it also matches the case it adds 1.0 to the score
        score_cases = case(
            (
                istartswith_op(
                    GenericSQLDrugSearchCache.index_content,
                    search_term.replace('"', ""),
                ),
                1.2,
            ),
            (
                contains_op(
                    GenericSQLDrugSearchCache.index_content,
                    search_term.replace('"', ""),
                ),
                1.1,
            ),
            (
                icontains_op(
                    GenericSQLDrugSearchCache.index_content,
                    search_term.replace('"', ""),
                ),
                1,
            ),
            else_=0,
        )

        for search_token in search_term_tokens:
            # if a drug contains one search token is add 0.1 to the score
            # if matches the case it add 0.2 to the score
            score_cases = score_cases.op("+")(
                case(
                    (
                        contains_op(
                            GenericSQLDrugSearchCache.index_content, search_token
                        ),
                        0.2,
                    ),
                    (
                        icontains_op(
                            GenericSQLDrugSearchCache.index_content, search_token
                        ),
                        0.1,
                    ),
                    else_=0,
                )
            )
        query = select(
            GenericSQLDrugSearchCache.pzn,
            score_cases.label("score"),
        )
        # pzn filter
        if pzn_contains:
            query = query.where(
                contains_op(GenericSQLDrugSearchCache.pzn, pzn_contains)
            )
        # category filters
        if filter_packgroesse:
            query = query.where(
                GenericSQLDrugSearchCache.packungsgroesse == filter_packgroesse
            )
        if filter_darrform:
            query = query.where(GenericSQLDrugSearchCache.darrform == filter_darrform)
        if filter_normpackungsgroeße_zuzahlstufe:
            query = query.where(
                GenericSQLDrugSearchCache.normpackungsgroeße_zuzahlstufe
                == filter_normpackungsgroeße_zuzahlstufe
            )
        if filter_appform:
            query = query.where(GenericSQLDrugSearchCache.appform == filter_appform)
        if filter_atc_level2:
            raise NotImplementedError(
                "Todo: Filtering by ATC Code level2 is not implemted yet"
            )
        if filter_generikakenn:
            query = query.where(
                GenericSQLDrugSearchCache.darrform == filter_generikakenn
            )
        if filter_darrform:
            query = query.where(
                GenericSQLDrugSearchCache.generikakenn == filter_darrform
            )
        if filter_apopflicht:
            query = query.where(
                GenericSQLDrugSearchCache.apopflicht == filter_apopflicht
            )
        if filter_apopflicht:
            query = query.where(
                GenericSQLDrugSearchCache.apopflicht == filter_apopflicht
            )
        if filter_preisart_neu:
            query = query.where(
                GenericSQLDrugSearchCache.preisart_neu == filter_preisart_neu
            )
        if only_current_medications:
            query = query.where(is_(GenericSQLDrugSearchCache.ahdatum, None))
        query = query.where(Column("score") > 0)
        if pagination:
            query = pagination.append_to_query(query, no_limit=True)
        query = query.order_by(desc("score"))

        log.debug(f"SEARCH QUERY: {query}")
        async with get_async_session_context() as session:
            search_res = await session.exec(query)
            pzns_with_score = search_res.all()

            result_count = len(pzns_with_score)
            if pagination.limit:
                pzns_with_score = pzns_with_score[: pagination.limit]
            async with get_stamm_crud_context(session=session) as stamm_crud:
                drugs = await stamm_crud.get_multiple(
                    pzns=[item[0] for item in pzns_with_score], keep_pzn_order=True
                )
                # you are here. check if score makes sense and order by it
                return PaginatedResponse(
                    total_count=result_count,
                    count=len(pzns_with_score),
                    offset=pagination.offset,
                    items=[
                        MedLogSearchEngineResult(
                            pzn=drug.pzn,
                            item=drug,
                            relevance_score=next(
                                item[1]
                                for item in pzns_with_score
                                if item[0] == drug.pzn
                            ),
                        )
                        for drug in drugs
                    ],
                )

    async def _get_state(self) -> GenericSQLDrugSearchState:
        state = None
        async with get_async_session_context() as session:
            query = select(GenericSQLDrugSearchState)
            res = await session.exec(query)
            state = res.one_or_none()
            log.debug(f"SATE:{state}")
        if state is None:
            log.debug("Create new GenericSQLDrugSearchState")
            new_state = GenericSQLDrugSearchState()
            await self._save_state(new_state)
            return new_state
        return state

    async def _save_state(
        self, state: GenericSQLDrugSearchState
    ) -> GenericSQLDrugSearchState:
        async with get_async_session_context() as session:
            session.add(state)
            await session.commit()
            await session.refresh(state)
        return state
