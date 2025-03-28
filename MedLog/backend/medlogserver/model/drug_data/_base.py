from typing import List, Self
from sqlmodel import Field, String, UUID, Relationship
from pydantic import field_validator, model_validator
from sqlalchemy.orm import backref, mapped_column
from sqlalchemy import UUID, ForeignKey, Column
from medlogserver.model._base_model import MedLogBaseModel, BaseTable, TimestampModel


class DrugModelTableBase(MedLogBaseModel, BaseTable):
    pass
