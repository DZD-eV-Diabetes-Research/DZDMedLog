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
            try {
                const runtimeConfig = useRuntimeConfig()
                const data = await $fetch(runtimeConfig.public.baseURL + "study", {
                    method: "GET",
                    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
                })
            
            this.studies = data            
            }
            catch (err: any) {
                tokenStore.error = err.response.data.detail
            }
        },

        async getStudy(id:string) {
            
            const foundItem = this.studies.items.find(item => item.id === id)
            return foundItem
        },

        async createStudy(display_name: string): Promise<void>{
            const tokenStore = useTokenStore()
            tokenStore.error = ""
            
            let body = {"display_name": display_name}
            
            try {
                const runtimeConfig = useRuntimeConfig()
                const data = await $fetch(runtimeConfig.public.baseURL + "study", {
                    method: "POST",
                    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
                    body,
                })      
            }
            catch (err: any) {
                tokenStore.error = err.response.data.detail
            }
        },
    },
    persist: true
})
