# Apoflicht-Schlüsselverzeichnis
# nicht als extra tabelle im Arzneimittelindex sonder nur aus der Beschreibung/Dokumentation ersichtlich
from typing import List, Self

import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.wido_gkv_arzneimittelindex._base import (
    DrugModelTableEnumBase,
)


class Biosimilar(DrugModelTableEnumBase, table=True):
    __tablename__ = "drug_enum_biosimilar"
    __table_args__ = {"comment": "Biosimilar"}

    @classmethod
    def get_static_data(self) -> List[Self]:
        return [
            Biosimilar(biosimilar="N", bedeutung="Biosimilar"),
            Biosimilar(biosimilar="K", bedeutung="Referenzarzneimittel"),
            Biosimilar(
                biosimilar="X",
                bedeutung="Arzneimittel unter dem gleichen ATC, das weder 'B' noch 'R' ist",
            ),
        ]

    # https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf

    biosimilar: str = Field(
        description="biosimilar id",
        sa_type=String(1),
        primary_key=True,
        schema_extra={"examples": ["N"]},
    )
    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(64),
        schema_extra={"examples": ["Biosimilar"]},
    )
