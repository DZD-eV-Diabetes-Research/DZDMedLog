from typing import Dict, Type
from medlogserver.db.drug_data.drug_search._base import MedLogDrugSearchEngineBase
from medlogserver.db.drug_data.drug_search.search_module_generic_sql import (
    GenericSQLDrugSearchCache,
)

SEARCH_ENGINES: Dict[str, Type[MedLogDrugSearchEngineBase]] = {
    "GenericSQLDrugSearch": GenericSQLDrugSearchCache
}
