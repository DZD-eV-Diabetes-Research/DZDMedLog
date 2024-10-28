from typing import List, Dict, Type, Callable, Optional, Annotated, Generator


import datetime
import csv


import zipfile
from pathlib import Path, PurePath

from medlogserver.worker.task import TaskBase

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


wido_gkv_arzneimittelindex_crud_classes: List[DrugCRUDBase] = [
    PreisartCRUD,
    BiosimilarCRUD,
    GenerikakennungCRUD,
    ApoPflichtCRUD,
    ApplikationsformCRUD,
    ATCaiCRUD,
    ATCAmtlichCRUD,
    DarreichungsformCRUD,
    ATCErgaenzungAmtlichCRUD,
    HerstellerCRUD,
    NormpackungsgroessenCRUD,
    Priscus2PZNCRUD,
    RecycledPZNCRUD,
    SondercodeBedeutungCRUD,
    SondercodesCRUD,
    StammAenderungenCRUD,
    StammCRUD,
]
"""
arzneimittel_index_expected_files = [
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
    "stamm_aenderungen.txt",
    "stamm.txt",
]
"""
arzneimittel_index_expected_files: List[str] = [
    model.get_source_csv_filename()
    for model in [
        model_crud.get_table_cls()
        for model_crud in wido_gkv_arzneimittelindex_crud_classes
    ]
    if hasattr(model, "get_source_csv_filename")
    and model.get_source_csv_filename() is not None
]


class WiDoArzneimittelImporter:

    def __init__(
        self,
        source_dir: Annotated[
            Optional[str],
            "Provide a directory that contains the extracted content of a GKV Arzneimittelindex zip file as provided by WiDo (Wissenschaftlichen Instituts der AOK)",
        ] = None,
    ):
        self.arzneimittel_index_content_dir = source_dir

    async def import_arzneimittelindex(
        self, rewrite_non_complete_existing: bool = True, exist_ok: bool = False
    ) -> AiDataVersion:
        ai_data_version = await self._determine_ai_data_version(
            rewrite_non_complete_existing=rewrite_non_complete_existing,
            exist_ok=exist_ok,
        )

        if ai_data_version.import_completed_at is not None and exist_ok:
            return ai_data_version

        for crud_class in wido_gkv_arzneimittelindex_crud_classes:
            crud_class: DrugCRUDBase = crud_class
            data_model: DrugModelTableBase = crud_class.get_table_cls()
            if data_model.is_enum_table():
                data_model: DrugModelTableEnumBase = data_model
                # Source that does not come from a csv sheet. Some enums are declared in the some Arzneimittelindex manual.
                mapped_data = data_model.get_static_data()
            else:
                raw_data = await self._read_data(crud_class=crud_class)
                mapped_data = await self._load_data(
                    ai_data_version=ai_data_version,
                    csv_data=raw_data,
                    crud=crud_class,
                )
            await self._write_to_db(mapped_data, crud_class)
            await self._mark_import_as_completed(ai_data_version)
        return ai_data_version

    async def _determine_ai_data_version(
        self, rewrite_non_complete_existing: bool = True, exist_ok: bool = False
    ) -> AiDataVersion:
        ai_data_version_from_source_data: AiDataVersion = (
            await self._sniff_ai_data_version_from_file(
                Path(
                    PurePath(
                        self.arzneimittel_index_content_dir,
                        arzneimittel_index_expected_files[0],
                    )
                )
            )
        )
        ai_data_version_from_db: Optional[AiDataVersion] = (
            await self._get_arzneimittelindex_version_from_db(
                ai_data_version_query=ai_data_version_from_source_data
            )
        )
        if ai_data_version_from_db is not None:
            if ai_data_version_from_db.import_completed_at is None:
                if not rewrite_non_complete_existing:
                    raise ValueError(
                        f"WiDo Arneimittelindex with version '{ai_data_version_from_db}' already exists but was not completed successful \
                            (Maybe you want to set 'rewrite_non_complete_existing' to True). Can not import data from '{self.arzneimittel_index_content_dir.absolute()}'."
                    )
                else:
                    log.info(f"Delete old ai_version entry '{ai_data_version_from_db}'")
                    await self._delete_arzneimittelindex_version_from_db(
                        ai_data_version_id=ai_data_version_from_db.id
                    )
            elif exist_ok:
                return ai_data_version_from_db
            elif not exist_ok:
                raise ValueError(
                    f"WiDo Arneimittelindex with version '{ai_data_version_from_db}' already exists. \
                            (Maybe you want to set 'exist_ok' to True). Can not import data from '{self.arzneimittel_index_content_dir.absolute()}'."
                )
        ai_data_version_from_source_data.source_file_path = str(
            self.arzneimittel_index_content_dir
        )
        return await self._write_arzneimittelindex_version_to_db(
            ai_data_version=ai_data_version_from_source_data
        )

    async def _get_arzneimittelindex_version_from_db(
        self, ai_data_version_query: AiDataVersion
    ) -> Optional[AiDataVersion]:
        async with get_async_session_context() as session:
            async with AiDataVersionCRUD.crud_context(session) as ai_version_crud:
                crud: AiDataVersionCRUD = ai_version_crud
                ai_data_version_from_db = await crud.get_by_datenstand_and_dateiversion(
                    datenstand=ai_data_version_query.datenstand,
                    dateiversion=ai_data_version_query.dateiversion,
                )
                return ai_data_version_from_db

    async def _delete_arzneimittelindex_version_from_db(self, ai_data_version_id: str):
        async with get_async_session_context() as session:
            async with AiDataVersionCRUD.crud_context(session) as ai_version_crud:
                crud: AiDataVersionCRUD = ai_version_crud
                await crud.delete(
                    id_=ai_data_version_id, force_pragma_foreign_keys=True
                )

    async def _write_arzneimittelindex_version_to_db(
        self, ai_data_version: AiDataVersion
    ) -> AiDataVersion:
        async with get_async_session_context() as session:
            async with AiDataVersionCRUD.crud_context(session) as ai_version_crud:
                crud: AiDataVersionCRUD = ai_version_crud
                return await crud.create(ai_data_version)

    async def _update_arzneimittelindex_version_to_db(
        self, ai_data_version: AiDataVersion
    ) -> AiDataVersion:
        async with get_async_session_context() as session:
            async with AiDataVersionCRUD.crud_context(session) as ai_version_crud:
                crud: AiDataVersionCRUD = ai_version_crud
                return await crud.update(ai_data_version)

    async def _sniff_ai_data_version_from_file(
        self,
        file_path: str,
    ) -> AiDataVersion:
        log.debug(f"Sniff ai data version from {Path(file_path).absolute().resolve()}")
        with open(file_path, "r", encoding="utf-8") as csvfile:
            reader_variable = csv.reader(
                csvfile, delimiter=wido_gkv_arzneimittelindex_csv_delimiter
            )
            for row in reader_variable:
                return AiDataVersion(dateiversion=row[0], datenstand=row[1])

    async def _mark_import_as_completed(self, ai_data_version: AiDataVersion):
        # refresh from db for good measure
        ai_data_version: AiDataVersion = (
            await self._get_arzneimittelindex_version_from_db(
                ai_data_version_query=ai_data_version
            )
        )
        ai_data_version.import_completed_at = datetime.datetime.now(
            datetime.timezone.utc
        )
        await self._update_arzneimittelindex_version_to_db(
            ai_data_version=ai_data_version
        )

    async def _read_data(self, crud_class: Type[DrugCRUDBase]):

        data_model: DrugModelTableBase = crud_class.get_table_cls()
        file_name = data_model.get_source_csv_filename()
        file_path = Path(PurePath(self.arzneimittel_index_content_dir, file_name))
        with open(file_path, encoding="utf-8") as csvfile:
            csv_reader = csv.reader(
                csvfile, delimiter=wido_gkv_arzneimittelindex_csv_delimiter
            )
            rows: List[List[str]] = []
            for row in csv_reader:
                rows.append(row)
            return rows

    async def _load_data(
        self,
        ai_data_version: AiDataVersion,
        csv_data: List[List[str]],
        crud: DrugCRUDBase,
    ) -> List[DrugModelTableBase]:
        data_model: Type[DrugModelTableBase] = crud.get_create_cls()

        # Extract metadata from model
        field_index_mappings: Dict[int, str] = {}
        for model_field_name, field_info in data_model.model_fields.items():

            # we misused the sa_column_kwargs.comment attrribute of the field
            # to store the information which column index of the source csv is mapped to this mode field
            # not very elegant but it works for now :)
            # see for gkvai_source_csv_col_index in "MedLog/backend/medlogserver/db/wido_gkv_arzneimittelindex/model/applikationsform.py" for examples.
            source_csv_column_index: int = None
            try:
                source_csv_column_index = int(
                    getattr(field_info, "sa_column_kwargs", None)["comment"].split(":")[
                        1
                    ]
                )
            except TypeError:
                # there is no gkvai_source_csv_col_index
                # we can igrnoe this field
                source_csv_column_index = None
            if source_csv_column_index is not None:
                field_index_mappings[source_csv_column_index] = model_field_name

        # Parse source data and map to model
        parsed_and_mapped_data: List[DrugModelTableBase] = []
        for row in csv_data:
            row_data = {"ai_dataversion_id": ai_data_version.id}
            for column_index, model_field_name in field_index_mappings.items():
                cell_value = row[column_index]
                if cell_value == "":
                    cell_value = None
                row_data[model_field_name] = cell_value
            parsed_and_mapped_data.append(data_model.model_validate(row_data))
        return parsed_and_mapped_data

    async def _write_to_db(
        self,
        data: List[DrugModelTableBase | DrugModelTableEnumBase],
        crud_class: DrugCRUDBase,
    ):
        # https://stackoverflow.com/questions/75150942/how-to-get-a-session-from-async-session-generator-fastapi-sqlalchemy
        # session = await anext(get_async_session())
        async with get_async_session_context() as session:
            async with crud_class.crud_context(session) as crud:
                crud: DrugCRUDBase = crud
                await crud.create_bulk(objects=data)


class WiDoArzneimittelSourceFileHandler:

    def __init__(
        self,
        source_file: Annotated[
            Optional[str],
            "Provide a GKV Arzneimittelindex zip file as provided by WiDo (Wissenschaftlichen Instituts der AOK)",
        ] = None,
        source_dir: Annotated[
            Optional[str],
            "Provide a directory that contains the extracted content of a GKV Arzneimittelindex zip file as provided by WiDo (Wissenschaftlichen Instituts der AOK)",
        ] = None,
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
        self, rewrite_existing: bool = True, exist_ok: bool = False
    ) -> Path:
        """This method unpacks a WiDo GKV Arzneimittelindex zip file (if nessecary).
        It validates the data for existents and non emptiness and
        returns the diectory that contains the actuall Arzneimittelindex payload files.

        Args:
            rewrite_non_complete_existing (bool, optional): _description_. Defaults to False.
            exist_ok (bool, optional): _description_. Defaults to False.

        Raises:
            ValueError: _description_

        Returns:
            pathlib.Path: the diectory that contains the actuall Arzneimittelindex payload files.
        """
        if self.source_file:
            source_dir = self._unpack_ai_zip(
                rewrite_non_complete_existing=rewrite_existing,
                exist_ok=exist_ok,
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
        rewrite_non_complete_existing: bool = True,
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
            if exist_ok and not rewrite_non_complete_existing:
                return self._get_arzneimittelindex_content_dir(extract_to_dir)
            elif exist_ok and rewrite_non_complete_existing:
                # delete existing data
                log.debug(f"Delete data in '{extract_to_dir}'")
                extract_to_dir.unlink()
        # Unzip
        extract_to_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source_zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to_dir)
        return self._get_arzneimittelindex_content_dir(extract_to_dir)

    def _get_arzneimittelindex_content_dir(
        self, source_path: Path, raise_if_unknown_pattern: bool = False
    ):
        """The actuall content of an unpacked WiDo GKV Arzneimittelindex lies in an extra root directory named after the Arzneimittelindex "datenstand"-version.
        This function tries to return alway the directory that contains the actuall Arzneimittelindex files.

        Args:
            source_path (Path): _description_
        """
        path_objects: List[Path] = list(source_path.iterdir())
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
        path_objects: List[Path] = list(source_path.iterdir())
        existent_files: List[Path] = [f for f in path_objects if f.is_file()]
        for expected_file_name in arzneimittel_index_expected_files:
            expected_and_existent_file: Path = next(
                (f for f in existent_files if f.name == expected_file_name), None
            )
            if expected_and_existent_file is None:
                return False
            elif expected_and_existent_file.stat().st_size == 0:
                return False
        return True


class TaskImportGKVArnzeimittelIndexData(TaskBase):
    async def work(
        self,
        source_file: Annotated[
            Optional[str],
            "Provide a GKV Arzneimittelindex zip file as provided by WiDo (Wissenschaftlichen Instituts der AOK)",
        ] = None,
        source_dir: Annotated[
            Optional[str],
            "Provide a directory that contains the extracted content of a GKV Arzneimittelindex zip file as provided by WiDo (Wissenschaftlichen Instituts der AOK)",
        ] = None,
        exist_ok: Annotated[
            bool,
            "Do not import if imported successful in the past",
        ] = False,
    ):
        file_handler = WiDoArzneimittelSourceFileHandler(
            source_file=source_file, source_dir=source_dir
        )
        importer = WiDoArzneimittelImporter(
            source_dir=file_handler.handle_arzneimittelindex_source(
                rewrite_existing=False, exist_ok=exist_ok
            ),
        )
        await importer.import_arzneimittelindex(exist_ok=exist_ok)
