import type {
    SchemaDrugAttrFieldDefinitionContainer,
    SchemaMedlogserverModelDrugDataApiDrugModelFactoryAttrRefs,
    SchemaMedlogserverModelDrugDataApiDrugModelFactoryAttrsMulti,
    SchemaMedlogserverModelDrugDataApiDrugModelFactoryMultiAttrRefs
} from "#open-fetch-schemas/medlogapi";

type ValueOf<T> = T[keyof T];
type ElementType<T> = T extends readonly (infer U)[] ? U : never;
type ElementUnionOfArrayProps<T> = ElementType<ValueOf<T>>;

export type FieldDefinition = ElementUnionOfArrayProps<SchemaDrugAttrFieldDefinitionContainer>

export function isMultiValueField(fieldDefinition: FieldDefinition, _fields: object): _fields is SchemaMedlogserverModelDrugDataApiDrugModelFactoryAttrsMulti {
    return fieldDefinition.is_multi_val_field && !fieldDefinition.is_reference_list_field;
}

export function isMultiRefField(fieldDefinition: FieldDefinition, _fields: object): _fields is SchemaMedlogserverModelDrugDataApiDrugModelFactoryMultiAttrRefs {
    return fieldDefinition.is_multi_val_field && fieldDefinition.is_reference_list_field;
}

export function isSingleRefField(fieldDefinition: FieldDefinition, _fields: object): _fields is SchemaMedlogserverModelDrugDataApiDrugModelFactoryAttrRefs {
    return !fieldDefinition.is_multi_val_field && fieldDefinition.is_reference_list_field;
}
