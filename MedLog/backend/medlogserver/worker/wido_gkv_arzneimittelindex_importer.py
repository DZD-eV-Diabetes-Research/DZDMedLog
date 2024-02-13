from typing import List, Dict, Type
import os
import csv
import dramatiq
import zipfile
from pathlib import Path, PurePath
from dataclasses import dataclass


# internal imports
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.utils import to_path

from medlogserver.db.wido_gkv_arzneimittelindex.model import (
    Applikationsform,
    ATCKlassifikation,
    AmtlicheATCKlassifikation,
    Darreichungsform,
    AbweichungenAmtlicherATC,
    Hersteller,
    Normpackungsgroessen,
    ArzneimittelPriscus2,
    RecycelteArtikelnummern,
    Sondercodes,
    SondercodesTypes,
    StammAenderungen,
    Stammdatei,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase

# TODO: this generated a circular import we need to seperate model and crud classes
# from medlogserver.db.intake_auth import IntakeAuthRefreshTokenCRUD


log = get_logger()
config = Config()

wido_gkv_arzneimittelindex_csv_delimiter: str = ";"
wido_gkv_arzneimittelindex_models: List[str] = [
    Applikationsform,
    ATCKlassifikation,
    AmtlicheATCKlassifikation,
    Darreichungsform,
    AbweichungenAmtlicherATC,
    Hersteller,
    Normpackungsgroessen,
    ArzneimittelPriscus2,
    RecycelteArtikelnummern,
    Sondercodes,
    SondercodesTypes,
    StammAenderungen,
    Stammdatei,
]


def unpack_data(
    source_zip_path: str | Path, extract_to_dir: str | Path = "/tmp/gkv_ai"
) -> str:
    source_zip_path: Path = to_path(source_zip_path)
    extract_to_dir: Path = to_path(extract_to_dir)
    if not source_zip_path.is_file():
        raise ValueError(f"Source zip file does not exist: '{source_zip_path}'")
    extract_to_dir.mkdir(parents=True, exist_ok=True)
    os.StrPath
    with zipfile.ZipFile(source_zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to_dir)
    # select version number dir in extract data
    # there is alway one directory in the Wido GKV Arzneimittelindex zip file
    # this dir containes our target files
    target_dir = list(extract_to_dir.iterdir())[0]
    return str(target_dir)


@dataclass
class SourceFile2ModelMap:
    model: Type[DrugModelTableBase]
    source_file_path: Path


def _map_filepathes_to_model(source_data_dir: Path | str) -> List[SourceFile2ModelMap]:
    source_data_file_to_model_class_name_map: List = []
    for model_class in wido_gkv_arzneimittelindex_models:
        source_file_path = to_path(
            source_data_dir, model_class.gkvai_source_csv_filename
        )
        if not source_file_path.exists() or not source_file_path.is_file():
            raise FileNotFoundError(
                f"Source data file '{model_class.gkvai_source_csv_filename}' not found in {source_data_dir}."
            )
        source_data_file_to_model_class_name_map.append(
            SourceFile2ModelMap(model=model_class, source_file_path=source_file_path)
        )
    return source_data_file_to_model_class_name_map


def load_data(source_data_dir: Path | str):
    source_data_file_to_model_class_name_map: List[SourceFile2ModelMap] = (
        _map_filepathes_to_model(source_data_dir=source_data_dir)
    )
    for source_data_to_model_entry in source_data_file_to_model_class_name_map:
        source_data_to_model_entry.model


def _load_model(model_class: Type[DrugModelTableBase], source_data_csv: Path):
    with open(source_data_csv, "r") as csvfile:
        reader_variable = csv.reader(
            csvfile, delimiter=wido_gkv_arzneimittelindex_csv_delimiter
        )

        for index, row in enumerate(reader_variable):
            row_data: Dict = {}
            for field_name, field_info in model_class.model_fields.items():

                # we misused the sa_column_kwargs.comment attrribute of the field
                # to store the information which column index of the source csv is mapped to this mode field
                # not very elegant but it works for now :)
                # see for gkvai_source_csv_col_index in "MedLog/backend/medlogserver/db/wido_gkv_arzneimittelindex/model/applikationsform.py" for examples.
                source_csv_column_index: int = None
                try:
                    source_csv_column_index = int(
                        getattr(field_info, "sa_column_kwargs", None)["comment"].split(
                            ":"
                        )[1]
                    )
                except TypeError:
                    # there is no gkvai_source_csv_col_index
                    # we can igrnoe this field
                    continue
                if source_csv_column_index is None:
                    continue
                row_data[field_name] = row[source_csv_column_index]

def _write_to_db(data:List[DrugModelTableBase]):

