# Apoflicht-Schlüsselverzeichnis
# nicht als extra tabelle im Arzneimittelindex sonder nur aus der Beschreibung/Dokumentation ersichtlich
from typing import List, Self

import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import (
    DrugModelTableEnumBase,
)


class Preisart(DrugModelTableEnumBase, table=True):
    __tablename__ = "drug_enum_preisart"
    __table_args__ = {"comment": "Preisart"}

    @classmethod
    def get_source_csv_filename(self) -> str:
        return None

    @classmethod
    def get_static_data(self) -> List[Self]:
        return [
            Preisart(preisart="A", bedeutung="Apothekenverkaufspreis"),
            Preisart(preisart="N", bedeutung="Nettopreis"),
            Preisart(preisart="E", bedeutung="Einkaufspreis"),
            Preisart(preisart="K", bedeutung="Krankenhausartikel"),
            Preisart(preisart="X", bedeutung="Ohne Preisangabe"),
        ]

    # https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf

    preisart: str = Field(
        description="preiart id",
        sa_type=String(1),
        primary_key=True,
    )
    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(30),
    )
