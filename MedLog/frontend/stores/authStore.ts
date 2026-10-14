import { defineStore } from '#imports'
import { useMedlogapi } from '#open-fetch';
import type { SchemaAuthSchemeInfo } from "#open-fetch-schemas/medlogapi";

interface AuthStore {
    loginError?: Error | unknown;
    loginInProgress: boolean;
    loginInProgressProviderSlug: string | null | undefined;
    schemes: SchemaAuthSchemeInfo[]
}

export const useAuthStore = defineStore('auth', {
    state: (): AuthStore => ({
        loginError: undefined,
        loginInProgress: false,
        loginInProgressProviderSlug: undefined,
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
                this.loginError = new Error('There is no auto-login scheme');
                return;
            }

            // Only OIDC login can be auto-login
            await this.doOIDCLogin(loginScheme);
        },
        async doBasicLogin(schema: SchemaAuthSchemeInfo, username: string, password: string): Promise<void> {
            if (schema.auth_type !== 'basic') {
                this.loginError = new Error('Auth schema mismatch, expected basic auth type');
            }

            this.loginError = undefined;
            this.loginInProgress = true;
            this.loginInProgressProviderSlug = schema.provider_slug;

            try {
                // TODO this has to be verified, local accounts are not a thing at the moment
                await $fetch(schema.login_endpoint, {
                    method: 'POST',
                    body: {
                        "username": username,
                        "password": password,
                    },
                });
            } catch (error) {
                this.loginError = error;
            } finally {
                this.loginInProgress = false;
                this.loginInProgressProviderSlug = undefined;
            }
        },
        async doOIDCLogin(schema: SchemaAuthSchemeInfo): Promise<void> {
            if (schema.auth_type !== 'oidc') {
                this.loginError = new Error('Auth schema mismatch, expected oidc auth type');
                return;
            }

            this.loginError = undefined;
            this.loginInProgress = true;
            this.loginInProgressProviderSlug = schema.provider_slug;

            await navigateTo(schema.login_endpoint, { external: true });

            this.loginInProgress = false;
            this.loginInProgressProviderSlug = undefined;

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
        isLocalLoginAvailable(): boolean {
            return this.localLoginScheme !== undefined;
        },
        localLoginScheme(state): SchemaAuthSchemeInfo | undefined {
            return state.schemes.find(scheme => scheme.auth_type === 'basic');
        },
        oidcLoginSchemes(state): SchemaAuthSchemeInfo[] | undefined {
            return state.schemes.filter(scheme => scheme.auth_type === 'oidc');
        },
    },
});
