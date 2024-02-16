from medlogserver.db.wido_gkv_arzneimittelindex.crud.ai_data_version import (
    AiDataVersionCRUD,
    get_ai_data_version_crud,
    get_ai_data_version_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.stamm import (
    StammCRUD,
    get_stamm_crud_context,
    get_stamm_crud,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.stamm_aenderungen import (
    StammAenderungenCRUD,
    get_stamm_aenderungen_crud,
    get_stamm_aenderungen_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.sonderbedeutung import (
    SondercodeBedeutungCRUD,
    get_sonderbedeutungcode_crud,
    get_sonderbedeutungcode_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.sonder import (
    SondercodesCRUD,
    get_sondercode_crud,
    get_sondercode_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.recycle import (
    RecycledPZNCRUD,
    get_recycle_crud,
    get_recycle_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.priscus2pzn import (
    Priscus2PZNCRUD,
    get_priscus2pzn_crud,
    get_priscus2pzn_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.normpackungsgroessen import (
    NormpackungsgroessenCRUD,
    get_normpackungsgroessen_crud,
    get_normpackungsgroessen_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.hersteller import (
    HerstellerCRUD,
    get_hersteller_crud,
    get_hersteller_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.ergaenzung_amtlich import (
    ATCErgaenzungAmtlichCRUD,
    get_ergaenzung_amtlich_crud,
    get_ergaenzung_amtlich_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.darrform import (
    DarreichungsformCRUD,
    get_darrform_crud,
    get_darrform_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.atc_ai import (
    ATCaiCRUD,
    get_atc_ai_crud,
    get_atc_ai_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.atc_amtlich import (
    ATCAmtlichCRUD,
    get_atc_amtlich_crud,
    get_atc_amtlich_crud_context,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.atc_ai import ATCaiCRUD
from medlogserver.db.wido_gkv_arzneimittelindex.crud.applikationsform import (
    ApplikationsformCRUD,
    get_applikationsform_crud,
    get_applikationsform_crud_context,
)
from medlogserver.db.base import Base, BaseTable


class DrugModelTableBase(Base, BaseTable):
    pass


# https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf
