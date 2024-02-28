import { defineStore } from 'pinia'
import { useTokenStore } from '@/stores/TokenStore'


import axios from 'axios';

export const useStudyStore = defineStore('StudyStore', {
    state: () => {
        return {
            studies: null,
        }
    },

    getters: {

    },


    actions: {
        async myStudies() {
            const tokenStore = useTokenStore()
            tokenStore.error = null
            try {
                axios.defaults.headers.common = { 'Authorization': "Bearer " + tokenStore.get_access_token }

                const response = await axios.get("/study")

                this.studies = response.data
            }
            catch (err) {
                tokenStore.error = err.response.data.detail
            }
        },
        async createStudy(payload) {
            const tokenStore = useTokenStore()
            tokenStore.error = null

            try {
                axios.defaults.headers.common = { 'Authorization': "Bearer " + tokenStore.get_access_token }

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
            catch (err) {
                tokenStore.error = err.response.data.detail
            }
        }
    },
    persist: true
})
