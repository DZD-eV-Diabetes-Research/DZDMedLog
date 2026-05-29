import {defineStore} from '#imports'
import type {SchemaStudyPermissionDesc, SchemaStudyPermissionRead} from "#open-fetch-schemas/medlogapi";

interface StudyPermissionStoreState {
    availablePermissions: SchemaStudyPermissionDesc[],
    studyPermissionsCurrentUser: SchemaStudyPermissionRead[],
}

export const useStudyPermissionStore = defineStore('StudyPermissionStore', {

    state: (): StudyPermissionStoreState => ({
        availablePermissions: [],
        studyPermissionsCurrentUser: [],
    }),
    actions: {
        async loadPermissions() {
            this.availablePermissions = await useGetPermissions();
        },
        async loadStudyPermissionsForCurrentUser() {
            const studyStore = useStudyStore();
            const {$medlogapi} = useNuxtApp();
            const permissions = [];

            for (const study of studyStore.studies) {
                if (!study.id) {
                    continue;
                }

                permissions.push(await $medlogapi("/api/study/{study_id}/permissions/me", {
                    path: {
                        study_id: study.id,
                    },
                }));
            }
            this.studyPermissionsCurrentUser = permissions;
        },
    },
    getters: {
        currentUserCanExport(state) {
            return (studyId?: string): boolean => {
                if (!studyId) {
                    return false;
                }

                const userStore = useUserStore();
                const permissionForStudy = state.studyPermissionsCurrentUser.find(item => item.study_id === studyId)
                if (!permissionForStudy) {
                    return false;
                }
                return userStore.isAdmin || permissionForStudy.is_study_viewer || permissionForStudy.is_study_admin;
            }
        },
        currentUserCanInterview(state) {
            return (studyId?: string): boolean => {
                if (!studyId) {
                    return false;
                }

                const userStore = useUserStore();
                const permissionForStudy = state.studyPermissionsCurrentUser.find(item => item.study_id === studyId)
                if (!permissionForStudy) {
                    return false;
                }
                return userStore.isAdmin || permissionForStudy.is_study_interviewer || permissionForStudy.is_study_admin;
            }
        },
        currentUserCanManageSomeStudy(state): boolean {
            console.log("user permissions", state.studyPermissionsCurrentUser);
            return state.studyPermissionsCurrentUser.some(permissionForStudy => permissionForStudy.is_study_admin === true);
        },
        currentUserCanManageStudy(state) {
            return (studyId?: string): boolean => {
                if (!studyId) {
                    return false;
                }

                const userStore = useUserStore();
                const permissionForStudy = state.studyPermissionsCurrentUser.find(item => item.study_id === studyId)
                if (!permissionForStudy) {
                    return false;
                }
                return userStore.isAdmin || permissionForStudy.is_study_admin;
            }
        },
        currentUserCanManageUsers(state) {
            return (studyId?: string): boolean => {
                if (!studyId) {
                    return false;
                }

                const userStore = useUserStore();
                const permissionForStudy = state.studyPermissionsCurrentUser.find(item => item.study_id === studyId)
                if (!permissionForStudy) {
                    return false;
                }
                return userStore.isAdmin || userStore.isUserAdmin || permissionForStudy.is_study_admin;
            }
        },
        currentUserCanView(state) {
            return (studyId?: string): boolean => {
                if (!studyId) {
                    return false;
                }

                const userStore = useUserStore();
                const permissionForStudy = state.studyPermissionsCurrentUser.find(item => item.study_id === studyId)
                if (!permissionForStudy) {
                    return false;
                }
                return userStore.isAdmin || permissionForStudy.is_study_viewer || permissionForStudy.is_study_interviewer || permissionForStudy.is_study_admin;
            }
        },
    },
})
