import { defineStore } from 'pinia'
import { useTokenStore } from '@/stores/TokenStore'

import axios from 'axios';


interface MyState {
    email: string,
    displayName: string,
    roles: string[],
    userName: string,
    isAdmin: boolean,
    viewProfile: boolean,
    buttonText: string

}

export const useUserStore = defineStore('UserStoreNew', {
    state: (): MyState => ({
        email: "",
        displayName: "",
        roles: [],
        userName: "",
        isAdmin: false,
        viewProfile: false,
        buttonText: "Profile"
    }),
    actions: {
        async userMe() {
            const tokenStore = useTokenStore()
            tokenStore.error = ""
            try {
                axios.defaults.headers.common = { 'Authorization': "Bearer " + tokenStore.accessToken }
                const response = await axios.get("/user/me")

                this.email = response.data.email
                this.displayName = response.data.display_name
                this.roles = response.data.roles
                this.userName = response.data.user_name

                if (this.roles.includes('medlog-admin')) {
                    this.isAdmin = true
                }
            }
            catch (err: any) {
                tokenStore.error = err.response.data.detail
            }
        },
        async toggle_profile() {
            this.viewProfile = !this.viewProfile
            if (this.viewProfile === true) {
                this.buttonText = "Back"
                this.userMe()
            } else {
                this.buttonText = "Profile"
            }
        }
    },
    persist: true,
})