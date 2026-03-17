import type {
    SchemaDrugAttrFieldDefinitionContainer,
    SchemaHttpValidationError,
    SchemaMedlogserverModelDrugDataApiDrugModelFactoryAttrRefs_1,
    SchemaMedlogserverModelDrugDataApiDrugModelFactoryAttrsMulti_1,
    SchemaMultiAttrRefs,
} from "#open-fetch-schemas/medlogapi";
import type { FetchError } from "ofetch";

// use ElementType<ValueOf<T>> to determine the type of items from an array type T
export type ValueOf<T> = T[keyof T];
export type ElementType<T> = T extends readonly (infer U)[] ? U : never;
type ElementUnionOfArrayProps<T> = ElementType<ValueOf<T>>;

export type FieldDefinition = ElementUnionOfArrayProps<SchemaDrugAttrFieldDefinitionContainer>

interface FastAPIError {
    detail: string | { [key: string]: string; };
}

export function isMultiValueField(fieldDefinition: FieldDefinition, _fields: object): _fields is SchemaMedlogserverModelDrugDataApiDrugModelFactoryAttrsMulti_1 {
    return fieldDefinition.is_multi_val_field && !fieldDefinition.is_reference_list_field;
}

export function isMultiRefField(fieldDefinition: FieldDefinition, _fields: object): _fields is SchemaMultiAttrRefs {
    return fieldDefinition.is_multi_val_field && fieldDefinition.is_reference_list_field;
}

export function isSingleRefField(fieldDefinition: FieldDefinition, _fields: object): _fields is SchemaMedlogserverModelDrugDataApiDrugModelFactoryAttrRefs_1 {
    return !fieldDefinition.is_multi_val_field && fieldDefinition.is_reference_list_field;
}

export function isFastAPIError(error: unknown): error is FastAPIError {
    return typeof error === "object" && error !== null && 'detail' in error && !!error.detail;
}

export function isFastAPIValidationError(error: unknown): error is SchemaHttpValidationError {
    if (!isFastAPIError(error)) {
        return false;
    }

    return Array.isArray(error.detail) && error.detail.every(detailObject => {
        return 'loc' in detailObject && Array.isArray(detailObject.loc) &&
            'msg' in detailObject && typeof detailObject.msg === 'string' &&
            'type' in detailObject && typeof detailObject.type === 'string';
    });
}

export function isFetchError(error: unknown): error is FetchError {
    return typeof error === 'object'
        && error !== null
        && 'request' in error
        && 'response' in error
        && 'data' in error;
}
