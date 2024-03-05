from medlogserver.db.wido_gkv_arzneimittelindex.ai_data_version import (
    AiDataVersionCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.stamm import StammCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.stamm_aenderungen import (
    StammAenderungenCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.sonderbedeutung import (
    SondercodeBedeutungCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.sonder import SondercodesCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.recycle import RecycledPZNCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.priscus2pzn import Priscus2PZNCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.normpackungsgroessen import (
    NormpackungsgroessenCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.hersteller import HerstellerCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.ergaenzung_amtlich import (
    ATCErgaenzungAmtlichCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.darrform import (
    DarreichungsformCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.atc_ai import ATCaiCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.atc_amtlich import ATCAmtlichCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.atc_ai import ATCaiCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.applikationsform import (
    ApplikationsformCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.enum_apofplicht import (
    ApoPflichtCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.enum_biosimilar import (
    BiosimilarCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.enum_generikakenn import (
    GenerikakennungCRUD,
)
from medlogserver.db.wido_gkv_arzneimittelindex.enum_preisart import PreisartCRUD

from medlogserver.model._base_model import MedLogBaseModel, BaseTable


class DrugModelTableBase(MedLogBaseModel, BaseTable):
    pass


# https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf
