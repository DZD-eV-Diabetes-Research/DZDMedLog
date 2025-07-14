// Store to handle the User-information

import { defineStore } from 'pinia'

interface UserStore {
    email: string,
    displayName: string,
    roles: string[],
    userName: string,
    isAdmin: boolean,
    viewProfile: boolean,
    buttonText: string,
    userID: string,
    firstEvent: boolean

}

export const useUserStore = defineStore('UserStore', {
    state: (): UserStore => ({
        email: "",
        displayName: "",
        roles: [],
        userName: "",
        isAdmin: false,
        viewProfile: false,
        buttonText: "Toggle to User",
        userID: "",
        firstEvent: false,
    }),
    actions: {
        async userMe() {
            const { $api } = useNuxtApp();

            try {
                const runtimeConfig = useRuntimeConfig()
                const data = await $api(runtimeConfig.public.baseURL + "user/me")

                this.email = data.email
                this.displayName = data.display_name
                this.roles = data.roles
                this.userName = data.user_name
                this.userID = data.id

                if (this.roles.includes('medlog-admin')) {
                    this.isAdmin = true
                };


            } catch (err) {
                console.log(err);
            }
        },
    },
    persist: {
        storage: localStorage,
    }
}) 