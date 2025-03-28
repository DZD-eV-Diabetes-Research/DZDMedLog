import { defineStore } from 'pinia'

interface ProbandState {
    probandID: string 
    interviews : any[]
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