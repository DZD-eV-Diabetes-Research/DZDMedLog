# Stammdatei

import uuid
import enum
from textwrap import dedent
from typing import Optional, Dict
from sqlmodel import Field, ForeignKeyConstraint, Relationship, SQLModel, Index
from sqlalchemy import String, Integer, Column, Boolean, SmallInteger

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase

from medlogserver.db.wido_gkv_arzneimittelindex.model.applikationsform import (
    Applikationsform,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.darrform import Darreichungsform
from medlogserver.db.wido_gkv_arzneimittelindex.model.hersteller import Hersteller
from medlogserver.db.wido_gkv_arzneimittelindex.model.normpackungsgroessen import (
    Normpackungsgroessen,
)

# TB: Model Fertig, ungetestet


class ApoPlfichtTypes(enum.Enum):
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


class GenericaKennungTypes(enum.Enum):
    ArzneimittelMitPatentBzwSchutzfristen = 0
    PatentfreiesOriginal = 1
    GenerikumInklBiosimilar = 2
    SonstigeNichtGenerikafähigeArzneimittelUndArzneimittelAusserHandel = 3


class BioSimilarTypes(str, enum.Enum):
    Biosimilar = "B"
    Referenzarzneimittel = "R"
    ArzneimittelUnterDemGleichenATC = "N"


DRUG_SEARCHFIELDS = (
    "laufnr",
    "stakenn",
    "staname",
    "atc_code",
    "indgr",
    "pzn",
    "name",
    "hersteller_code",
    "darrform",
    "zuzahlstufe",
    "packgroesse",
    "dddpk",
    "apopflicht",
    "generikakenn",
    "appform",
)


class StammBase(DrugModelTableBase, table=False):

    # https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf

    laufnr: str = Field(
        description="Laufende Nummer (vom WIdO vergeben)",
        sa_type=String(7),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
    )
    stakenn: Optional[str] = Field(
        description="(Sämtliche Arzneimittel eines Handelsnamens)Standardaggregatkennung (zu Lfd. Nr.)",
        sa_type=String(1),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )
    staname: str = Field(
        description="Standardaggregatname (vom WIdO vergeben) (enhält *NV* wenn 'Noch nicht abschließend klassifiziertes Arzneimittel')",
        sa_type=String(70),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:4"},
    )
    atc_code: Optional[str] = Field(
        description="ATC-Code (Klassifikation nach WIdO)",
        sa_type=String(7),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:5"},
    )
    indgr: str = Field(
        description="Indikationsgruppe (nach Roter Liste 2014)",
        sa_type=String(2),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:6"},
    )
    #
    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:7"},
        primary_key=True,
    )
    name: str = Field(
        description="Präparatename",
        sa_type=String(100),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:8"},
    )
    hersteller_code: str = Field(
        description="Hersteller (siehe Schlüsselverzeichnis hersteller.txt)",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:9"},
        # We have composite foreign key. see __table_args__ at the top of this class
        # foreign_key="drug_hersteller.herstellercode",
    )

    darrform: str = Field(
        description="Darreichungsform(siehe Schlüsselverzeichnis darrform.txt)",
        sa_type=String(5),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:10"},
        # We have composite foreign key. see __table_args__ at the top of this class
        # foreign_key="drug_darrform.darrform",
    )

    zuzahlstufe: Optional[str] = Field(
        description="Normpackungsgröße (siehe Schlüsselverzeichnis norm-packungsgroessen.txt)",
        sa_type=String(1),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:11"},
        # We have composite foreign key. see __table_args__ at the top of this class
        # foreign_key="drug_normpackungsgroessen.zuzahlstufe",
    )
    packgroesse: str = Field(
        description="Packungsgröße (in 1/10 Einheiten)",
        sa_type=String(7),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:12"},
    )
    dddpk: str = Field(
        description="DDD je Packung (nach WIdO, in 1/1000 Einheiten)",
        sa_type=String(9),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:13"},
    )
    apopflicht: ApoPlfichtTypes = Field(
        description="Apotheken-/Rezeptpflicht",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:14"},
    )
    preisart_alt: Optional[PreisartTypes] = Field(
        description="Preisart, alt (Schlüssel PreisartTypes)",
        sa_type=String(1),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:15"},
    )
    preisart_neu: Optional[PreisartTypes] = Field(
        description="Preisart, alt (Schlüssel siehe PreisartTypes)",
        sa_type=String(1),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:16"},
    )
    preis_alt: int = Field(
        description="Preis alt (in Cent)",
        sa_type=Integer(),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:17"},
    )
    preis_neu: int = Field(
        description="Preis neu (in Cent)",
        sa_type=Integer(),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:18"},
    )
    festbetrag: int = Field(
        description="Festbetrag (in Cent)",
        sa_type=Integer(),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:19"},
    )
    marktzugang: Optional[str] = Field(
        description="Datum Marktzugang (JJJJMMTT)",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:20"},
    )
    ahdatum: Optional[str] = Field(
        description="Datum Außer Handel (JJJJMMTT)",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:21"},
    )

    rueckruf: bool = Field(
        description="Rückruf/zurückgezogen oder zurückgezogen durch Hersteller",
        sa_type=Boolean(),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:22"},
    )
    generikakenn: GenericaKennungTypes = Field(
        description="Generika-Kennung",
        sa_type=SmallInteger(),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:23"},
    )
    appform: Optional[str] = Field(
        description="Applikationsform (siehe Schlüsselverzeichnis applikationsform.txt)",
        sa_type=String(5),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:24"},
        # We have composite foreign key. see __table_args__ at the top of this class
        # foreign_key="drug_applikationsform.appform",
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
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:25"},
    )
    orphan: bool = Field(
        description="Von der EMA mit Orphan Drug Status zugelassene Arzneimittel (Klassifikation zum Stichtag)",
        sa_type=Boolean(),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:26"},
    )


class Stamm(StammBase, table=True):
    __tablename__ = "drug_stamm"

    # On composite foreign keys https://github.com/tiangolo/sqlmodel/issues/222
    __table_args__ = (
        Index("idx_drug_search", *DRUG_SEARCHFIELDS),
        ForeignKeyConstraint(
            name="composite_foreign_key_appform",
            columns=["appform", "ai_version_id"],
            refcolumns=[
                "drug_applikationsform.appform",
                "drug_applikationsform.ai_version_id",
            ],
        ),
        ForeignKeyConstraint(
            name="composite_foreign_key_hersteller_code",
            columns=["hersteller_code", "ai_version_id"],
            refcolumns=[
                "drug_hersteller.herstellercode",
                "drug_hersteller.ai_version_id",
            ],
        ),
        ForeignKeyConstraint(
            name="composite_foreign_key_darrform",
            columns=["darrform", "ai_version_id"],
            refcolumns=[
                "drug_darrform.darrform",
                "drug_darrform.ai_version_id",
            ],
        ),
        ForeignKeyConstraint(
            name="composite_foreign_key_zuzahlstufe",
            columns=["zuzahlstufe", "ai_version_id"],
            refcolumns=[
                "drug_normpackungsgroessen.zuzahlstufe",
                "drug_normpackungsgroessen.ai_version_id",
            ],
        ),
    )

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "stamm.txt"

    ai_version_ref: AiDataVersion = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
    darrform_ref: Darreichungsform = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
    appform_ref: Applikationsform = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
    zuzahlstufe_ref: Normpackungsgroessen = Relationship(
        sa_relationship_kwargs={"lazy": "joined"}
    )
    hersteller_ref: Hersteller = Relationship(sa_relationship_kwargs={"lazy": "joined"})


class StammRead(StammBase, table=False):
    ai_version_ref: AiDataVersion
    darrform_ref: Darreichungsform
    appform_ref: Applikationsform
    zuzahlstufe_ref: Optional[Normpackungsgroessen]
    hersteller_ref: Hersteller
