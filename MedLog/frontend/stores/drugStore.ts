import { defineStore } from 'pinia'

interface DrugState {
    custom: boolean
    item: any
    source: string
    frequency: string
    intervall: string
    intake_start_time_utc: string
    intake_end_time_utc: string
    dose: number
    consumed_meds_today: string
    action: boolean
    row: any
    
}

export const useDrugStore = defineStore('DrugStore',{
    id: "drug-store",
    state: (): DrugState => ({
        custom: false,
        item: null,
        source: "",
        frequency: "",
        intervall: "",
        intake_start_time_utc: "",
        intake_end_time_utc: "",
        dose: 0,
        consumed_meds_today: "Yes",
        action: false,
        row: null

    }),
    getters: {
        isAction: (state) => state.action
    },
    persist: true
}) 