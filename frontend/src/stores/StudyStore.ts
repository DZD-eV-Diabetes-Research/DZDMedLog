import { defineStore } from 'pinia'
import { useTokenStore } from '@/stores/TokenStore'

import axios from 'axios';

interface Study {
    deactivated: boolean;
    id:string;
    display_name: string;
    created_at: string;
    no_permissions: boolean;
    name: string;
}

interface MyState {
    studies: Study[],
    event: string,
}

export const useStudyStore = defineStore('StudyStoreNew', {
    
    state: (): MyState => ({
        studies: [],
        event: "",
    }),
    actions: {
        async listStudies(): Promise<void> {
            const tokenStore = useTokenStore()
            tokenStore.error = ""
            try {
                axios.defaults.headers.common = { 'Authorization': "Bearer " + tokenStore.accessToken }

                const response = await axios.get("/study")
                this.studies = response.data
            }
            catch (err:any) {
                tokenStore.error = err.response.data.detail
            }
        },
        // TO UPDATE / FIX TYPE OF PAYLOAD
        async createStudy(payload:any) {
            const tokenStore = useTokenStore()
            tokenStore.error = ""

            try {
                axios.defaults.headers.common = { 'Authorization': "Bearer " + tokenStore.accessToken }

                await axios.post("/study", {
                    display_name: payload.displayName,
                    deactivated: false,
                    no_permissions: false,
                    name: payload.name
                },
                    {
                        headers: {
                            'Content-Type': 'json',
                        }
                    })
            }
            catch (err: any) {
                tokenStore.error = err.response.data.detail
            }
        },
        async listEvents(studyID:string) {
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
