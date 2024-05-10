import { defineStore } from 'pinia'

interface UserStore {
    email: string,
    displayName: string,
    roles: string[],
    userName: string,
    isAdmin: boolean,
    viewProfile: boolean,
    buttonText: string

}

export const useUserStore = defineStore('UserStore', {
    id: "user-store",
    state: (): UserStore => ({
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
            try {
                const runtimeConfig = useRuntimeConfig()
                const data = await $fetch(runtimeConfig.public.baseURL + "user/me", {
                    method: "GET",
                    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
                })

                this.email = data.email
                this.displayName = data.display_name
                this.roles = data.roles
                this.userName = data.user_name

                if (this.roles.includes('medlog-admin')) {
                    this.isAdmin = true
                };


            } catch (err) {
                console.log(err);
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
        },
    },
    persist: true
}) 