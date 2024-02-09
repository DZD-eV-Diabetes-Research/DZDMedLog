# Recycelte Artikelnummern
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable


class RecycelteArtikelnummern(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "recycle.txt"
