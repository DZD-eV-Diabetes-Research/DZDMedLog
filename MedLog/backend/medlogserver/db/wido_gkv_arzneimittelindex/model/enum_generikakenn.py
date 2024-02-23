# Apoflicht-Schlüsselverzeichnis
# nicht als extra tabelle im Arzneimittelindex sonder nur aus der Beschreibung/Dokumentation ersichtlich
from typing import List, Self

import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import (
    DrugModelTableEnumBase,
)


class Generikakennung(DrugModelTableEnumBase, table=True):
    __tablename__ = "drug_enum_generikakenn"
    __table_args__ = {"comment": "Generikakennung"}

    @classmethod
    def get_static_data(self) -> List[Self]:
        return [
            Generikakennung(
                generikakenn=0, bedeutung="Arzneimittel mit Patent- bzw. Schutzfristen"
            ),
            Generikakennung(generikakenn=1, bedeutung="patentfreies Original"),
            Generikakennung(generikakenn=2, bedeutung="Generikum inkl. Biosimilar"),
            Generikakennung(
                generikakenn=3,
                bedeutung="Sonstige nicht generikafähige Arzneimittel und Arzneimittel außer Handel (seit mehr als 24 Monaten)",
            ),
        ]

    # https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf

    generikakenn: int = Field(
        description="generikakenn id",
        sa_type=SmallInteger,
        primary_key=True,
        schema_extra={"examples": ["0"]},
    )
    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(110),
        schema_extra={"examples": ["Arzneimittel mit Patent- bzw. Schutzfristen"]},
    )
