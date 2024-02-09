# Amtliche ATC-Klassifikation mit ATC-Code, ATC-Bedeutung
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable


class AmtlicheATCKlassifikation(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "atc-amtlich.txt"
