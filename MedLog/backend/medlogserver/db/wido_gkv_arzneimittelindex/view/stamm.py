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
from medlogserver.db.base import Base, BaseTable
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

log = get_logger()
config = Config()


class StammJoinedView(DrugViewBase):

    async def _generate_rows_match_score(
        self, row: List[Stamm], search_term: str
    ) -> int:
        match_score = 0
        search_words = search_term.split(" ")

        # look up if the complete search term is in the result. this will score the most
        if len(search_words) > 1:
            for field_name in DRUG_SEARCHFIELDS:
                field_val: str = str(getattr(row, field_name))
                term_found: bool = False
                if search_term in field_val:
                    term_found = True
                    match_score += 1.3
                elif search_term.lower() in field_val.lower():
                    term_found = True
                    match_score += 1.2
                if term_found:
                    # if the term comes up often in the drug description we dont want to count it again and again
                    break
        # look up if the single word of the search term are in the result.
        for s_word in search_words:
            word_found: bool = False
            for field_name in DRUG_SEARCHFIELDS:
                field_val: str = str(getattr(row, field_name))
                if s_word in field_val:
                    word_found = True
                    match_score += 1.1
                elif s_word.lower() in field_val.lower():
                    word_found = True
                    match_score += 1.0
            if word_found:
                # if the word comes up often in the drug description we dont want to count it again and again
                continue

        return match_score

    async def _sort_by_generated_match_score(
        self, rows: List[Stamm], search_term: str
    ) -> List[Stamm]:
        rows_with_match_score: List[Tuple[int, Stamm]] = []
        for row in rows:
            rows_with_match_score.append(
                (
                    await self._generate_rows_match_score(row, search_term),
                    row,
                )
            )
        rows_with_match_score
        return [
            r[1]
            for r in sorted(rows_with_match_score, key=lambda x: x[0], reverse=True)
        ]

    async def search(
        self,
        search_term: str,
        current_version_only: bool = True,
        pagination: PageParams = None,
    ) -> Sequence[Stamm]:

        query = (
            select(Stamm)
            .join(Applikationsform)
            .join(Hersteller)
            .join(Normpackungsgroessen)
            .join(Darreichungsform)
        )
        filters: list = []

        search_words = search_term.split(" ")
        for search_word in search_words:
            for field_name in DRUG_SEARCHFIELDS:
                # todo: add joined tables
                filter_ = getattr(Stamm, field_name).icontains(search_word)
                log.debug(f"filter:{filter_}")
                filters.append(filter_)
        query = query.where(or_(*filters))
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(Stamm.ai_version_id == current_ai_version.id)
        if pagination:
            query = pagination.append_to_query(query)
        log.debug(f"Drug Search query: {query}")
        results = await self.session.exec(statement=query)
        return await self._sort_by_generated_match_score(
            results.all(), search_term=search_term
        )


async def get_stamm_joined_view(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[StammJoinedView, None]:
    yield StammJoinedView(session=session)


get_stamm_joined_view_context = contextlib.asynccontextmanager(get_stamm_joined_view)
