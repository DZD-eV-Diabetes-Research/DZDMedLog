import { defineStore } from '#imports'
import { useMedlogapi } from '#open-fetch';

interface ConfigStore {
    branding: {
        supportEmail?: string,
    },
    versionInfo: {
        branch?: string,
        version?: string,
    },
}

export const useConfigStore = defineStore('config', {
    state: (): ConfigStore => ({
        branding: {
            supportEmail: undefined,
        },
        versionInfo: {
            branch: undefined,
            version: undefined,
        }
    }),
    actions: {
        async fetchAllConfigs() {
            await this.fetchVersionConfig();
            await this.fetchBrandingConfig();
        },
        async fetchBrandingConfig() {
            const { data, error } = await useMedlogapi("/api/config/branding")
            if (error.value) {
                throw error.value;
            }

            this.branding.supportEmail = data.value?.support_email ?? undefined;
        },
        async fetchVersionConfig() {
            const { data, error } = await useMedlogapi("/api/config/version")
            if (error.value) {
                throw error.value;
            }

            this.versionInfo.branch = data.value?.branch ?? undefined;
            this.versionInfo.version = data.value?.version ?? undefined;
        },
    },
});
