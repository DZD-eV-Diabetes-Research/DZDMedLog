from typing import List, Dict, Type, Callable, Optional, Annotated
from pydantic import Field
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
from medlogserver.model.wido_gkv_arzneimittelindex import (
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
    Preisart,
    Biosimilar,
    Generikakennung,
    ApoPflicht,
)
from medlogserver.db.wido_gkv_arzneimittelindex import (
    AiDataVersionCRUD,
    ATCAmtlichCRUD,
    ATCaiCRUD,
    ApplikationsformCRUD,
    DarreichungsformCRUD,
    ATCErgaenzungAmtlichCRUD,
    NormpackungsgroessenCRUD,
    Priscus2PZNCRUD,
    SondercodeBedeutungCRUD,
    RecycledPZNCRUD,
    StammAenderungenCRUD,
    HerstellerCRUD,
    StammCRUD,
    SondercodesCRUD,
    PreisartCRUD,
    BiosimilarCRUD,
    GenerikakennungCRUD,
    ApoPflichtCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex._base import DrugCRUDBase

from medlogserver.model.wido_gkv_arzneimittelindex._base import (
    DrugModelTableBase,
    DrugModelTableEnumBase,
)

# TODO: this generated a circular import we need to seperate model and crud classes
# from medlogserver.db.intake_auth import IntakeAuthRefreshTokenCRUD


log = get_logger()
config = Config()

wido_gkv_arzneimittelindex_csv_delimiter: str = ";"
wido_gkv_arzneimittelindex_model_crud_map: Dict[Type[DrugModelTableBase], Callable] = {
    Preisart: PreisartCRUD.crud_context,
    Biosimilar: BiosimilarCRUD.crud_context,
    Generikakennung: GenerikakennungCRUD.crud_context,
    ApoPflicht: ApoPflichtCRUD.crud_context,
    Applikationsform: ApplikationsformCRUD.crud_context,
    ATCai: ATCaiCRUD.crud_context,
    ATCAmtlich: ATCAmtlichCRUD.crud_context,
    Darreichungsform: DarreichungsformCRUD.crud_context,
    ATCErgaenzungAmtlich: ATCErgaenzungAmtlichCRUD.crud_context,
    Hersteller: HerstellerCRUD.crud_context,
    Normpackungsgroessen: NormpackungsgroessenCRUD.crud_context,
    Priscus2PZN: Priscus2PZNCRUD.crud_context,
    RecycledPZN: RecycledPZNCRUD.crud_context,
    Sondercodes: SondercodesCRUD.crud_context,
    SondercodeBedeutung: SondercodeBedeutungCRUD.crud_context,
    StammAenderungen: StammAenderungenCRUD.crud_context,
    Stamm: StammCRUD.crud_context,
}

arzneimittel_index_expected_files: List[str] = [
    "applikationsform.txt",
    "atc-ai.txt",
    "atc-amtlich.txt",
    "darrform.txt",
    "ergaenzung_amtlich.txt",
    "hersteller.txt",
    "normpackungsgroessen.txt",
    "priscus2pzn.txt",
    "recycle.txt",
    "sonder.txt",
    "sonderbedeutung.txt",
    "stamm.txt",
    "stamm_aenderungen.txt",
]


class WiDoArzneimittelImporter:
    def __init__(
        self,
        source_file: Annotated[
            Optional[str],
            Field(
                default=None,
                description="Provide a GKV Arzneimittelindex zip file as provided by WiDo (Wissenschaftlichen Instituts der AOK)",
            ),
        ],
        source_dir: Annotated[
            Optional[str],
            Field(
                default=None,
                description="Provide a directory that contains the extracted content of a GKV Arzneimittelindex zip file as provided by WiDo (Wissenschaftlichen Instituts der AOK)",
            ),
        ],
    ):
        self.file_handler = WiDoArzneimittelSourceFileHandler(
            source_file=source_file, source_dir=source_dir
        )

    def import_arzneimittelindex(
        self, rewrite_existing: bool = False, exist_ok: bool = False
    ):
        arzneimittel_index_content_dir = (
            self.file_handler.handle_arzneimittelindex_source(
                rewrite_existing=rewrite_existing, exist_ok=exist_ok
            )
        )
        # todo: You are here.


class WiDoArzneimittelSourceFileHandler:

    def __init__(
        self,
        source_file: Annotated[
            Optional[str],
            Field(
                default=None,
                description="Provide a GKV Arzneimittelindex zip file as provided by WiDo (Wissenschaftlichen Instituts der AOK)",
            ),
        ],
        source_dir: Annotated[
            Optional[str],
            Field(
                default=None,
                description="Provide a directory that contains the extracted content of a GKV Arzneimittelindex zip file as provided by WiDo (Wissenschaftlichen Instituts der AOK)",
            ),
        ],
    ):
        if (source_dir and source_file) or (not source_dir and not source_file):
            raise ValueError(
                "Provide either source_file or source_dir not both or none."
            )
        if source_dir:
            self.source_dir: Path = Path(source_dir)
            self.source_file = None
        elif source_file:
            self.source_dir = None
            self.source_file: Path = Path(source_file)

    def handle_arzneimittelindex_source(
        self, rewrite_existing: bool = False, exist_ok: bool = False
    ) -> Path:
        """(If nessecary) this method unpack a WiDo GKV Arzneimittelindex zip file.
        It validates the data for existents and non emptiness and
        returns the diectory that contains the actuall Arzneimittelindex payload files.

        Args:
            rewrite_existing (bool, optional): _description_. Defaults to False.
            exist_ok (bool, optional): _description_. Defaults to False.

        Raises:
            ValueError: _description_

        Returns:
            pathlib.Path: the diectory that contains the actuall Arzneimittelindex payload files.
        """
        if self.source_file:
            source_dir = self._unpack_ai_zip(
                rewrite_existing=rewrite_existing, exist_ok=exist_ok
            )
        elif self.source_dir:
            source_dir = self._get_arzneimittelindex_content_dir(self.source_dir)
            if not self._are_unpacked_ai_index_files_existent_and_non_empty(
                self.source_dir
            ):
                raise ValueError(
                    f"WiDo GKV Arzneimittelindex in '{source_dir}' does not contains all exptected files or contains empty(corrupt) files."
                )
        return source_dir

    def _unpack_ai_zip(
        self,
        source_zip_path: str | Path,
        extract_to_dir: str | Path = None,
        rewrite_existing: bool = False,
        exist_ok: bool = False,
    ) -> Path:
        # input validation and normalizing
        if extract_to_dir is None:
            extract_to_dir = to_path(["/tmp/gkv_ai/", source_zip_path.stem])
        else:
            extract_to_dir: Path = to_path(extract_to_dir)
        source_zip_path: Path = to_path(source_zip_path)
        if not source_zip_path.is_file():
            raise ValueError(f"Source zip file does not exist: '{source_zip_path}'")
        # check for existence
        if self._are_unpacked_ai_index_files_existent_and_non_empty(extract_to_dir):
            if not exist_ok:
                raise FileExistsError(
                    f"Target directory ('{extract_to_dir}') to unpack Arzneimittelindex is not empty. Maybe you want to call this function with 'exist_ok' set to true."
                )
            if exist_ok and not rewrite_existing:
                return self._get_arzneimittelindex_content_dir(extract_to_dir)
            elif exist_ok and rewrite_existing:
                # delete existing data
                log.debug(f"Delete data in '{extract_to_dir}'")
                extract_to_dir.unlink()
        # Unzip
        extract_to_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source_zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to_dir)
        return self._get_arzneimittelindex_content_dir(extract_to_dir)

    def _get_arzneimittelindex_content_dir(
        source_path: Path, raise_if_unknown_pattern: bool = False
    ):
        """The actuall content of an unpacked WiDo GKV Arzneimittelindex lies in an extra root directory named after the Arzneimittelindex "datenstand"-version.
        This function tries to return alway the directory that contains the actuall Arzneimittelindex files.

        Args:
            source_path (Path): _description_
        """
        path_objects: List[Path] = list[source_path.iterdir()]
        if len(path_objects) == 1:
            return path_objects[0]
        elif len(path_objects) > 1:
            return source_path
        elif raise_if_unknown_pattern:
            raise ValueError(
                f"Can not determine if '{source_path}' is a directory with a WiDo GKV Arzneimittelindex."
            )
        return source_path

    def _are_unpacked_ai_index_files_existent_and_non_empty(
        self,
        source_path: Path,
    ) -> bool:
        source_path = self._get_arzneimittelindex_content_dir(source_path)
        path_objects: List[Path] = list[source_path.iterdir()]
        existent_files: List[Path] = [f for f in path_objects if f.is_file()]
        for expected_file_name in arzneimittel_index_expected_files:
            expected_and_existent_file: Path = next(
                [f for f in existent_files if f.name == expected_file_name], None
            )
            if expected_and_existent_file is None:
                return False
            elif expected_and_existent_file.stat().st_size == 0:
                return False
        return True


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
    model: Type[DrugModelTableBase | DrugModelTableEnumBase]
    source_file_path: Path
    crud_context_func: Callable


def _map_filepathes_to_model(source_data_dir: Path | str) -> List[SourceFile2ModelMap]:
    source_data_file_to_model_class_name_map: List = []
    for (
        model_class,
        crud_context_func,
    ) in wido_gkv_arzneimittelindex_model_crud_map.items():
        if not model_class.is_enum_table():
            source_file_name = model_class.get_source_csv_filename()

            source_file_path = to_path(source_data_dir, source_file_name)
            if not source_file_path.exists() or not source_file_path.is_file():
                raise FileNotFoundError(
                    f"Source data file '{source_file_name}' not found in {source_data_dir}."
                )
        else:
            source_file_path = None
        source_data_file_to_model_class_name_map.append(
            SourceFile2ModelMap(
                model=model_class,
                source_file_path=source_file_path,
                crud_context_func=crud_context_func,
            )
        )
    return source_data_file_to_model_class_name_map


async def sniff_arzneimittel_version(testrow: List[str]) -> AiDataVersion:
    async def get_or_create_version_from_db(dateiversion: str, datenstand: str):
        async with get_async_session_context() as session:
            async with AiDataVersionCRUD.crud_context(session) as ai_version_crud:
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

    ai_data_version = await get_or_create_version_from_db(
        dateiversion=testrow[0], datenstand=testrow[1]
    )

    return ai_data_version


async def sniff_ai_data_version_from_file(file_path: str) -> AiDataVersion:
    log.debug(f"Sniff ai data version from {Path(file_path).absolute().resolve()}")
    with open(file_path, "r") as csvfile:
        reader_variable = csv.reader(
            csvfile, delimiter=wido_gkv_arzneimittelindex_csv_delimiter
        )

        for index, row in enumerate(reader_variable):
            return AiDataVersion(dateiversion=row[0], datenstand=row[1])


async def get_current_ai_data_version_from_db() -> Optional[AiDataVersion]:
    current_ai_data_version = None
    async with get_async_session_context() as session:
        async with AiDataVersionCRUD.crud_context(session) as ai_data_version_crud:
            current_ai_data_version = await ai_data_version_crud.get_current(
                none_is_ok=True
            )
    return current_ai_data_version


async def load_data(
    source_data_dir: Path | str,
    skip_if_version_is_in_db: bool = True,
):
    current_ai_data_version: AiDataVersion = await get_current_ai_data_version_from_db()
    sniffed_source_file_version = await sniff_ai_data_version_from_file(
        f"{source_data_dir}/stamm.txt"
    )
    if (
        current_ai_data_version is not None
        and sniffed_source_file_version.datenstand <= current_ai_data_version.datenstand
        and skip_if_version_is_in_db
    ):
        log.info(
            f"Skip drug data provisioning. Data with version '{current_ai_data_version}' or a newer version is allready loaded into DB"
        )
        return
    source_data_file_to_model_class_name_map: List[SourceFile2ModelMap] = (
        _map_filepathes_to_model(source_data_dir=source_data_dir)
    )
    for (
        source_data_to_model_entry_container
    ) in source_data_file_to_model_class_name_map:
        if not source_data_to_model_entry_container.model.is_enum_table():
            file_ai_data_version: AiDataVersion = await _load_model(
                datacontainer=source_data_to_model_entry_container
            )
            if (
                sniffed_source_file_version.datenstand
                != file_ai_data_version.datenstand
                or sniffed_source_file_version.dateiversion
                != file_ai_data_version.dateiversion
            ):
                raise ValueError(
                    "It seems that the import mixes different versions of the GKV Wido Arzneimittelindex. This is not supported"
                )
        else:
            await _load_enum_model(source_data_to_model_entry_container)
    await complete_ai_import(file_ai_data_version)


async def _load_enum_model(datacontainer: SourceFile2ModelMap):
    model: DrugModelTableEnumBase = datacontainer.model
    await _write_to_db(
        model.get_static_data(), crud_context_getter=datacontainer.crud_context_func
    )


async def _load_model(datacontainer: SourceFile2ModelMap) -> AiDataVersion:
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
                ai_data_version = await sniff_arzneimittel_version(row)
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

    await _write_to_db(parsed_data, crud_context_getter=datacontainer.crud_context_func)

    return ai_data_version


async def _write_to_db(
    data: List[DrugModelTableBase | DrugModelTableEnumBase],
    crud_context_getter: Callable,
):
    # https://stackoverflow.com/questions/75150942/how-to-get-a-session-from-async-session-generator-fastapi-sqlalchemy
    # session = await anext(get_async_session())
    async with get_async_session_context() as session:
        async with crud_context_getter(session) as crud:
            crud: DrugCRUDBase = crud
            await crud.create_bulk(objects=data)


def complete_ai_import(version: AiDataVersion) -> AiDataVersion:

    async def set_ai_data_version_completed(ai_version: AiDataVersion):
        async with get_async_session_context() as session:
            async with AiDataVersionCRUD.crud_context(session) as ai_version_crud:
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
