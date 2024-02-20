from typing import List, Dict, Type, Callable
import os
import datetime
import csv

# import dramatiq
import asyncio
import zipfile
from pathlib import Path, PurePath
from dataclasses import dataclass


# internal imports
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.utils import to_path
from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.db.wido_gkv_arzneimittelindex.model import (
    AiDataVersion,
    Applikationsform,
    ATCai,
    ATCAmtlich,
    Darreichungsform,
    ATCErgaenzungAmtlich,
    Hersteller,
    Normpackungsgroessen,
    Priscus2PZN,
    RecycledPZN,
    Sondercodes,
    SondercodeBedeutung,
    StammAenderungen,
    Stamm,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud import (
    AiDataVersionCRUD,
    get_ai_data_version_crud_context,
    get_atc_amtlich_crud_context,
    get_atc_ai_crud_context,
    get_applikationsform_crud_context,
    get_darrform_crud_context,
    get_ergaenzung_amtlich_crud_context,
    get_normpackungsgroessen_crud_context,
    get_priscus2pzn_crud_context,
    get_sonderbedeutungcode_crud_context,
    get_recycle_crud_context,
    get_stamm_aenderungen_crud_context,
    get_hersteller_crud_context,
    get_stamm_crud_context,
    get_sondercode_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase

# TODO: this generated a circular import we need to seperate model and crud classes
# from medlogserver.db.intake_auth import IntakeAuthRefreshTokenCRUD


log = get_logger()
config = Config()

wido_gkv_arzneimittelindex_csv_delimiter: str = ";"
wido_gkv_arzneimittelindex_model_crud_map: Dict[Type[DrugModelTableBase], Callable] = {
    Applikationsform: get_applikationsform_crud_context,
    ATCai: get_atc_ai_crud_context,
    ATCAmtlich: get_atc_amtlich_crud_context,
    Darreichungsform: get_darrform_crud_context,
    ATCErgaenzungAmtlich: get_ergaenzung_amtlich_crud_context,
    Hersteller: get_hersteller_crud_context,
    Normpackungsgroessen: get_normpackungsgroessen_crud_context,
    Priscus2PZN: get_priscus2pzn_crud_context,
    RecycledPZN: get_recycle_crud_context,
    Sondercodes: get_sondercode_crud_context,
    SondercodeBedeutung: get_sonderbedeutungcode_crud_context,
    StammAenderungen: get_stamm_aenderungen_crud_context,
    Stamm: get_stamm_crud_context,
}


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
    crud_context_func: Callable


def _map_filepathes_to_model(source_data_dir: Path | str) -> List[SourceFile2ModelMap]:
    source_data_file_to_model_class_name_map: List = []
    for (
        model_class,
        crud_context_func,
    ) in wido_gkv_arzneimittelindex_model_crud_map.items():
        source_file_name = model_class.get_source_csv_filename()

        source_file_path = to_path(source_data_dir, source_file_name)
        if not source_file_path.exists() or not source_file_path.is_file():
            raise FileNotFoundError(
                f"Source data file '{source_file_name}' not found in {source_data_dir}."
            )
        source_data_file_to_model_class_name_map.append(
            SourceFile2ModelMap(
                model=model_class,
                source_file_path=source_file_path,
                crud_context_func=crud_context_func,
            )
        )
    return source_data_file_to_model_class_name_map


def sniff_arzneimittel_version(testrow: List[str]) -> AiDataVersion:
    async def get_or_create_version_from_db(dateiversion: str, datenstand: str):
        async with get_async_session_context() as session:
            async with get_ai_data_version_crud_context(session) as ai_version_crud:
                crud: AiDataVersionCRUD = ai_version_crud
                existing_version = await crud.get_by_datenstand_and_dateiversion(
                    dateiversion=dateiversion, datenstand=datenstand
                )
                if existing_version:
                    return existing_version

                new_version = AiDataVersion(
                    dateiversion=dateiversion, datenstand=datenstand
                )
                new_version = await crud.create(new_version)
                log.info(f"new_version {type(new_version)} {new_version}")

                return new_version

    ai_data_version = asyncio.run(
        get_or_create_version_from_db(dateiversion=testrow[0], datenstand=testrow[1])
    )
    return ai_data_version


def load_data(source_data_dir: Path | str):
    version = None
    source_data_file_to_model_class_name_map: List[SourceFile2ModelMap] = (
        _map_filepathes_to_model(source_data_dir=source_data_dir)
    )
    for (
        source_data_to_model_entry_container
    ) in source_data_file_to_model_class_name_map:

        file_ai_data_version: AiDataVersion = _load_model(
            datacontainer=source_data_to_model_entry_container
        )
        if version is None:
            version: AiDataVersion = file_ai_data_version
        elif version.id != file_ai_data_version.id:
            raise ValueError(
                "It seems that the import mixes different versions of the GKV Wido Arzneimittelindex. This is not supported"
            )
    asyncio.run(complete_ai_import(version))


def _load_model(datacontainer: SourceFile2ModelMap) -> AiDataVersion:
    parsed_data: List[DrugModelTableBase] = []
    ai_data_version: AiDataVersion = None
    with open(datacontainer.source_file_path, "r") as csvfile:
        reader_variable = csv.reader(
            csvfile, delimiter=wido_gkv_arzneimittelindex_csv_delimiter
        )

        for index, row in enumerate(reader_variable):
            # cast empty row values in python `None` values
            cleaned_row = []
            for cell in row:
                if cell == "":
                    cleaned_row.append(None)
                else:
                    cleaned_row.append(cell)
            row = cleaned_row
            # get arzneimittelindex data version
            if ai_data_version is None:
                ai_data_version = sniff_arzneimittel_version(row)
            row_data: Dict = {"ai_version_id": ai_data_version.id}

            for field_name, field_info in datacontainer.model.model_fields.items():

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
            parsed_data.append(datacontainer.model.model_validate(row_data))

    asyncio.run(
        _write_to_db(parsed_data, crud_context_getter=datacontainer.crud_context_func)
    )
    return ai_data_version


async def _write_to_db(data: List[DrugModelTableBase], crud_context_getter: Callable):
    # https://stackoverflow.com/questions/75150942/how-to-get-a-session-from-async-session-generator-fastapi-sqlalchemy
    # session = await anext(get_async_session())
    async with get_async_session_context() as session:
        async with crud_context_getter(session) as crud:
            crud: DrugCRUDBase = crud
            await crud.create_bulk(objects=data)


def complete_ai_import(version: AiDataVersion) -> AiDataVersion:

    async def set_ai_data_version_completed(ai_version: AiDataVersion):
        async with get_async_session_context() as session:
            async with get_ai_data_version_crud_context(session) as ai_version_crud:
                crud: AiDataVersionCRUD = ai_version_crud
                existing_version = await crud.get_by_datenstand_and_dateiversion(
                    dateiversion=ai_version.dateiversion,
                    datenstand=ai_version.datenstand,
                )
                existing_version.import_completed_at = datetime.datetime.now(
                    datetime.timezone.utc
                )
                existing_version = await crud.update(existing_version)
                log.info(f"Set  {existing_version} as completed.")

                return existing_version

    return set_ai_data_version_completed(version)
