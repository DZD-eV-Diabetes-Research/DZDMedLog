import { defineStore } from '#imports'
import { useMedlogapi } from '#open-fetch';
import type { SchemaHealthCheckReport } from "#open-fetch-schemas/medlogapi";

interface HealthCheckStore {
    healthy?: boolean
    report?: SchemaHealthCheckReport
}

export const useHealthCheckStore = defineStore('healthCheck', {
    state: (): HealthCheckStore => ({
        healthy: undefined,
        report: undefined,
    }),
    actions: {
        async doSimpleHealthCheck() {
            const { data, error } = await useMedlogapi("/api/health")
            if (error.value) {
                throw error.value;
            }

            this.healthy = data.value?.healthy === true
        },
        async doFullHealthCheck() {
            const { data, error } = await useMedlogapi("/api/health/report")
            if (error.value) {
                throw error.value;
            }

            if (data.value) {
                this.report = data.value;
            } else {
                this.report = undefined;
            }
        },
    },
    getters: {
        fullReport: state => state.report
    },
});
