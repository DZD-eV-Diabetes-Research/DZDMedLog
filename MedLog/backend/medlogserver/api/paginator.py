from typing import Optional, Generic, TypeVar, List, Annotated, Literal, get_args, Type
import inspect
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Query
from sqlmodel import desc
from medlogserver.config import Config
import types

config = Config()

from medlogserver.log import get_logger

log = get_logger()

from medlogserver.db._base_model import BaseModel

ToBePagedModel = TypeVar("ToBePagedModel")


class MetaQueryParamsChangeTypeHintsForOrderBy(type):
    """This metaclass will dynamicly adapt the possible 'order_by' values according to the implented model generic subclass of QueryParamsGeneric.
    Also it is possbile to define 'defaults' with a dict as a class attribute. This will replace the default-defaults given in QueryParamsGeneric
    """

    exclude_from_order_by: List[str] = ["ai_version_id"]

    def __new__(cls, name, bases, attr):
        if attr["__orig_bases__"][0] != Generic[ToBePagedModel]:
            target_model_attributes = list(
                get_args(attr["__orig_bases__"][0])[0].model_fields.keys()
            )
            target_model_attributes = [
                a for a in target_model_attributes if a not in cls.exclude_from_order_by
            ]
            print("-----")
            print("class", attr["__orig_bases__"][0])
            print("target_model_attributes", target_model_attributes)
            print("bases[0]", bases[0])

            # set typing Literal[<>] values for __init__."order_by"
            # bases[0].__init__.__annotations__["order_by"].__dict__[
            #    "__args__"
            # ] = target_model_attributes

            # overwrite default params in __init__ func according to the generic sub model attr 'defaults' .
            new_sub_class = super().__new__(cls, name, bases, attr)
            import copy

            new_sub_class.__init__ = copy.deepcopy(new_sub_class.__init__)
            for index, init_param_name in enumerate(
                list(inspect.signature(bases[0].__init__).parameters.keys())[1:]
            ):

                if "defaults" in attr and init_param_name in attr["defaults"]:
                    # print("SET ", init_param_name, "TO ", attr["defaults"])
                    new_defaults = list(bases[0].__init__.__defaults__)
                    new_defaults[index] = attr["defaults"][init_param_name]
                    bases[0].__init__.__defaults__ = tuple(new_defaults)

            # print("default", bases[0].__init__.__defaults__)

            # print(attr["__init__"])

            print("new_sub_class.__init__", new_sub_class.__init__)
            print("#####")
            new_sub_class.__init__.__annotations__["order_by"] = Literal[
                tuple(target_model_attributes)
            ]
        else:
            new_sub_class = super().__new__(cls, name, bases, attr)
        return new_sub_class


class QueryParamsGeneric(
    Generic[ToBePagedModel], metaclass=MetaQueryParamsChangeTypeHintsForOrderBy
):
    defaults = dict()

    def __init__(
        self,
        offset: Optional[int] = Query(
            default=0, description="Specify the starting point for result sets/list"
        ),
        limit: int = Query(
            default=100,
            description="Specify the max amount of result items",
        ),
        order_by: Literal[
            "Generic",
            "Placeholder",
            "this will be replaced in by the metaclass when subclassing this generic class",
        ] = Query(
            default=None,
            description="Order the result set by this attribute",
        ),
        order_desc: Annotated[
            bool, Query(description="Flip the sorting order")
        ] = False,
    ):
        self.offset = offset
        self.limit = limit
        self.order_by = order_by
        self.order_desc = order_desc

    def order(
        self, items=List[ToBePagedModel], reverse: bool = False
    ) -> List[ToBePagedModel]:
        if self.order_by:
            return sorted(
                items, key=lambda x: getattr(x, self.order_by), reverse=reverse
            )
        else:
            return items

    def append_to_query(self, sqlmodel_query, no_limit: bool = False):
        sqlmodel_query = sqlmodel_query.offset(self.offset)
        if self.limit and not no_limit:
            sqlmodel_query = sqlmodel_query.limit(self.limit)
        if self.order_by:
            order_field = self.order_by
            if self.order_desc:
                order_field = desc(self.order_by)
            sqlmodel_query = sqlmodel_query.order_by(order_field)
        return sqlmodel_query


class PageParams(BaseModel):

    offset: int = Field(
        default=0,
        description="Starting position index of the returned items in the dataset.",
        examples=[200],
    )
    limit: Optional[int] = Field(
        default=100,
        description="Max number if items to be included in the response.",
        examples=[50],
    )
    order_by: Literal["BLA"] = Field(
        default=None, description="The attribute name to order the results by"
    )

    order_desc: Optional[bool] = Field(
        default=False,
        description="If set to True order descending otherwise order result ascending",
    )

    def append_to_query(self, sqlmodel_query, no_limit: bool = True):
        log.warning(f"{PageParams} is deprecated. Switch to QueryParamsGeneric")
        sqlmodel_query = sqlmodel_query.offset(self.offset)
        if self.limit and not no_limit:
            sqlmodel_query = sqlmodel_query.limit(self.limit)
        if self.order_by:
            order_field = self.order_by
            if self.order_desc:
                order_field = desc(self.order_by)
            sqlmodel_query = sqlmodel_query.order_by(order_field)
        return sqlmodel_query


# https://docs.pydantic.dev/latest/concepts/models/#generic-models
class PaginatedResponse(BaseModel, Generic[ToBePagedModel]):
    total_count: Optional[int] = Field(
        default=None,
        description="Total number of items in the database",
        examples=[300],
    )
    offset: Optional[int] = Field(
        default=0,
        description="Starting position index of the returned items in the dataset.",
        examples=[299],
    )
    count: int = Field(
        description="Number of items returned in the response", examples=[1]
    )
    items: List[ToBePagedModel] = Field(
        description="List of items returned in the response following given criteria"
    )


async def pagination_query(
    offset: int = 0,
    limit: int = Query(default=100, le=1000),
    order_by: str = None,
    order_desc: bool = False,
) -> PageParams:
    """Function to be included as a "Depends" in a FastAPi route.

    Args:
        offset (int, optional): _description_. Defaults to 0.
        limit (int, optional): _description_. Defaults to Query(default=100, le=1000).
        order_by (str, optional): _description_. Defaults to None.
        order_desc (bool, optional): _description_. Defaults to False.

    Returns:
        PageParams: _description_
    """
    return PageParams(
        offset=offset, limit=limit, order_by=order_by, order_desc=order_desc
    )


from typing import Callable


def create_query_params_generic_class(
    base_class: BaseModel, default_offset: int = 0, default_limit: int = 100
) -> Type:
    target_model_attributes = tuple(list(base_class.model_fields.keys()))
    init_annotations = {
        "offset": Annotated[
            Optional[int],
            Query(
                description="Specify the starting point for result sets/list",
            ),
        ],
        "limit": Annotated[
            int,
            Query(
                description="Specify the max amount of result items",
            ),
        ],
        "order_by": Annotated[
            Literal[target_model_attributes],
            Query(
                description="Order the result set by this attribute",
            ),
        ],
        "order_desc": Annotated[bool, Query(description="Flip the sorting order")],
    }
    init_default = (default_offset, default_limit, None, False)
    init_func: Callable = lambda self, offset, limit, order_by, order_desc: [
        setattr(self, "offset", offset),
        setattr(self, "limit", limit),
        setattr(self, "order_by", order_by),
        setattr(self, "order_desc", order_desc),
    ]
    init_func.__defaults__ = init_default
    init_func.__annotations__ = init_annotations
    class_attrs = {
        "__init__": init_func,
    }
    return type(f"{base_class.__name__}QueryParams", (), class_attrs)

    def order(self, items=List[base_class], reverse: bool = False) -> List[base_class]:
        if self.order_by:
            return sorted(
                items, key=lambda x: getattr(x, self.order_by), reverse=reverse
            )
        else:
            return items

    def append_to_query(self, sqlmodel_query, no_limit: bool = False):
        sqlmodel_query = sqlmodel_query.offset(self.offset)
        if self.limit and not no_limit:
            sqlmodel_query = sqlmodel_query.limit(self.limit)
        if self.order_by:
            order_field = self.order_by
            if self.order_desc:
                order_field = desc(self.order_by)
            sqlmodel_query = sqlmodel_query.order_by(order_field)
        return sqlmodel_query

    class_attrs = {
        "__init__": init_func,
        "order": order,
        "append_to_query": append_to_query,
    }
    return type(f"{base_class.__name__}QueryParams", (), class_attrs)
