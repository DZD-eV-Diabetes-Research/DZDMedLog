from pathlib import Path
from medlogserver.model.drug_data.importers.wido_gkv_arzneimittelindex import (
    WidoAiImporter,
)


def get_DrugReadApiClasses() -> Dict[str, Type]:
    importer = WidoAiImporter(Path(), "")
    fields = importer.get_attr_field_definitions()


"""
# https://www.getorchestra.io/guides/pydantic-dynamic-model-creation-in-fastapi
def 

DrugApiRead = create_model("DrugRead",)
"""
