import { defineStore } from 'pinia'
import axios from 'axios';

interface MyState {
    accessToken: string
    refreshToken: string
    error: string
    loggedStatus: boolean
}

export const useTokenStore = defineStore('TokenStoreNew', {
    state: (): MyState => ({
        accessToken: "",
        refreshToken: "",
        error: "",
        loggedStatus: false,
    }),
    actions: {
        async login(payload: { username: string; password: string }): Promise<void> {
            try {
                const response = await axios.post('/auth/token', {
                    username: payload.username,
                    password: payload.password
                }, {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                });
                
                this.accessToken = response.data.access_token
                this.refreshToken = response.data.refresh_token
                this.loggedStatus = true

            } catch(err:any) {
                this.error = "Wrong username or password"
            }

        },
        async updateAccessToken(): Promise<void> {

            axios.defaults.headers.common = { 'refresh-token': "Bearer " + this.refreshToken }

            try {
                const response = await axios.post('/auth/refresh', {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    }
                })
                this.accessToken = response.data.access_token
            } catch(err:any) {
                this.error = err.response.data.detail
            }
        }
    },
    persist: true
});
