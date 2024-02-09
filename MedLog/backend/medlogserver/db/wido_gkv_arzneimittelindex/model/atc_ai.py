# ATC-Klassifikation des GKV-Arzneimittelindex mit ATC-Code, ATC - Bedeutung

import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable


class ATCKlassifikation(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "atc-ai.txt"
