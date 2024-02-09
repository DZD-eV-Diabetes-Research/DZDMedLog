# Abweichungen amtlicher ATC Code mit DDD
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable


class AbweichungenAmtlicherATC(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "ergaenzung_amtlich.txt"
