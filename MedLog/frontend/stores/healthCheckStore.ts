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
                this.healthy = undefined;
                throw error.value;
            }

            if (typeof data.value !== 'object') {
                this.healthy = undefined;
                throw new Error("Health endpoint did not provide an object");
            }

            this.healthy = data.value?.healthy === true
        },
        async doFullHealthCheck() {
            const { data, error } = await useMedlogapi("/api/health/report")
            if (error.value) {
                this.report = undefined;
                throw error.value;
            }

            if (typeof data.value !== 'object') {
                this.report = undefined;
                throw new Error("Health report endpoint did not provide an object");
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
