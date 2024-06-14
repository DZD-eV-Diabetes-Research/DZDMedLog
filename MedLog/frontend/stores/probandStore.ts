import { defineStore } from 'pinia'

interface ProbandState {
    probandID: string 
    interviews : Array
}

export const useProbandStore = defineStore('ProbandStore',{
    id: "proband-store",
    state: (): ProbandState => ({
        
        probandID: "",
        interviews: null
    }),
    persist: true
}) 