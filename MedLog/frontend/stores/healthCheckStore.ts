import { defineStore } from 'pinia'
import { useMedlogapi, type MedlogapiResponse } from '#open-fetch';

type HealthReport = MedlogapiResponse<'get_health_report_api_health_report_get'>

interface HealthCheckStore {
    healthy?: boolean
    report?: HealthReport
}

export const useHealthCheck = defineStore('healthCheck', {
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
});
