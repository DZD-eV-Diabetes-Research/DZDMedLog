# Arzneimittel - PRISCUS2 - Datei
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable


class ArzneimittelPriscus2(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "priscus2pzn.txt"
