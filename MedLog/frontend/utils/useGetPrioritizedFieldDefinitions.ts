import type { FieldDefinition } from "~/type-helper";
import type { SchemaDisplayPriorityClass, SchemaDrugAttrFieldDefinitionContainer } from "#open-fetch-schemas/medlogapi";

export default function (fieldDefinitions: SchemaDrugAttrFieldDefinitionContainer) {
    const fields: Record<SchemaDisplayPriorityClass, { attributeClass: keyof SchemaDrugAttrFieldDefinitionContainer, fieldDefinition: FieldDefinition }[]> = { 1: [], 2: [], 3: [] };

    // Group field definitions by priority class
    for (const attributeClassString of Object.keys(fieldDefinitions)) {
        const attributeClass = attributeClassString as keyof typeof fieldDefinitions;
        for (const fieldDefinition of fieldDefinitions[attributeClass] as FieldDefinition[]) {
            if (fieldDefinition.field_display_priority_class && Object.keys(fields).includes(String(fieldDefinition.field_display_priority_class))) {
                fields[fieldDefinition.field_display_priority_class].push({ attributeClass, fieldDefinition });
            }
        }
    }

    // Sort within priority classes
    for (const priorityClassArray of Object.values(fields)) {
        priorityClassArray.sort((a, b) => {
            if (a.fieldDefinition.field_display_sort_order == b.fieldDefinition.field_display_sort_order) {
                return 0;
            }

            if (a.fieldDefinition.field_display_sort_order === null) {
                return 1;
            } else if (b.fieldDefinition.field_display_sort_order === null) {
                return -1;
            }

            return a.fieldDefinition.field_display_sort_order - b.fieldDefinition.field_display_sort_order;
        });
    }

    return fields;
}
