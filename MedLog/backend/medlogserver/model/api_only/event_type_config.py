from typing import List

from pydantic import Field

from medlogserver.model._base_model import MedLogBaseApiModel


class EventTypeConfig(MedLogBaseApiModel):
    """The event types an interview can be recorded as (issue #388)."""

    enabled: bool = Field(
        description="Are event types available on this server. If `false`, `event_type_mode` and `event_type` of events must stay `null` and the client should hide all event type inputs."
    )
    event_types: List[str] = Field(
        description="The configured event types, in the configured order.",
        examples=[["on-site visit", "remote interview"]],
    )
