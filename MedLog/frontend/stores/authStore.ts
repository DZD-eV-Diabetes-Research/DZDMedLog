import { defineStore } from '#imports'
import { useMedlogapi } from '#open-fetch';
import type { SchemaAuthSchemeInfo } from "#open-fetch-schemas/medlogapi";

interface AuthStore {
    schemes: SchemaAuthSchemeInfo[]
}

export const useAuthStore = defineStore('auth', {
    state: (): AuthStore => ({
        schemes: [],
    }),
    actions: {
        async fetchAllAuthSchemes() {
            const { data, error } = await useMedlogapi("/api/auth/list")
            if (error.value) {
                throw error.value;
            }

            this.schemes = data.value ?? [];
        },
        async doAutoLogin() {
            const loginScheme = this.autoLoginScheme;
            if (!loginScheme) {
                throw new Error('There is no auto-login scheme');
            }

            // Only OIDC login can be auto-login
            await this.doOIDCLogin(loginScheme);
        },
        async doBasicLogin(schema: SchemaAuthSchemeInfo, username: string, password: string): Promise<void> {
            if (schema.auth_type !== 'basic') {
                throw new Error('Auth schema mismatch, expected basic auth type');
            }

            // TODO this has to be verified, local accounts are not a thing at the moment
            await $fetch(schema.login_endpoint, {
                method: 'POST',
                body: {
                    "username": username,
                    "password": password,
                },
            });
        },
        async doOIDCLogin(schema: SchemaAuthSchemeInfo): Promise<void> {
            if (schema.auth_type !== 'oidc') {
                throw new Error('Auth schema mismatch, expected oidc auth type');
            }

            await navigateTo(schema.login_endpoint, { external: true });
        },
    },
    getters: {
        autoLoginAvailable(): boolean {
            return this.autoLoginScheme !== undefined;
        },
        autoLoginScheme(state): SchemaAuthSchemeInfo | undefined  {
            return state.schemes.find(schema => schema.auto_login)
        },
        allSchemes: (state) => state.schemes,
    },
});
