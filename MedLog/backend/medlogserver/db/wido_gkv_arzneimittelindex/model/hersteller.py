# Hersteller - Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable


class Hersteller(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "hersteller.txt"
