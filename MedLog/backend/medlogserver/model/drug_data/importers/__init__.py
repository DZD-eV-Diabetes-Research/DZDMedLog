from typing import Dict, Type
from medlogserver.model.drug_data.importers._base import DrugDataSetImporterBase
from medlogserver.model.drug_data.importers.wido_gkv_arzneimittelindex import (
    WidoAiImporter52,
)
from medlogserver.model.drug_data.importers.mmi_pharmindex import (
    MmmiPharmaindex1_32,
)

DRUG_IMPORTERS: Dict[str, Type[DrugDataSetImporterBase]] = {
    "WidoGkvArzneimittelindex52": WidoAiImporter52,
    "MmmiPharmaindex1_32": MmmiPharmaindex1_32,
}
