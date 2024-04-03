# Apoflicht-Schlüsselverzeichnis
# nicht als extra tabelle im Arzneimittelindex sonder nur aus der Beschreibung/Dokumentation ersichtlich
from typing import List, Self
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.wido_gkv_arzneimittelindex._base import (
    DrugModelTableEnumBase,
)


class ApoPflicht(DrugModelTableEnumBase, table=True):
    __tablename__ = "drug_enum_apoflicht"
    __table_args__ = {"comment": "Apotheken-/Rezeptpflicht"}

    @classmethod
    def get_static_data(self) -> List[Self]:
        return [
            ApoPflicht(apopflicht=0, bedeutung="Nichtarzneimittel"),
            ApoPflicht(
                apopflicht=1, bedeutung="nicht apothekenpflichtiges Arzneimittel"
            ),
            ApoPflicht(
                apopflicht=2,
                bedeutung="apothekenpflichtiges, rezeptfreies Arzneimittel",
            ),
            ApoPflicht(apopflicht=3, bedeutung="rezeptpflichtiges Arzneimittel"),
        ]

    # https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf

    apopflicht: int = Field(
        description="apopflicht id",
        sa_type=SmallInteger,
        primary_key=True,
        schema_extra={"examples": ["0"]},
    )
    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(60),
        schema_extra={"examples": ["Nichtarzneimittel"]},
    )
