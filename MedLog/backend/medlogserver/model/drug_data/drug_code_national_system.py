from typing import List, Self
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.drug_data._base import (
    DrugModelTableEnumBase,
)


class DrugCodeNationalSystem(DrugModelTableEnumBase, table=True):
    __tablename__ = "drug_national_code_system"
    __table_args__ = {"comment": "A list of national pharmaceutical product indexes. To be completed..."}

    @classmethod
    def get_static_data(self) -> List[Self]:
        return [
            DrugCodeNationalSystem(id="PZN", name="Pharmazentralnummer",country="Germany"),
            DrugCodeNationalSystem(id="NDC", name="National Drug Code",country="US"),
            DrugCodeNationalSystem(id="DIN", name="Drug Identification Number",country="Canada"),
            DrugCodeNationalSystem(id="ARTG", name="Australian Register of Therapeutic Goods",country="Australia"),
            DrugCodeNationalSystem(id="YJ", name="YJ Code",country="Japan"),
            DrugCodeNationalSystem(id="CIS", name="Code Identifiant de Spécialité",country="France"),
            DrugCodeNationalSystem(id="EUPC", name="EU Product Code",country="European Union"),
            DrugCodeNationalSystem(id="AIPS", name=" Authentic Information on Pharmaceutical Specialties",country="Switzerland"),
        ]

    id: str = Field(
        description="Shortname identifier for the national mmedication code system. Also the name for one code instance.",
        sa_type=String,
        primary_key=True,
        schema_extra={"examples": ["PZN","NDC"]},
    )
    name: str = Field(        
        description="Longname identifier for the national drug code system.",
        sa_type=String,
        schema_extra={"examples": ["Pharmazentralnummer","National Drug Code"]})
    country: str = Field(
        description="Country that uses this system",
        sa_type=String,
        schema_extra={"examples": ["Germany","USA"]},
    )
