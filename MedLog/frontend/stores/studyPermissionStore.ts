import {defineStore} from '#imports'
import type {SchemaStudyPermissionDesc} from "#open-fetch-schemas/medlogapi";

interface StudyPermissionStoreState {
    availablePermissions: SchemaStudyPermissionDesc[],
}

export const useStudyPermissionStore = defineStore('StudyPermissionStore', {

    state: (): StudyPermissionStoreState => ({
        availablePermissions: [],
    }),
    actions: {
        async loadPermissions() {
            this.availablePermissions = await useGetPermissions();
        },
    },
})
