// Store to handle the dynamic fields of drugs

import { defineStore } from '#imports'
import { useMedlogapi } from '#open-fetch';
import type { SchemaDrugAttrFieldDefinitionContainer, SchemaDrugCodeSystem } from "#open-fetch-schemas/medlogapi";

interface DrugFieldStore {
    codes: SchemaDrugCodeSystem[]
    fields: SchemaDrugAttrFieldDefinitionContainer
}

export const useDrugFields = defineStore('drugFields', {
    state: (): DrugFieldStore => ({
        codes: [],
        fields: {
            attrs: [],
            attrs_multi: [],
            attrs_ref: [],
            attrs_multi_ref: []
        }
    }),
    actions: {
        async fetchCodes() {
            const { data, error } = await useMedlogapi("/api/drug/code_def");
            if (error.value) {
                throw error.value;
            }

            if (data.value) {
                this.codes = data.value;
            }
        },
        async fetchFields() {
            const { data, error } = await useMedlogapi("/api/drug/field_def");
            if (error.value) {
                throw error.value;
            }

            if (data.value) {
                this.fields = data.value;
            }
        },
    },
    getters: {
        allFields: (state: DrugFieldStore) => {
            return state.fields;
        },
        clientVisibleCodes: (state: DrugFieldStore) => {
            return state.codes.filter((item) => item.client_visible === true);
        },
        fieldsForSearchResults: (state): SchemaDrugAttrFieldDefinitionContainer => {
            return {
                attrs: state.fields.attrs.filter(item => item.show_in_search_results),
                attrs_ref: state.fields.attrs_ref.filter(item => item.show_in_search_results),
                attrs_multi: state.fields.attrs_multi.filter(item => item.show_in_search_results),
                attrs_multi_ref: state.fields.attrs_multi_ref.filter(item => item.show_in_search_results),
            }
        },
        fieldsForCustomDrugs: (state): SchemaDrugAttrFieldDefinitionContainer => {
            return {
                attrs: state.fields.attrs.filter(item => item.used_for_custom_drug),
                attrs_ref: state.fields.attrs_ref.filter(item => item.used_for_custom_drug),
                attrs_multi: state.fields.attrs_multi.filter(item => item.used_for_custom_drug),
                attrs_multi_ref: state.fields.attrs_multi_ref.filter(item => item.used_for_custom_drug),
            }
        },
    }
});
