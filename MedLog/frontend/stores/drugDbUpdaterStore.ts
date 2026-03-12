import type { SchemaDrugUpdaterStatus } from "#open-fetch-schemas/medlogapi";

interface DrugDbUpdaterStore {
    updateFeatureAvailable: boolean
    status?: SchemaDrugUpdaterStatus
}

export const useDrugDbUpdaterStore = defineStore('drugDBUpdater', {
    state: (): DrugDbUpdaterStore => ({
        updateFeatureAvailable: false,
        status: undefined,
    }),
    actions: {
        async fetchStatus() {
            const { data, error } = await useMedlogapi("/api/drug/db/update")

            if (error.value && error.value.statusCode === 501) {
                // Updater is not implemented for this data source
                this.updateFeatureAvailable = false;
                this.status = undefined;
                return;
            } else if (error.value) {
                this.updateFeatureAvailable = false;
                this.status = undefined;
                throw error.value;
            }

            this.updateFeatureAvailable = true;
            this.status = data.value;
        },
    },
});
