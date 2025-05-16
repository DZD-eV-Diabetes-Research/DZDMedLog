from typing import List, Dict, Optional, Literal
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
    or_,
    and_,
)
from sqlalchemy.orm import selectinload
from sqlalchemy import case, func
from medlogserver.db._session import get_async_session_context
from medlogserver.db.drug_data.drug_search._base import (
    MedLogDrugSearchEngineBase,
    MedLogSearchEngineResult,
)
from medlogserver.db._session import AsyncSession

from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.db.drug_data.drug_dataset_version import DrugDataSetVersionCRUD
from medlogserver.api.paginator import QueryParamsInterface, PaginatedResponse
from medlogserver.model.drug_data.drug import DrugData
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
from medlogserver.db.drug_data.drug import DrugCRUD
from medlogserver.model.drug_data.drug_attr import DrugVal, DrugValRef, DrugValMultiRef
from medlogserver.model.drug_data.api_drug_model_factory import drug_to_drugAPI_obj
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.drug_data.drug import DrugAttrTypeName

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
    market_exit_date: Optional[datetime.date] = Field(default=None)
    is_custom_drug: bool = Field(default=False)


class GenericSQLDrugSearchEngine(MedLogDrugSearchEngineBase):
    description: str = (
        "'Build-in' search engine. Works with every SQL Database. Does not need any additional setup. Maybe perfoms poor concerning speed and result quality."
    )

    def __init__(
        self,
        engine_config: Dict = None,
    ):
        self.drug_data_importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]
        self.current_dataset_version: Optional[DrugDataSetVersion] = None
        self.custom_drugs_dataset_version: Optional[DrugDataSetVersion] = None
        self._all_drug_attr_field_definitions: (
            Dict[DrugAttrTypeName, List[DrugAttrFieldDefinition]] | None
        ) = None

    async def disable(self):
        """If we switch the search engine, we may need to tidy up some thing (e.g. Remove large indexed that are not needed anymore).
        # This func will be called on every MedLog boot for non-enabled search engines.
        """
        # todo: we may want to delete/remove the modules tables (GenericSQLDrugSearchCache, GenericSQLDrugSearchState) here. Will be cleaner but not neccessary.
        pass

    async def _get_current_dataset_version(self):
        if self.current_dataset_version is None:
            async with get_async_session_context() as session:
                async with DrugDataSetVersionCRUD.crud_context(
                    session=session
                ) as drug_dataset_crud:
                    drug_dataset_crud: DrugDataSetVersionCRUD = (
                        drug_dataset_crud  # typing hint help
                    )
                    self.current_dataset_version = await drug_dataset_crud.get_current()
        return self.current_dataset_version

    async def _get_custom_drugs_dataset_version(self):
        if self.custom_drugs_dataset_version is None:
            async with get_async_session_context() as session:
                async with DrugDataSetVersionCRUD.crud_context(
                    session=session
                ) as drug_dataset_crud:
                    drug_dataset_crud: DrugDataSetVersionCRUD = (
                        drug_dataset_crud  # typing hint help
                    )
                    self.custom_drugs_dataset_version = (
                        await drug_dataset_crud.get_custom()
                    )

        return self.custom_drugs_dataset_version

    async def build_index(self, force_rebuild: bool = False):
        # tables will be created with build in MedLog/backend/medlogserver/db/_init_db.py -> init_db() we do not need to take care here.
        target_drug_dataset_version = await self._get_current_dataset_version()
        custom_drug_dataset_version = await self._get_custom_drugs_dataset_version()
        state = await self._get_state()
        if state.index_build_up_in_process:
            log.warning(
                "Cancel build_index for 'GenericSQLDrugSearchEngine'-Engine because build up is allready in progress"
            )
            return
        if (
            state.last_index_build_based_on_drug_datasetversion_id
            == target_drug_dataset_version.id
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
                await session.flush()
                await self._build_index(session=session)
                # flush content, so we can count it.
                await session.flush()
                index_item_count = await self._count_cache_items(session=session)
                log.debug(f"Index build up index_item_count: {index_item_count}")
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
        state.last_index_build_at = datetime.datetime.now(
            tz=datetime.timezone.utc
        ).replace(tzinfo=None)
        state.last_index_build_based_on_drug_datasetversion_id = (
            target_drug_dataset_version.id
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

    async def _get_all_drug_attr_definitions_fields(
        self,
    ) -> Dict[
        DrugAttrTypeName,
        List[DrugAttrFieldDefinition],
    ]:
        if self._all_drug_attr_field_definitions is None:
            self._all_drug_attr_field_definitions = (
                await self.drug_data_importer_class().get_all_attr_field_definitions()
            )
        return self._all_drug_attr_field_definitions

    async def _build_index(
        self, session: AsyncSession, skip_commit: bool = True, batch_size: int = 100000
    ):
        """
        Build search index with batch processing to reduce memory consumption.

        Args:
            session: Database session
            skip_commit: Whether to skip final commit
            batch_size: Number of records to process before flushing to database
        """
        target_drug_dataset_version = await self._get_current_dataset_version()
        log.debug(
            f"INDEX BUILD UP target_drug_dataset_version: {target_drug_dataset_version.id} {type(target_drug_dataset_version.id)}"
        )

        custom_drugs_dataset = await self._get_custom_drugs_dataset_version()
        log.debug(
            f"INDEX BUILD UP custom_drugs_dataset: {custom_drugs_dataset.id} {type(custom_drugs_dataset.id)}"
        )

        # Build the base query to fetch drugs
        query = (
            select(DrugData)
            .where(
                or_(
                    DrugData.source_dataset_id == target_drug_dataset_version.id,
                    DrugData.source_dataset_id == custom_drugs_dataset.id,
                )
            )
            .order_by(DrugData.id)
        )
        query = query.options(
            selectinload(DrugData.attrs),
            selectinload(DrugData.attrs_ref).selectinload(DrugValRef.lov_item),
            selectinload(DrugData.attrs_multi),
            selectinload(DrugData.attrs_multi_ref).selectinload(
                DrugValMultiRef.lov_item
            ),
            selectinload(DrugData.codes),
        )

        # Process in batches using offset and limit
        offset = 0
        total_processed = 0

        while True:
            # Fetch batch of drugs
            log.debug(
                f"[INDEX BUILD UP] Fetching next DrugData batch of max size {batch_size}"
            )
            batch_query = query.offset(offset).limit(batch_size)
            res = await session.exec(
                batch_query, execution_options={"populate_existing": True}
            )
            drugs = res.all()

            # Exit loop if no more drugs to process
            if not drugs:
                break
            log.debug(
                f"[INDEX BUILD UP] Fetched next DrugData batch of size {len(drugs)}"
            )

            cache_entries = []
            for drug in drugs:
                cache_entry: GenericSQLDrugSearchCache = await self._drug_to_cache_obj(
                    drug
                )
                cache_entries.append(cache_entry)
            log.debug(
                f"[INDEX BUILD UP] Writing next GenericSQLDrugSearchCache-batch of {len(cache_entries)}"
            )
            # Add batch to session and flush
            session.add_all(cache_entries)
            await session.flush()

            # Clear session to free memory (but maintain transaction)
            session.expunge_all()

            # Update counters
            batch_count = len(drugs)
            total_processed += batch_count
            offset += batch_count

            log.debug(
                f"[INDEX BUILD UP] Processed batch of {batch_count} drugs, total processed: {total_processed}"
            )

    async def _drug_to_cache_obj(self, drug: DrugData) -> GenericSQLDrugSearchCache:
        drug_attr_field_defs_all = await self._get_all_drug_attr_definitions_fields()
        searchable_drug_fields_names_by_type: Dict[
            DrugAttrTypeName,
            List[DrugAttrFieldDefinition],
        ] = {}
        for attr_type_name, field_defintions in drug_attr_field_defs_all.items():
            if attr_type_name == "codes":
                # Drug Codes are handled extra.
                continue
            if attr_type_name not in searchable_drug_fields_names_by_type:
                searchable_drug_fields_names_by_type[attr_type_name] = []
            searchable_drug_fields_names_by_type[attr_type_name] = [
                dd.field_name for dd in field_defintions if dd.searchable == True
            ]
        field_values_aggregated = drug.trade_name
        for attr in drug.attrs:
            if attr.field_name in searchable_drug_fields_names_by_type["attrs"]:
                field_values_aggregated += f" {attr.value}"
        for attr_multi in drug.attrs_multi:
            if (
                attr_multi.field_name
                in searchable_drug_fields_names_by_type["attrs_multi"]
                and attr_multi.value is not None
            ):
                field_values_aggregated += f" {attr_multi.value}"
        for attr_ref in drug.attrs_ref:
            if (
                attr_ref.field_name in searchable_drug_fields_names_by_type["attrs_ref"]
                and attr_ref.value is not None
            ):
                field_values_aggregated += (
                    f" {attr_ref.value} {attr_ref.lov_item.display}"
                )
        for attr_multi_ref in drug.attrs_multi_ref:
            if (
                attr_multi_ref.field_name
                in searchable_drug_fields_names_by_type["attrs_multi_ref"]
                and attr_multi_ref.value is not None
            ):
                field_values_aggregated += (
                    f" {attr_multi_ref.value} {attr_multi_ref.lov_item.display}"
                )
        for code in drug.codes:
            field_values_aggregated += f" {code.code}"
        return GenericSQLDrugSearchCache(
            id=drug.id,
            search_index_content=field_values_aggregated,
            search_cache_codes="|".join(
                [f"{c.code_system_id}:{c.code}" for c in drug.codes]
            ),
            market_exit_date=drug.market_exit_date,
            is_custom_drug=drug.is_custom_drug,
        )

    async def index_ready(self) -> bool:
        state = await self._get_state()
        return (
            not state.index_build_up_in_process
            and state.last_index_build_at is not None
        )

    async def insert_drug_to_index(self, drug: DrugData):
        """Adhoc insert a single drug into the index. this is needed for user defined custom drugs.

        Args:
            drug (Drug): _description_
        """
        cache_entry = await self._drug_to_cache_obj(drug)
        async with get_async_session_context() as session:
            session.add(cache_entry)
            await session.commit()

    async def total_item_count(self) -> int:
        # count of all items that are in the index.
        state = await self._get_state()
        return state.index_item_count

    async def search(
        self,
        search_term: str = None,
        market_accessable: Optional[bool] = None,
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
            query.join(
                DrugData, onclause=GenericSQLDrugSearchCache.id == DrugData.id
            ).join(DrugValRef)
            for filter_ref_field_name, filter_rev_value in filter_ref_vals.items():
                query.where(
                    DrugValRef.field_name == filter_ref_field_name
                    and DrugValRef.value == filter_rev_value
                )
        if market_accessable == True:
            query = query.where(
                or_(
                    is_(GenericSQLDrugSearchCache.market_exit_date, None),
                    GenericSQLDrugSearchCache.market_exit_date > datetime.date.today(),
                )
            )
        if market_accessable == False:
            query = query.where(
                and_(
                    is_not(GenericSQLDrugSearchCache.market_exit_date, None),
                    GenericSQLDrugSearchCache.market_exit_date < datetime.date.today(),
                )
            )
        query = query.where(score_cases > 0)
        if pagination:
            query = pagination.append_to_query(
                query, ignore_limit=True, ignore_order_by=True
            )
        query = query.order_by(GenericSQLDrugSearchCache.is_custom_drug)
        query = query.order_by(desc("score"))

        log.debug(f"DRUG SEARCH QUERY: {query}")
        async with get_async_session_context() as session:
            search_res = await session.exec(query)
            drug_ids_with_score = search_res.all()

            result_count = len(drug_ids_with_score)
            if pagination.limit:
                drug_ids_with_score = drug_ids_with_score[: pagination.limit]
            async with DrugCRUD.crud_context(session=session) as drug_crud:
                drug_crud: DrugCRUD = drug_crud  # typing hint help

                drugs = await drug_crud.get_multiple(
                    ids=[item[0] for item in drug_ids_with_score],
                    keep_result_in_ids_order=True,
                )
                # i do not understand why i need to translate/cast Drug to DrugApiRead object by hand (via drug_to_drugAPI_obj) here because in the "list" endpoint pydantic does it for me... Todo: investigate
                search_result_objs = [
                    MedLogSearchEngineResult(
                        drug_id=drug.id,
                        drug=await drug_to_drugAPI_obj(drug),
                        relevance_score=next(
                            item[1]
                            for item in drug_ids_with_score
                            if item[0] == drug.id
                        ),
                    )
                    for drug in drugs
                ]
                return PaginatedResponse(
                    total_count=result_count,
                    count=len(drug_ids_with_score),
                    offset=pagination.offset,
                    items=search_result_objs,
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
