// Store to handle the current subject/patient

import { defineStore } from 'pinia'

interface ProbandState {
    probandID: string 
    interviews : any[] | null
}

export const useProbandStore = defineStore('ProbandStore',{
    state: (): ProbandState => ({
        probandID: "",
        interviews: null
    }),
    persist: {
        storage: localStorage,
    }
}) 