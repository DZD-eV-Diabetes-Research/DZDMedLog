# Stammdatei

import uuid
import enum
from textwrap import dedent
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, Boolean, SmallInteger

from medlogserver.db.base import Base, BaseTable


# TB: Model Fertig, ungetestet


class ApoplfichtTypes(str, enum.Enum):
    Nichtarzneimittel = 0
    NichtApothekenpflichtigesArzneimittel = 1
    ApothekenpflichtigesRezeptfreiesArzneimittel = 2
    RezeptpflichtigesArzneimittel = 3


class PreisartTypes(str, enum.Enum):
    Apothekenverkaufspreis = None
    Nettopreis = "N"
    Einkaufspreis = "E"
    Krankenhausartikel = "K"
    OhnePreisangabe = "X"


class GenericaKennungTypes(str, enum.Enum):
    ArzneimittelMitPatentBzwSchutzfristen = 0
    PatentfreiesOriginal = 1
    GenerikumInklBiosimilar = 2
    SonstigeNichtGenerikafähigeArzneimittelUndArzneimittelAusserHandel = 3


class BioSimilarTypes(str, enum.Enum):
    Biosimilar = "B"
    Referenzarzneimittel = "R"
    ArzneimittelUnterDemGleichenATC = "N"


class Stammdatei(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "stamm.txt"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    # https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf
    dateiversion: str = Field(
        description="Dateiversion",
        sa_type=String(3),
        schema_extra={
            "gkvai_source_csv_col_index": 0,
        },
    )
    datenstand: str = Field(
        description="Monat Datenstand (JJJJMM)",
        sa_type=String(6),
        schema_extra={"gkvai_source_csv_col_index": 1},
    )
    laufnr: str = Field(
        description="Laufende Nummer (vom WIdO vergeben)",
        sa_type=String(7),
        schema_extra={"gkvai_source_csv_col_index": 2},
    )
    stakenn: str = Field(
        description="(Sämtliche Arzneimittel eines Handelsnamens)Standardaggregatkennung (zu Lfd. Nr.)",
        sa_type=String(1),
        schema_extra={"gkvai_source_csv_col_index": 3},
    )
    staname: str = Field(
        description="Standardaggregatname (vom WIdO vergeben)",
        sa_type=String(70),
        schema_extra={"gkvai_source_csv_col_index": 4},
    )
    atc_code: str = Field(
        description="ATC-Code (Klassifikation nach WIdO)",
        sa_type=String(7),
        schema_extra={"gkvai_source_csv_col_index": 5},
    )
    indgr: str = Field(
        description="Indikationsgruppe (nach Roter Liste 2014)",
        sa_type=String(2),
        schema_extra={"gkvai_source_csv_col_index": 6},
    )
    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        schema_extra={"gkvai_source_csv_col_index": 7},
    )
    name: str = Field(
        description="Präparatename",
        sa_type=String(100),
        schema_extra={"gkvai_source_csv_col_index": 8},
    )
    hersteller_code: str = Field(
        description="Hersteller (siehe Schlüsselverzeichnis hersteller.txt)",
        sa_type=SmallInteger,
        schema_extra={"gkvai_source_csv_col_index": 9},
    )
    darrform: str = Field(
        description="Darreichungsform(siehe Schlüsselverzeichnis darrform.txt)",
        sa_type=SmallInteger,
        schema_extra={"gkvai_source_csv_col_index": 10},
    )
    zuzahlstufe: str = Field(
        description="Normpackungsgröße (siehe Schlüsselverzeichnis norm-packungsgroessen.txt)",
        sa_type=SmallInteger,
        schema_extra={"gkvai_source_csv_col_index": 11},
    )
    packgroesse: str = Field(
        description="Packungsgröße (in 1/10 Einheiten)",
        sa_type=String(7),
        schema_extra={"gkvai_source_csv_col_index": 12},
    )
    dddpk: str = Field(
        description="DDD je Packung (nach WIdO, in 1/1000 Einheiten)",
        sa_type=String(9),
        schema_extra={"gkvai_source_csv_col_index": 13},
    )
    apopflicht: ApoplfichtTypes = Field(
        description="Apotheken-/Rezeptpflicht",
        sa_type=SmallInteger,
        schema_extra={"gkvai_source_csv_col_index": 14},
    )
    preisart_alt: PreisartTypes = Field(
        description="Preisart, alt (Schlüssel siehe nachfolgendes Feld)",
        sa_type=String(1),
        schema_extra={"gkvai_source_csv_col_index": 15},
    )
    preisart_neu: PreisartTypes = Field(
        description="Preisart, alt (Schlüssel siehe nachfolgendes Feld)",
        sa_type=String(1),
        schema_extra={"gkvai_source_csv_col_index": 16},
    )
    preis_alt: str = Field(
        description="Preis alt (in Cent)",
        sa_type=Integer(),
        schema_extra={"gkvai_source_csv_col_index": 17},
    )
    preis_neu: str = Field(
        description="Preis neu (in Cent)",
        sa_type=Integer(),
        schema_extra={"gkvai_source_csv_col_index": 18},
    )
    festbetrag: str = Field(
        description="Festbetrag (in Cent)",
        sa_type=Integer(),
        schema_extra={"gkvai_source_csv_col_index": 19},
    )
    marktzugang: str = Field(
        description="Datum Marktzugang (JJJJMMTT)",
        sa_type=String(8),
        schema_extra={"gkvai_source_csv_col_index": 20},
    )
    ahdatum: str = Field(
        description="Datum Außer Handel (JJJJMMTT)",
        sa_type=String(8),
        schema_extra={"gkvai_source_csv_col_index": 21},
    )

    rueckruf: bool = Field(
        description="Rückruf/zurückgezogen oder zurückgezogen durch Hersteller",
        sa_type=Boolean(),
        schema_extra={"gkvai_source_csv_col_index": 22},
    )
    generikakenn: PreisartTypes = Field(
        description="Generika-Kennung",
        sa_type=SmallInteger(),
        schema_extra={"gkvai_source_csv_col_index": 23},
    )
    appform: int = Field(
        description="Applikationsform (siehe Schlüsselverzeichnis applikationsform.txt)",
        sa_type=SmallInteger(),
        schema_extra={"gkvai_source_csv_col_index": 24},
    )
    biosimilar: Optional[BioSimilarTypes] = Field(
        description=dedent(
            """Gentechnologisch bzw. biotechnologisch hergestellte
                Arzneimittel, zu denen Biosimilars zugelassen und im
                deutschen Markt verfügbar sind oder waren
                'B' -Biosimilar
                'R' - Referenzarzneimittel
                'N' - Arzneimittel unter dem gleichen ATC, das weder 'B'
                noch 'R' ist
                Für alle weiteren Arzneimittel ist dieses Feld nicht ge-
                füllt (NULL)"""
        ),
        sa_type=String(1),
        schema_extra={"gkvai_source_csv_col_index": 25},
    )
    orphan: bool = Field(
        description="Von der EMA mit Orphan Drug Status zugelassene Arz-neimittel (Klassifikation zum Stichtag)",
        sa_type=Boolean(),
        schema_extra={"gkvai_source_csv_col_index": 26},
    )
