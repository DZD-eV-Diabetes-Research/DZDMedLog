import { type MedlogapiResponse, useMedlogapi } from "#open-fetch";
import { defineStore } from 'pinia'

export type Roles = MedlogapiResponse<'Get_Roles_api_role_get'>

interface RoleStoreState {
    roles: Roles,
}

export const useRoleStore = defineStore('RoleStore', {

    state: (): RoleStoreState => ({
        permissions: [],
    }),
    actions: {
        async loadRoles() {
            const { data, error } = await useMedlogapi("/api/role")
            if (error.value) {
                throw error.value;
            }

            this.roles = data.value ?? [];
        },
    },
    getters: {
        adminRoles(state: RoleStoreState): Roles {
            return state.roles?.filter((role) => role.has_admin_permissions)
        },
        availableRoles(state: RoleStoreState): Roles {
            return state.roles;
        },
        userManagerRoles(state: RoleStoreState): Roles {
            return state.roles?.filter((role) => role.has_usermanager_permissions)
        },
        isAdminRole() {
            return (role: string) => {
                return this.adminRoles.map(role => role.role_name).includes(role);
            }
        },
        isUserManagerRole() {
            return (role: string) => {
                return this.userManagerRoles.map(role => role.role_name).includes(role);
            }
        },
    },
})
