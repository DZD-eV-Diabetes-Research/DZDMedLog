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
    drugData: {
        sourceName: string,
        sourceInfoUrl: string,
        supportsForceManualUpdate: boolean,
        supportsScheduledAutoUpdate: boolean,
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
        },
        drugData: {
            sourceName: "",
            sourceInfoUrl: "",
            supportsForceManualUpdate: false,
            supportsScheduledAutoUpdate: false
        }
    }),
    actions: {
        async fetchAllConfigs() {
            await this.fetchVersionConfig();
            await this.fetchBrandingConfig();
            await this.fetchDataSourceConfig();
        },
        async fetchBrandingConfig() {
            const { data, error } = await useMedlogapi("/api/config/branding")
            if (error.value) {
                throw error.value;
            }

            if (typeof data.value !== 'object') {
                throw new Error("Branding endpoint did not provide an object");
            }

            this.branding.supportEmail = data.value?.support_email ?? undefined;
        },
        async fetchVersionConfig() {
            const { data, error } = await useMedlogapi("/api/config/version")
            if (error.value) {
                throw error.value;
            }

            if (typeof data.value !== 'object') {
                throw new Error("Version endpoint did not provide an object");
            }

            this.versionInfo.branch = data.value?.branch ?? undefined;
            this.versionInfo.version = data.value?.version ?? undefined;
        },
        async fetchDataSourceConfig() {
            const { data, error } = await useMedlogapi("/api/config/drugdata")
            if (error.value) {
                throw error.value;
            }

            if (typeof data.value !== 'object') {
                throw new Error("Drug data endpoint did not provide an object");
            }

            this.drugData.sourceName = data.value?.drug_data_source_name ?? "";
            this.drugData.sourceInfoUrl = data.value?.drug_data_source_info_url ?? "";
            this.drugData.supportsForceManualUpdate = data.value?.supports_force_manual_update === true;
            this.drugData.supportsScheduledAutoUpdate = data.value?.supports_scheduled_auto_update === true;
        },
    },
    getters: {
        appName: () => {
            // Currently the app name is part of the health check report
            const healthCheckStore = useHealthCheckStore();
            return healthCheckStore.fullReport?.name ?? "DZDMedLog"
        },
    },
});
