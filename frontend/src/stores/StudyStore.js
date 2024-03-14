import { defineStore } from 'pinia'
import { useTokenStore } from '@/stores/TokenStore'

import axios from 'axios';

import { StudyApiFp } from '@/openapi-client-type'
const studyApi = StudyApiFp();
const listStudiesRequestFunction = studyApi.listStudiesStudyGet();

export const useStudyStore = defineStore('StudyStore', {
    state: () => {
        return {
            studies: null,
        }
    },

    getters: {
    },

    actions: {
        async testStudies() {
            listStudiesRequestFunction()
                .then(response => {
                    console.log('List of studies:', response.data);
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        },
        async listStudies() {
            const tokenStore = useTokenStore()
            tokenStore.error = null
            try {
                axios.defaults.headers.common = { 'Authorization': "Bearer " + tokenStore.get_access_token }

                const response = await axios.get("/study")

                console.log(response.data)
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
