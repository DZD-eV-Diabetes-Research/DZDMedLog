# Stammdatei

import uuid
import enum
from textwrap import dedent
from typing import Optional, Dict, Self
from sqlmodel import (
    Field,
    ForeignKeyConstraint,
    Relationship,
    SQLModel,
    Index,
    Constraint,
    CheckConstraint,
)
from sqlalchemy import String, Integer, Column, Boolean, SmallInteger
from pydantic import field_validator
from sqlalchemy import ForeignKey
from medlogserver.db._base_crud import BaseTable
from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase

from medlogserver.model.wido_gkv_arzneimittelindex.applikationsform import (
    Applikationsform,
)
from medlogserver.model.wido_gkv_arzneimittelindex.ai_data_version import (
    AiDataVersion,
)
from medlogserver.model.wido_gkv_arzneimittelindex.darrform import Darreichungsform
from medlogserver.model.wido_gkv_arzneimittelindex.hersteller import Hersteller
from medlogserver.model.wido_gkv_arzneimittelindex.normpackungsgroessen import (
    Normpackungsgroessen,
)
from medlogserver.model.wido_gkv_arzneimittelindex.enum_apopflicht import (
    ApoPflicht,
)
from medlogserver.model.wido_gkv_arzneimittelindex.enum_preisart import Preisart

from medlogserver.model.wido_gkv_arzneimittelindex.enum_generikakenn import (
    Generikakennung,
)

from medlogserver.model.wido_gkv_arzneimittelindex.enum_biosimilar import Biosimilar


DRUG_SEARCHFIELDS = (
    "name",
    "staname",
    "laufnr",
    "atc_code",
    "indgr",
    "pzn",
    "hersteller_code",
    "darrform",
    "packgroesse",
    "dddpk",
)


class StammRoot(DrugModelTableBase, table=False):
    """Root class for drug entries. This is the common base for WiDo Arzneimittelindex drugs and user defined drugs.

    Args:
        DrugModelTableBase (_type_): _description_
        table (bool, optional): _description_. Defaults to False.
    """

    pzn: Optional[str] = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:7"},
        primary_key=False,
        index=True,
        schema_extra={"examples": ["10066230"]},
    )
    name: str = Field(
        description="Präparatename",
        sa_type=String(100),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:8"},
        schema_extra={"examples": ["Venenum Fang 5 mg Kriminon"]},
    )
    hersteller_code: Optional[str] = Field(
        description="Herstellerschlüssel (Siehe `hersteller_ref` für vollen Herstellernamen)",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:9"},
        # We have composite foreign key. see __table_args__ at the top of this class
        # foreign_key="drug_hersteller.herstellercode",
        schema_extra={"examples": ["BEHR"]},
    )
    darrform: str = Field(
        description="Darreichungsformschlüssel (Siehe `darrform_ref` für vollen Namen)",
        sa_type=String(5),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:10"},
        # We have composite foreign key. see __table_args__ at the top of this class
        # foreign_key="drug_darrform.darrform",
        schema_extra={"examples": ["ZKA"]},
    )
    appform: Optional[str] = Field(
        description="Applikationsformschlüssel (Siehe `appform_ref` für vollen Namen)",
        sa_type=String(5),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:24"},
        # We have composite foreign key. see __table_args__ at the top of this class
        # foreign_key="drug_applikationsform.appform",
        schema_extra={"examples": [0]},
    )
    hersteller_code: Optional[str] = Field(
        description="Herstellerschlüssel (Siehe `hersteller_ref` für vollen Herstellernamen)",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:9"},
        # We have composite foreign key. see __table_args__ at the top of this class
        # foreign_key="drug_hersteller.herstellercode",
        schema_extra={"examples": ["BEHR"]},
    )
    atc_code: Optional[str] = Field(
        description="ATC-Code (Klassifikation nach WIdO)",
        sa_type=String(7),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:5"},
        schema_extra={"examples": ["B01AA03"]},
    )
    packgroesse: Optional[int] = Field(
        description="Packungsgröße (in 1/10 Einheiten)",
        sa_type=Integer,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:12"},
        schema_extra={"examples": ["1000"]},
    )


class StammUserCustomBase(StammRoot, table=False):
    __table_args__ = (
        # Index("idx_drug_search", *DRUG_SEARCHFIELDS),
        ForeignKeyConstraint(
            name="composite_foreign_key_appform_custom_drug",
            columns=["appform", "ai_dataversion_id"],
            refcolumns=[
                "drug_applikationsform.appform",
                "drug_applikationsform.ai_dataversion_id",
            ],
        ),
        # Todo: need to find a way to create nullable/optional composite foreign keys. otherwise we will fail inserting stamm entries with e.g. empty appform.
        # Update/Wontfix on this ToDo: sqlite does not support nullable/optional composite foreign keys constraints (google keywords: SIMPLE mode sqlite composite foreign key).
        # As a fix we disable foreign key constraints for sqlite
        # and only enable it via "PRAGMA foreign_keys = ON;" when needed (e.g. On Delete ai_dataversion entry)
        # review later... there may be a better more generic solution
        ForeignKeyConstraint(
            name="composite_foreign_key_hersteller_code_custom_drug",
            columns=["hersteller_code", "ai_dataversion_id"],
            refcolumns=[
                "drug_hersteller.herstellercode",
                "drug_hersteller.ai_dataversion_id",
            ],
        ),
        ForeignKeyConstraint(
            name="composite_foreign_key_darrform_custom_drug",
            columns=["darrform", "ai_dataversion_id"],
            refcolumns=[
                "drug_darrform.darrform",
                "drug_darrform.ai_dataversion_id",
            ],
        ),
    )
    ai_dataversion_id: uuid.UUID = Field(
        description="Foreing key to 'AiDataVersion'. Custom drug still need this to refernce their look-up list like darrform, herstellercode,... which are always thight to a specific ai_data_version.",
        # foreign_key="ai_dataversion.id",
        default=None,
        primary_key=False,
        sa_column_args=[ForeignKey("ai_dataversion.id", ondelete="CASCADE")],
    )


class StammUserCustomCreateAPI(StammRoot, table=False):
    pass


class StammUserCustom(StammUserCustomBase, BaseTable, table=True):
    __tablename__ = "drug_stamm_user_custom"

    created_by_user: uuid.UUID = Field(foreign_key="user.id")
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    ai_version_ref: AiDataVersion = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        }
    )
    darrform_ref: Darreichungsform = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        }
    )
    appform_ref: Optional[Applikationsform] = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        }
    )
    hersteller_ref: Optional[Hersteller] = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        }
    )


class StammUserCustomRead(StammUserCustomBase, table=False):
    id: uuid.UUID = Field()
    ai_version_ref: AiDataVersion
    darrform_ref: Darreichungsform
    appform_ref: Optional[Applikationsform]
    hersteller_ref: Optional[Hersteller]


class StammBase(StammRoot, table=False):

    # https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf

    # On composite foreign keys https://github.com/tiangolo/sqlmodel/issues/222
    __table_args__ = (
        # Index("idx_drug_search", *DRUG_SEARCHFIELDS),
        ForeignKeyConstraint(
            name="composite_foreign_key_appform",
            columns=["appform", "ai_dataversion_id"],
            refcolumns=[
                "drug_applikationsform.appform",
                "drug_applikationsform.ai_dataversion_id",
            ],
        ),
        # Todo: need to find a way to create nullable/optional composite foreign keys. otherwise we will fail inserting stamm entries with e.g. empty appform.
        # Update/Wontfix on this ToDo: sqlite does not support nullable/optional composite foreign keys constraints (google keywords: SIMPLE mode sqlite composite foreign key).
        # As a fix we disable foreign key constraints for sqlite
        # and only enable it via "PRAGMA foreign_keys = ON;" when needed (e.g. On Delete ai_dataversion entry)
        # review later... there may be a better more generic solution
        ForeignKeyConstraint(
            name="composite_foreign_key_hersteller_code",
            columns=["hersteller_code", "ai_dataversion_id"],
            refcolumns=[
                "drug_hersteller.herstellercode",
                "drug_hersteller.ai_dataversion_id",
            ],
        ),
        ForeignKeyConstraint(
            name="composite_foreign_key_darrform",
            columns=["darrform", "ai_dataversion_id"],
            refcolumns=[
                "drug_darrform.darrform",
                "drug_darrform.ai_dataversion_id",
            ],
        ),
        ForeignKeyConstraint(
            name="composite_foreign_key_normpackungsgroessen_zuzahlstufe",
            columns=["zuzahlstufe", "ai_dataversion_id"],
            refcolumns=[
                "drug_normpackungsgroessen.zuzahlstufe",
                "drug_normpackungsgroessen.ai_dataversion_id",
            ],
        ),
    )

    ai_dataversion_id: uuid.UUID = Field(
        description="Foreing key to 'AiDataVersion' ('GKV WiDo Arzneimittel Index' Data Format Version) which contains the information which Arzneimittel Index 'Datenstand' and 'Dateiversion' the row has",
        # foreign_key="ai_dataversion.id",
        default=None,
        primary_key=True,
        sa_column_args=[ForeignKey("ai_dataversion.id", ondelete="CASCADE")],
    )
    pzn: Optional[str] = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:7"},
        primary_key=True,
        index=True,
        schema_extra={"examples": ["10066230"]},
    )
    laufnr: str = Field(
        description="Laufende Nummer (vom WIdO vergeben)",
        sa_type=String(7),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        schema_extra={"examples": ["12903"]},
    )
    stakenn: Optional[str] = Field(
        description="(Sämtliche Arzneimittel eines Handelsnamens)Standardaggregatkennung (zu Lfd. Nr.)",
        sa_type=String(1),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
        schema_extra={"examples": ["1"]},
    )
    staname: str = Field(
        description="Standardaggregatname (vom WIdO vergeben) (enhält *NV* wenn 'Noch nicht abschließend klassifiziertes Arzneimittel')",
        sa_type=String(70),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:4"},
        schema_extra={"examples": ["Warfarin"]},
    )

    indgr: str = Field(
        description="Indikationsgruppe (nach Roter Liste 2014)",
        sa_type=String(2),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:6"},
        schema_extra={"examples": ["20"]},
    )
    #
    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:7"},
        primary_key=True,
        index=True,
        schema_extra={"examples": ["10066230"]},
    )
    hersteller_code: str = Field(
        description="Herstellerschlüssel (Siehe `hersteller_ref` für vollen Herstellernamen)",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:9"},
        # We have composite foreign key. see __table_args__ at the top of this class
        # foreign_key="drug_hersteller.herstellercode",
        schema_extra={"examples": ["BEHR"]},
    )
    zuzahlstufe: Optional[str] = Field(
        description="Normpackungsgrößenschlüssel (Siehe `zuzahlstufe_ref` für vollen Namen)",
        sa_type=String(1),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:11"},
        # We have composite foreign key. see __table_args__ at the top of this class
        # foreign_key="drug_normpackungsgroessen.zuzahlstufe",
        schema_extra={"examples": ["E"]},
    )
    packgroesse: int = Field(
        description="Packungsgröße (in 1/10 Einheiten)",
        sa_type=Integer,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:12"},
        schema_extra={"examples": ["1000"]},
    )
    dddpk: str = Field(
        description="DDD je Packung (nach WIdO, in 1/1000 Einheiten)",
        sa_type=String(9),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:13"},
        schema_extra={"examples": ["000066667"]},
    )
    apopflicht: int = Field(
        description="Apotheken-/Rezeptpflichtschlüssel (Siehe `apopflicht_ref` für vollen Namen)",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:14"},
        foreign_key="drug_enum_apopflicht.apopflicht",
        schema_extra={"examples": ["0"]},
    )

    preisart_alt: Optional[str] = Field(
        description="Preisart, alt schlüssel  (Siehe `preisart_alt_ref` für vollen Namen)",
        sa_type=String(1),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:15"},
        foreign_key="drug_enum_preisart.preisart",
        schema_extra={"examples": ["X"]},
    )
    preisart_neu: Optional[str] = Field(
        description="Preisart, neu schlüssel  (Siehe `preisart_neu_ref` für vollen Namen)",
        sa_type=String(1),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:16"},
        foreign_key="drug_enum_preisart.preisart",
        schema_extra={"examples": ["X"]},
    )
    preis_alt: int = Field(
        description="Preis alt (in Cent)",
        sa_type=Integer(),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:17"},
        schema_extra={"examples": ["1512"]},
    )
    preis_neu: int = Field(
        description="Preis neu (in Cent)",
        sa_type=Integer(),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:18"},
        schema_extra={"examples": ["1515"]},
    )
    festbetrag: int = Field(
        description="Festbetrag (in Cent)",
        sa_type=Integer(),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:19"},
        schema_extra={"examples": ["1514"]},
    )
    marktzugang: Optional[str] = Field(
        description="Datum Marktzugang (JJJJMMTT)",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:20"},
        schema_extra={"examples": ["20140231"]},
    )
    ahdatum: Optional[str] = Field(
        description="Datum Außer Handel (JJJJMMTT)",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:21"},
        schema_extra={"examples": ["20140331"]},
    )

    rueckruf: bool = Field(
        description="Rückruf/zurückgezogen oder zurückgezogen durch Hersteller",
        sa_type=Boolean(),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:22"},
        schema_extra={"examples": [False]},
    )
    generikakenn: int = Field(
        description="Generika-Kennung",
        sa_type=SmallInteger(),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:23"},
        foreign_key="drug_enum_generikakenn.generikakenn",
        schema_extra={"examples": [0]},
    )
    biosimilar: Optional[str] = Field(
        description=dedent(
            """Gentechnologisch bzw. biotechnologisch hergestellte
                Arzneimittel, zu denen Biosimilars zugelassen und im
                deutschen Markt verfügbar sind oder waren"""
        ),
        sa_type=String(1),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:25"},
        foreign_key="drug_enum_biosimilar.biosimilar",
        schema_extra={"examples": ["N"]},
    )
    orphan: bool = Field(
        description="Von der EMA mit Orphan Drug Status zugelassene Arzneimittel (Klassifikation zum Stichtag)",
        sa_type=Boolean(),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:26"},
        schema_extra={"examples": ["false"]},
    )

    @field_validator("apopflicht", "generikakenn", mode="before")
    def transform_str_id_to_int(cls, value) -> int:
        return int(value)

    @field_validator("preisart_neu", "preisart_alt", mode="before")
    def fix_empty_apothekenverkaufspreis_preisart_(cls, value) -> int:
        # ToDo: Tim: Is this correct? After reviewing this i am not sure that it is correct what i did here.
        # review later...
        if value == "" or value is None:
            return "A"
        return value


class Stamm(StammBase, table=True):
    __tablename__ = "drug_stamm"

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "stamm.txt"

    ai_version_ref: AiDataVersion = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        }
    )
    darrform_ref: Darreichungsform = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        }
    )
    appform_ref: Optional[Applikationsform] = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        }
    )
    zuzahlstufe_ref: Normpackungsgroessen = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        }
    )
    hersteller_ref: Hersteller = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        }
    )

    apopflicht_ref: ApoPflicht = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Stamm.apopflicht]",
            "lazy": "joined",
            "viewonly": True,
        },
    )

    preisart_neu_ref: Optional[Preisart] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Stamm.preisart_neu]",
            "lazy": "joined",
            "viewonly": True,
        }
    )
    preisart_alt_ref: Optional[Preisart] = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "foreign_keys": "[Stamm.preisart_alt]",
        }
    )
    biosimilar_ref: Optional[Biosimilar] = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        },
    )
    generikakenn_ref: Generikakennung = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        }
    )


class StammRead(StammBase, table=False):
    ai_version_ref: AiDataVersion
    darrform_ref: Darreichungsform
    appform_ref: Optional[Applikationsform]
    zuzahlstufe_ref: Optional[Normpackungsgroessen]
    hersteller_ref: Hersteller
    apopflicht_ref: ApoPflicht
    preisart_neu_ref: Optional[Preisart]
    preisart_alt_ref: Optional[Preisart]
    biosimilar_ref: Optional[Biosimilar]
    generikakenn_ref: Generikakennung
