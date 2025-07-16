// Store to handle to current studies

import { defineStore } from 'pinia'

interface Study {
    deactivated: boolean;
    id: string;
    display_name: string;
    created_at: string;
    no_permissions: boolean;
    name: string;
}

interface StudyState {
    studies: Study[],
    event: string,
}

export const useStudyStore = defineStore('StudyStore', {

    state: (): StudyState => ({
        studies: [],
        event: "",
    }),
    actions: {
        async listStudies(): Promise<void> {
            const tokenStore = useTokenStore()
            tokenStore.error = ""
            const {$medlogapi} = useNuxtApp();
            try {
                const data = await $medlogapi("/api/study")

                this.studies = data
            }
            catch (err: any) {
                tokenStore.error = err?.response.data.detail
            }
        },

        async getStudy(id: string) {
            if (this.studies.length === 0) {
            }
            else {
                const foundItem = this.studies.items.find(item => item.id === id)
                return foundItem
            }
        },
    },
    persist: {
        storage: localStorage,
    }
})