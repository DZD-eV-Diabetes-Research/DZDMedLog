from typing import List, Optional, Sequence, Type, AsyncGenerator, Self
from fastapi import Depends
import contextlib
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel import func, select
from uuid import UUID

from sqlalchemy.inspection import inspect as sqlinspect
from medlogserver.model.wido_gkv_arzneimittelindex._base import (
    DrugModelTableBase,
    DrugModelTableEnumBase,
)
from medlogserver.model.wido_gkv_arzneimittelindex.ai_data_version import (
    AiDataVersion,
)

from medlogserver.db._base_crud import (
    CRUDBaseMetaClass,
    CRUDBase,
    create_crud_base,
    GenericCRUDTableType,
    GenericCRUDReadType,
    GenericCRUDCreateType,
    GenericCRUDUpdateType,
)
from medlogserver.db.wido_gkv_arzneimittelindex.ai_data_version import (
    AiDataVersionCRUD,
)

from medlogserver.api.paginator import QueryParamsInterface
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class DrugCRUDBase(
    CRUDBase[
        GenericCRUDTableType,
        GenericCRUDReadType,
        GenericCRUDCreateType,
        GenericCRUDUpdateType,
    ]
):
    # _is_ai_versionless_table_: bool = False

    def __init__(self, session: AsyncSession):
        self.session = session
        self._current_ai_version: AiDataVersion = None
        self._is_ai_versionless_table_: bool = False

    @property
    def table(self):
        return self.get_table_cls()

    @classmethod
    def _get_generics_def(cls):
        for base in cls.__orig_bases__:
            if (
                hasattr(base, "__origin__")
                and base.__origin__ is DrugCRUDBase
                and len(base.__args__) == 4
            ):
                if issubclass(
                    base.__args__[0], (DrugModelTableEnumBase, DrugModelTableBase)
                ):
                    return base

    async def _get_current_ai_version(
        self,
    ) -> AiDataVersion:
        if self._is_ai_versionless_table_:
            raise ValueError("Does not make any sense. Remove this tim")
        if self._current_ai_version is None:
            async with AiDataVersionCRUD.crud_context(self.session) as ai_version_crud:
                ai_version_crud: AiDataVersionCRUD = ai_version_crud
                self._current_ai_version = await ai_version_crud.get_current()

        return self._current_ai_version

    def _get_primary_key(self):
        tbl_class = self.get_table_cls()
        pks = []
        for pk in sqlinspect(tbl_class).primary_key:
            if pk.name != "ai_version_id":
                pks.append(pk.name)
        if len(pks) == 1:
            return pks[0]
        raise KeyError(f"Primary Key for {tbl_class.__name__} not unambiguous: {pks}")

    async def count(self, current_version_only: bool = True) -> int:
        table = self.get_table_cls()
        query = select(func.count()).select_from(table)
        if not self._is_ai_versionless_table_ and current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(table.ai_version_id == current_ai_version.id)
        results = await self.session.exec(statement=query)
        return results.first()

    async def list(
        self, current_version_only: bool = True, pagination: QueryParamsInterface = None
    ) -> Sequence[GenericCRUDReadType]:
        query = select(self.table)
        if not self._is_ai_versionless_table_ and current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(self.table.ai_version_id == current_ai_version.id)
        if pagination:
            query = pagination.append_to_query(query)
        print("###QUERY", query)
        results = await self.session.exec(statement=query)
        res = results.all()
        print("results.all()", res)
        return res

    async def get(
        self,
        key: str,
        ai_version_id: UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[GenericCRUDReadType]:
        tbl_class = self.get_table_cls()
        if ai_version_id is None and not self._is_ai_versionless_table_:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id
        pk = self._get_primary_key()
        query = select(tbl_class).where(getattr(tbl_class, pk) == key)
        if not self._is_ai_versionless_table_:
            query = query.where(tbl_class.ai_version_id == ai_version_id)

        results = await self.session.exec(statement=query)
        appform: GenericCRUDReadType | None = results.one_or_none()
        if appform is None and raise_exception_if_none:
            raise raise_exception_if_none
        return appform

    async def create(
        self,
        create_obj: GenericCRUDCreateType,
        raise_custom_exception_if_exists: Exception = None,
    ) -> GenericCRUDReadType:
        table = self.get_table_cls()
        pk = self._get_primary_key()
        current_ai_data_version = None
        if not self._is_ai_versionless_table_:
            current_ai_data_version = self._get_current_ai_version()
        log.debug(f"Create {table.__name__}: {create_obj}")
        query_existing = select(table).where(
            getattr(table, pk) == getattr(create_obj, pk)
        )
        if not self._is_ai_versionless_table_:
            query_existing = query_existing.where(
                create_obj.ai_version_id == current_ai_data_version.ai_version_id
            )
        res = await self.session.exec(query_existing)
        existing_obj = res.one_or_none()
        if existing_obj:
            if raise_custom_exception_if_exists:
                raise raise_custom_exception_if_exists
            return existing_obj
        self.session.add(create_obj)
        await self.session.commit()
        await self.session.refresh(create_obj)
        return create_obj

    async def create_bulk(self, objects: List[GenericCRUDCreateType]):
        tbl_class = self.get_table_cls()
        log.info(f"Create bulk of {tbl_class.__name__} (Count: {len(objects)})...")
        for obj in objects:
            if not isinstance(obj, self.get_create_cls()):
                raise ValueError(
                    f"List item is not a '{self.get_create_cls().__name__}' instance: Expected {self.get_create_cls()} got {type(obj)}\n {obj}"
                )
        self.session.add_all(objects)
        await self.session.commit()


def create_drug_crud_base(
    table_model,
    read_model,
    create_model,
    update_model,
    ai_versionless_table_: bool = False,
) -> Type[DrugCRUDBase]:
    drug_base_class = DrugCRUDBase[table_model, read_model, create_model, update_model]
    drug_base_class._is_ai_versionless_table_ = ai_versionless_table_
    return drug_base_class
