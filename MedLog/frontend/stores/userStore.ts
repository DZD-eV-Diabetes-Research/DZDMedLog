// Store to handle the User-information

import { defineStore } from 'pinia'

interface UserStore {
    email: string,
    displayName: string,
    roles: string[],
    userName: string,
    viewProfile: boolean,
    buttonText: string,
    userID: string,
}

export const useUserStore = defineStore('UserStore', {
    state: (): UserStore => ({
        email: "",
        displayName: "",
        roles: [],
        userName: "",
        viewProfile: false,
        buttonText: "Toggle to User",
        userID: "",
    }),
    actions: {
        async setUserInfo() {
            const {$medlogapi} = useNuxtApp();

            try {
                const data = await $medlogapi("/api/user/me")

                this.email = data.email
                this.displayName = data.display_name
                this.roles = data.roles
                this.userName = data.user_name
                this.userID = data.id
            } catch (err) {
                console.log(err);
            }
        }
    },
    getters: {
        isLoggedIn: state => {
            return state.userID !== ''
        },
        isAdmin: state => {
            const roleStore = useRoleStore()
            return state.roles.some(role => roleStore.isAdminRole(role));
        },
        isUserAdmin: state => {
            const roleStore = useRoleStore()
            return state.roles.some(role => roleStore.isUserManagerRole(role));
        },
    },
}) 
