// Store to handle the dynamic fields of drugs

import { defineStore } from 'pinia'
import { useMedlogapi, type MedlogapiResponse } from '#open-fetch';

type Fields = MedlogapiResponse<'list_field_definitions_api_drug_field_def_get'>

interface DrugFieldStore {
    fields: Fields
}

export const useDrugFields = defineStore('drugFields', {
    state: (): DrugFieldStore => ({
        fields: {
            attrs: [],
            attrs_multi: [],
            attrs_ref: [],
            attrs_multi_ref: []
        }
    }),
    actions: {
        async fetchFields() {
            const { data, error } = await useMedlogapi("/api/drug/field_def");
            if (error.value) {
                throw error.value;
            }

            if (data.value) {
                this.fields = data.value;
            }
        }
    },
    getters: {
        allFields: (state: DrugFieldStore) => {
            return state.fields;
        },
        fieldsForSearchResults: (state): Fields => {
            return {
                attrs: state.fields.attrs.filter(item => item.show_in_search_results),
                attrs_ref: state.fields.attrs_ref.filter(item => item.show_in_search_results),
                attrs_multi: state.fields.attrs_multi.filter(item => item.show_in_search_results),
                attrs_multi_ref: state.fields.attrs_multi_ref.filter(item => item.show_in_search_results),
            }
        },
        fieldsForCustomDrugs: (state): Fields => {
            return {
                attrs: state.fields.attrs.filter(item => item.used_for_custom_drug),
                attrs_ref: state.fields.attrs_ref.filter(item => item.used_for_custom_drug),
                attrs_multi: state.fields.attrs_multi.filter(item => item.used_for_custom_drug),
                attrs_multi_ref: state.fields.attrs_multi_ref.filter(item => item.used_for_custom_drug),
            }
        },
    }
});
