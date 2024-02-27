from medlogserver.db.wido_gkv_arzneimittelindex.crud.ai_data_version import (
    AiDataVersionCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.stamm import StammCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.crud.stamm_aenderungen import (
    StammAenderungenCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.sonderbedeutung import (
    SondercodeBedeutungCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.sonder import SondercodesCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.crud.recycle import RecycledPZNCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.crud.priscus2pzn import Priscus2PZNCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.crud.normpackungsgroessen import (
    NormpackungsgroessenCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.hersteller import HerstellerCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.crud.ergaenzung_amtlich import (
    ATCErgaenzungAmtlichCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.darrform import (
    DarreichungsformCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.atc_ai import ATCaiCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.crud.atc_amtlich import ATCAmtlichCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.crud.atc_ai import ATCaiCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.crud.applikationsform import (
    ApplikationsformCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.enum_apofplicht import (
    ApoPflichtCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.enum_biosimilar import (
    BiosimilarCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.enum_generikakenn import (
    GenerikakennungCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.enum_preisart import PreisartCRUD

from medlogserver.db.base import BaseModel, BaseTable


class DrugModelTableBase(BaseModel, BaseTable):
    pass


# https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf
