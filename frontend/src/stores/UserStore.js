import { defineStore } from 'pinia'
import { useTokenStore } from '@/stores/TokenStore'

import axios from 'axios';

export const useUserStore = defineStore('UserStore', {
    state: () => {
        return {
            email: null,
            display_name: null,
            roles: null,
            user_name: null,
            my_api: import.meta.env.VITE_API,
        }
    },
    getters: {
        get_email(){
            return this.email
        },
        get_display_name(){
            return this.display_name
        },
        get_roles(){
            return this.roles
        },
        get_user_name(){
            return this.user_name
        },
    },
    actions: {
        async userMe() {
            const tokenStore = useTokenStore()
            tokenStore.error = null
            try {

            axios.defaults.headers.common = { 'Authorization': "Bearer " + tokenStore.get_access_token }

            const response = await axios.get("/user/me")

            this.email = response.data.email
            this.display_name = response.data.display_name
            this.roles = response.data.roles
            this.user_name = response.data.user_name
        }
        catch (err) {
            tokenStore.error = err.response.data.detail
        }

        },
    }
    ,
    persist: true,
})