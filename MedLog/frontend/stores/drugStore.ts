import { defineStore } from 'pinia'

interface DrugState {
    item: any
    intake_start_time_utc: string
    as_needed_does_unit: number
    consumed_meds_today: boolean
    
}

export const useDrugStore = defineStore('DrugStore',{
    id: "drug-store",
    state: (): DrugState => ({
        
        item: null,
        intake_start_time_utc: "",
        as_needed_does_unit: 0,
        consumed_meds_today: false

    }),
    persist: true
}) 