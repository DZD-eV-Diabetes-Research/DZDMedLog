# Applikationsform-Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable


class Applikationsform(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "applikationsform.txt"
