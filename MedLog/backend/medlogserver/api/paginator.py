from typing import Optional, Generic, TypeVar, List, Annotated, Literal
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Query


ToBePagedModel = TypeVar("ToBePagedModel")


class PageParams(BaseModel, Generic[ToBePagedModel]):

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
    order_by: Literal[ToBePagedModel.model_fields()] = Field(
        default=None, description="The attribute name to order the results by"
    )

    order_desc: Optional[bool] = Field(
        default=False,
        description="If set to True order descending otherwise order result ascending",
    )

    def append_to_query(self, q, no_limit: bool = True):
        q = q.offset(self.offset)
        if self.limit and not no_limit:
            q = q.limit(self.limit)
        return q


# https://docs.pydantic.dev/latest/concepts/models/#generic-models
class PaginatedResponse(BaseModel, Generic[ToBePagedModel]):
    total_count: Optional[int] = Field(
        default=None,
        description="Total number of items in the database",
        examples=[300],
    )
    offset: int = Field(
        description="Starting position index of the returned items in the dataset.",
        examples=[299],
    )
    count: int = Field(
        description="Number of items returned in the response", examples=[1]
    )
    items: List[M] = Field(
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
