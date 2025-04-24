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
    id: "user-store",
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
            const tokenStore = useTokenStore()
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
        async toggle_profile() {
            this.isAdmin = !this.isAdmin
            if (this.isAdmin) {
                this.buttonText = "Toggle to User"
            } else {
                this.buttonText = "Toggle to Admin"
            }
        },
        // async toggle_profile() {
        //     this.viewProfile = !this.viewProfile
        //     if (this.viewProfile === true) {
        //         this.buttonText = "Back"
        //         this.userMe()
        //     } else {
        //         this.buttonText = "Profile"
        //     }
        // },
    },
    persist: {
        storage: localStorage,
    }
}) 