from typing import List, Dict, Optional
from typing_extensions import Unpack
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
from medlogserver.db.drug_data.drug_search._base import (
    MedLogDrugSearchEngineBase,
    MedLogSearchEngineResult,
)
from medlogserver.db._session import AsyncSession


from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.api.paginator import QueryParamsInterface, PaginatedResponse
from medlogserver.model.drug_data.drug import Drug
from medlogserver.db.drug_data.drug import DrugCRUD
from medlogserver.model.drug_data.drug_attr import DrugAttr, DrugRefAttr

from medlogserver.model.drug_data.importers import DRUG_IMPORTERS
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class GenericSQLDrugSearchState(SQLModel, table=True):
    __tablename__ = "drug_search_generic_sql_state"
    dummy_pk: int = Field(default=1, primary_key=True)
    index_build_up_in_process: bool = Field(default=False)
    last_index_build_at: Optional[datetime.datetime] = Field(default=None)
    last_index_build_based_on_drug_datasetversion_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="drug_dataset_version.id"
    )
    index_item_count: Optional[int] = Field(default=False)
    last_error: Optional[str] = Field(default=None)


class GenericSQLDrugSearchCache(SQLModel, table=True):
    __tablename__ = "drug_search_generic_sql_cache"
    __table_args__ = {
        "comment": "Aggregates and indexes drug attributtes for the current drug dataset, for faster search."
    }
    id: uuid.UUID = Field(
        primary_key=True,
        foreign_key="drug.id",
        description="one to one relation to a drug",
    )
    search_index_content: str = Field(
        index=True,
        description="All searchable fields and ref_fields (values and display) aggregated into one indexed string",
    )
    search_cache_codes: str = Field(
        index=True,
        description="All drug codes aggregated into one indexed string",
    )
    market_withdrawal_at: Optional[datetime.date] = Field(default=None)


class GenericSQLDrugSearchEngine(MedLogDrugSearchEngineBase):
    description: str = (
        "'Build-in' search engine. Works with every SQL Database. Does not need any additional setup. Maybe perfoms poor concerning speed and result quality."
    )

    def __init__(
        self,
        target_drug_dataset_version: DrugDataSetVersion,
        engine_config: Dict = None,
    ):
        self.target_drug_dataset_version: DrugDataSetVersion = (
            target_drug_dataset_version
        )
        self.drug_data_importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]

    async def disable(self):
        """If we switch the search engine, we may need to tidy up some thing (e.g. Remove large indexed that are not needed anymore).
        # This func will be called on every MedLog boot for non-enabled search engines.
        """
        # todo: we may want to delete/remove the modules tables (GenericSQLDrugSearchCache, GenericSQLDrugSearchState) here. Will be cleaner but not neccessary.
        pass

    async def build_index(self, force_rebuild: bool = False):
        # tables will be created with build in MedLog/backend/medlogserver/db/_init_db.py -> init_db() we do not need to take care here.
        state = await self._get_state()
        if state.index_build_up_in_process:
            log.warning(
                "Cancel build_index for 'GenericSQLDrugSearchEngine'-Engine because build up is allready in progress"
            )
            return
        if (
            state.last_index_build_based_on_drug_datasetversion_id
            == self.target_drug_dataset_version.id
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
                await session.commit()
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
        state.last_index_build_based_on_drug_datasetversion_id = (
            self.target_drug_dataset_version.id
        )
        state.index_item_count = index_item_count
        state.last_error = None
        await self._save_state(state)

    async def _clear_cache(self, session: AsyncSession, skip_commit: bool = True):
        statement = delete(GenericSQLDrugSearchCache)
        await session.exec(statement)
        if not skip_commit:
            session.commit()

    async def _count_cache_items(self, session: AsyncSession) -> int:
        query = select(func.count(GenericSQLDrugSearchCache.id))
        results = await session.exec(statement=query)
        return results.first()

    async def _build_index(self, session: AsyncSession, skip_commit: bool = True):
        drug_search_attr = []
        # collect all drug attributes definition that are definied "searchable"
        drug_attr_field_defs_all = (
            await self.drug_data_importer_class().get_attr_field_definitions()
        )
        drug_attr_field_names_searchable: List[str] = [
            dd for dd in drug_attr_field_defs_all if dd.searchable == True
        ]

        # collect all drug reference attributes (select/list-of-values) definition that are definied "searchable"
        drug_attr_ref_field_defs_all = (
            await self.drug_data_importer_class().get_ref_attr_field_definitions()
        )
        drug_attr_ref_field_names_searchable: List[str] = [
            drd for drd in drug_attr_ref_field_defs_all if drd.searchable == True
        ]

        # fetch all drugs of the current dataset
        query = select(Drug).where(
            Drug.source_dataset_id == self.target_drug_dataset_version.id
        )
        res = await session.exec(query)
        cache_entries: List[GenericSQLDrugSearchCache] = []
        for drug in res.all():
            field_values_aggregated = drug.trade_name
            for attr in drug.attrs:
                if attr.field_name in drug_attr_field_names_searchable:
                    field_values_aggregated += f" {attr.value}"
            for ref_attr in drug.ref_attrs:
                if attr.field_name in drug_attr_ref_field_names_searchable:
                    field_values_aggregated += (
                        f" {ref_attr.value} {ref_attr.lov_entry.display}"
                    )
            for code in drug.codes:
                field_values_aggregated += f" {code.code}"
            cache_entries.append(
                GenericSQLDrugSearchCache(
                    id=drug.id,
                    search_index_content=field_values_aggregated,
                    search_cache_codes="|".join(
                        [f"{c.code_system_id}:{c.code}" for c in drug.codes]
                    ),
                    market_withdrawal_at=drug.market_withdrawal_at,
                )
            )
        session.add_all(cache_entries)
        if not skip_commit:
            await session.commit()

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
        only_current_medications: bool = False,
        pagination: QueryParamsInterface = None,
        **filter_ref_vals: int | str | bool,
    ) -> PaginatedResponse[MedLogSearchEngineResult]:
        # clean empty string filters
        filter_ref_vals = {
            k: v for k, v in filter_ref_vals.items() if v != "" and v is not None
        }

        search_term = (
            search_term.replace("'", '"')
            .replace("`", '"')
            .replace("´", '"')
            .replace("„", '"')
            .replace("“", '"')
            .replace("‘", '"')
        )
        search_term_tokens = shlex.split(search_term)
        search_term_tokens = [token for token in search_term_tokens if len(token) > 2]

        # if a name starts with the exact search term we add 1.2 to the score
        # if the drug contains the whole search term cohesive it adds 1.1 to the search score.
        # if it also matches the case it adds 1.0 to the score
        score_cases = case(
            (
                istartswith_op(
                    GenericSQLDrugSearchCache.search_index_content,
                    search_term.replace('"', ""),
                ),
                1.2,
            ),
            (
                contains_op(
                    GenericSQLDrugSearchCache.search_index_content,
                    search_term.replace('"', ""),
                ),
                1.1,
            ),
            (
                icontains_op(
                    GenericSQLDrugSearchCache.search_index_content,
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
                            GenericSQLDrugSearchCache.search_index_content, search_token
                        ),
                        0.2,
                    ),
                    (
                        icontains_op(
                            GenericSQLDrugSearchCache.search_index_content, search_token
                        ),
                        0.1,
                    ),
                    else_=0,
                )
            )
        query = select(
            GenericSQLDrugSearchCache.id,
            score_cases.label("score"),
        )
        if filter_ref_vals:
            # Todo: not sure if this will improve speed in any way :D maybe we need extra an chaching table/index for ref values
            query.join(Drug, onclause=GenericSQLDrugSearchCache.id == Drug.id).join(
                DrugRefAttr
            )
            for filter_ref_field_name, filter_rev_value in filter_ref_vals.items():
                query.where(
                    DrugRefAttr.field_name == filter_ref_field_name
                    and DrugRefAttr.value == filter_rev_value
                )
        if only_current_medications:
            query = query.where(
                is_(GenericSQLDrugSearchCache.market_withdrawal_at, None)
                or GenericSQLDrugSearchCache.market_withdrawal_at
                < datetime.date.today()
            )
        query = query.where(Column("score") > 0)
        if pagination:
            query = pagination.append_to_query(
                query, ignore_limit=True, ignore_order_by=True
            )

        query = query.order_by(desc("score"))

        log.debug(f"SEARCH QUERY: {query}")
        async with get_async_session_context() as session:
            search_res = await session.exec(query)
            drug_ids_with_score = search_res.all()

            result_count = len(drug_ids_with_score)
            if pagination.limit:
                drug_ids_with_score = drug_ids_with_score[: pagination.limit]
            async with DrugCRUD.crud_context(session=session) as drug_crud:
                drug_crud: DrugCRUD = drug_crud  # typing hint help

                drugs = await drug_crud.get_multiple(
                    ids=[item[0] for item in drug_ids_with_score], keep_pzn_order=True
                )
                return PaginatedResponse(
                    total_count=result_count,
                    count=len(drug_ids_with_score),
                    offset=pagination.offset,
                    items=[
                        MedLogSearchEngineResult(
                            drug_id=drug.id,
                            item=drug,
                            relevance_score=next(
                                item[1]
                                for item in drug_ids_with_score
                                if item[0] == drug.id
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
