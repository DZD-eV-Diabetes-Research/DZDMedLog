import { defineStore } from 'pinia'

export const useUserStore = defineStore('UserStore', {
    state: () => ({
        email: null,
        display_name: null,
        roles: null,
        user_name: null,
        my_api: import.meta.env.VITE_API
    })
})