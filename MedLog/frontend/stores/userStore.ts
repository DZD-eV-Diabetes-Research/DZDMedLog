// Store to handle the User-information

import {defineStore} from 'pinia'
import type {SchemaUser} from '#open-fetch-schemas/medlogapi'

interface UserStore {
    currentUserId?: string
    users: SchemaUser[]
}

export const useUserStore = defineStore('UserStore', {
    state: (): UserStore => ({
        currentUserId: undefined,
        users: [],
    }),
    actions: {
        async setUserInfo() {
            const me = await useGetUserMe();
            this.upsertUser(me);
            this.currentUserId = me.id;
        },
        async loadUsers() {
            const users = await useGetUsers(true);
            for (const user of users) {
                this.upsertUser(user);
            }
        },
        upsertUser(userToUpsert: SchemaUser) {
            const indexOfExistingUser = this.users.findIndex(user => user.id === userToUpsert.id);
            if (indexOfExistingUser !== -1) {
                this.users[indexOfExistingUser] = userToUpsert;
            } else {
                this.users.push(userToUpsert);
            }
        },
    },
    getters: {
        allUsers: (state): SchemaUser[] => {
            return state.users
        },
        currentUser: (state): SchemaUser | null => {
            const foundUser = state.users.find(user => user.id === state.currentUserId);
            return foundUser ? foundUser : null;
        },
        isLoggedIn(): boolean{
            return this.currentUser !== null
        },
        isAdmin(): boolean {
            if (!this.currentUser) {
                return false;
            }

            const roleStore = useRoleStore()
            return this.currentUser.roles.some(role => roleStore.isAdminRole(role));
        },
        isUserAdmin(): boolean {
            if (!this.currentUser) {
                return false;
            }

            const roleStore = useRoleStore()
            return this.currentUser.roles.some(role => roleStore.isUserManagerRole(role));
        },
        nameForUser(state: UserStore) {
            return (userId: string) => {
                const user = state.users.find(item => item.id === userId);

                return user ? (user.display_name ?? user.user_name) : undefined;
            };
        }
    },
}) 
