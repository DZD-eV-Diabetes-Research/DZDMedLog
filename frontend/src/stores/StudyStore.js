import { defineStore } from 'pinia'
import { useTokenStore } from '@/stores/TokenStore'


import axios from 'axios';

export const useStudyStore = defineStore('StudyStore', {
    state: () => {
        return {
            studies: null,
            test: "test"
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

                this.studies = response
            }
            catch (err) {
                tokenStore.error = err.response.data.detail
            }

        },

    }
})
