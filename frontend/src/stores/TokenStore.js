import { defineStore } from 'pinia'

import axios from 'axios';

export const useTokenStore = defineStore('TokenStore', {
    state: () => {
        return {
            access_token: null,
            refresh_token: null,
            error: null,
            logged_in: false,
        }
    },

    getters: {
        get_error() {
            return this.error
        },
        get_access_token() {
            return this.access_token
        },
        get_refresh_token() {
            return this.refresh_token
        },
        get_logged_in(){
            return this.logged_in
        }
    },


    actions: {

        async login(payload) {

            try {
                const response = await axios.post('/auth/token', {
                    username: payload.username,
                    password: payload.password
                }, {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                }
                )
                this.access_token = response.data.access_token
                this.refresh_token = response.data.refresh_token
                this.logged_in = true
            } catch (err) {
                this.error = err.response.data.detail
            }

        },

        async updateAccessToken() {

            axios.defaults.headers.common = { 'refresh-token': "Bearer " + this.get_refresh_token }

            try {
                const response = await axios.post('/auth/refresh', {
                    headers: {
                        'Content-Type': 'json',
                    }
                })

                this.access_token = response.data.access_token
            } catch (err) {
                this.error = err.response.data.detail
            }

        }
    },
    persist: true,
})
