from typing import (
    List,
    Optional,
    Sequence,
    Type,
    AsyncGenerator,
    Self,
    TypeVar,
    Generic,
)
from fastapi import Depends
import contextlib
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel import func, select, delete
from uuid import UUID

from medlogserver.db._session import get_async_session
from medlogserver.db.wido_gkv_arzneimittelindex.model._base import (
    DrugModelTableBase,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.ai_data_version import (
    AiDataVersionCRUD,
    get_ai_data_version_crud,
    get_ai_data_version_crud_context,
)
from medlogserver.db.base import BaseModel, BaseTable
from medlogserver.api.paginator import PageParams
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


GenericCRUDTableType = TypeVar("GenericCRUDTableType", bound=BaseTable)
GenericCRUDReadType = TypeVar("GenericCRUDReadType", bound=BaseModel)
GenericCRUDUpdateType = TypeVar("GenericCRUDUpdateType", bound=BaseModel)
GenericCRUDCreateType = TypeVar("GenericCRUDCreateType", bound=BaseModel)


class CRUDBaseMetaClass(type):
    @property
    def crud_context(cls):
        return contextlib.asynccontextmanager(cls.get_crud)


class CRUDBase(
    Generic[
        GenericCRUDTableType,
        GenericCRUDReadType,
        GenericCRUDCreateType,
        GenericCRUDUpdateType,
    ],
    metaclass=CRUDBaseMetaClass,
):
    def __init__(self, session: AsyncSession):
        self.session = session

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.table = cls.get_table_cls()

    @classmethod
    def _get_generics_def(cls):
        for base in cls.__orig_bases__:
            if (
                hasattr(base, "__origin__")
                and base.__origin__ is CRUDBase
                and len(base.__args__) == 4
                and issubclass(base.__args__[0], BaseTable)
            ):
                return base

    @classmethod
    def get_table_cls(cls) -> Type[GenericCRUDTableType]:
        return cls._get_generics_def().__args__[0]

    @classmethod
    def get_read_cls(cls) -> Type[GenericCRUDReadType]:
        return cls._get_generics_def().__args__[1]

    @classmethod
    def get_create_cls(cls) -> Type[GenericCRUDCreateType]:
        return cls._get_generics_def().__args__[2]

    @classmethod
    def get_update_cls(cls) -> Type[GenericCRUDUpdateType]:
        return cls._get_generics_def().__args__[3]

    @classmethod
    async def get_crud(
        cls,
        session: AsyncSession = Depends(get_async_session),
    ) -> AsyncGenerator[Self, None]:
        yield cls(session=session)

    """Moved to metaclass CRUDBaseMetaClass to be an propery. otherwise we had to call "cls.get_crud_context()(session)" which is ugly
    @classmethod
    def get_crud_context(cls):
        return contextlib.asynccontextmanager(cls.get_crud)
    """

    @classmethod
    def get_default_order_by(cls):
        pass

    ################
    # CRUD METHODS #
    ################

    async def count(self) -> int:
        query = select(func.count()).select_from(self.table)
        results = await self.session.exec(statement=query)
        return results.first()

    async def list(
        self, pagination: PageParams = None
    ) -> Sequence[GenericCRUDReadType]:
        query = select(self.get_table_cls())
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        id_: str | UUID,
        raise_exception_if_none: Exception = None,
    ) -> Optional[GenericCRUDReadType]:
        query = select(self.get_table_cls()).where(self.get_table_cls().id == id_)
        results = await self.session.exec(statement=query)
        res = results.one_or_none()
        if res is None and raise_exception_if_none:
            raise raise_exception_if_none
        return res

    async def create(
        self,
        obj: GenericCRUDCreateType,
    ) -> GenericCRUDReadType:
        log.debug(f"Create {self.get_table_cls().__name__}: {obj}")
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(
        self,
        update_obj: GenericCRUDUpdateType,
        id_: str | UUID,
        raise_exception_if_not_exists=None,
    ) -> GenericCRUDReadType:
        event_from_db = await self.get(
            event_id=id_, raise_exception_if_none=raise_exception_if_not_exists
        )
        for k, v in update_obj.model_dump(exclude_unset=True).items():
            if k in self.get_update_cls.model_fields.keys():
                setattr(event_from_db, k, v)
        self.session.add(event_from_db)
        await self.session.commit()
        await self.session.refresh(event_from_db)
        return event_from_db

    async def delete(
        self,
        id_: str | UUID,
        raise_exception_if_not_exists=None,
    ):
        tbl = self.get_table_cls()
        existing_obj_query = select(tbl).where(tbl.id == id_)
        results = await self.session.exec(statement=existing_obj_query)
        existing_obj = results.one_or_none()
        if existing_obj is None and raise_exception_if_not_exists:
            raise raise_exception_if_not_exists
        if existing_obj is not None:
            del_statement = delete(tbl).where(self.tbl.id == id_)
            await self.session.exec(del_statement)
            await self.session.commit()
        return

    async def create_bulk(
        self,
        objects: List[GenericCRUDCreateType],
    ):
        log.debug(f"Create bulk of {self.table.__name__}")
        for obj in objects:
            if not isinstance(obj, self.get_create_cls()):
                raise ValueError(
                    f"List item is not a {self.table.__name__} instance:\n {obj}"
                )
        self.session.add_all(objects)
        await self.session.commit()
