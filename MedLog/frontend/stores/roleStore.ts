import { useMedlogapi } from "#open-fetch";
import { defineStore } from '#imports'
import type { SchemaUserRoleApiRead } from "#open-fetch-schemas/medlogapi";

interface RoleStoreState {
    roles: SchemaUserRoleApiRead[],
}

export const useRoleStore = defineStore('RoleStore', {

    state: (): RoleStoreState => ({
        roles: [],
    }),
    actions: {
        async loadRoles() {
            const { data, error } = await useMedlogapi("/api/role")
            if (error.value) {
                throw error.value;
            }

            if (!Array.isArray(data.value)) {
                throw new Error("Roles endpoint did not provide an array");
            }

            this.roles = data.value ?? [];
        },
    },
    getters: {
        adminRoles(state: RoleStoreState): SchemaUserRoleApiRead[] {
            return state.roles?.filter((role) => role.has_admin_permissions)
        },
        availableRoles(state: RoleStoreState): SchemaUserRoleApiRead[] {
            return state.roles;
        },
        userManagerRoles(state: RoleStoreState): SchemaUserRoleApiRead[] {
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
