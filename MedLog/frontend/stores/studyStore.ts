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
            console.log(data);
            
            }
            catch (err: any) {
                tokenStore.error = err.response.data.detail
            }
        },

        async listEvents(studyID: string) {
            const tokenStore = useTokenStore()
            tokenStore.error = ""

            try {
                axios.defaults.headers.common = { 'Authorization': "Bearer " + tokenStore.accessToken }

                const response = await axios.get("study/" + studyID + "/event")
                this.event = response.data

            }
            catch (err: any) {
                tokenStore.error = err.response.data.detail
            }
        }
    },
    persist: true
})
