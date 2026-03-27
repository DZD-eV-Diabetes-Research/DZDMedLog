import type {SchemaSystemAnnouncement} from "#open-fetch-schemas/medlogapi";

interface SystemAnnouncementsStore {
    systemAnnouncements: SchemaSystemAnnouncement[],
}

export const useSystemAnnouncementsStore = defineStore('systemAnnouncements', {
    state: (): SystemAnnouncementsStore => ({
        systemAnnouncements: [],
    }),
    actions: {
        async fetchSystemAnnouncements() {
            const { $medlogapi } = useNuxtApp();
            this.systemAnnouncements = await $medlogapi('/api/config/announcements');
        },
    },
    getters: {
        allAnnouncements: state => {
            return state.systemAnnouncements;
        },
        numberOfAlertAnnouncements: state => {
            return state.systemAnnouncements.filter(item => item.type === 'alert').length;
        },
        numberOfInfoAnnouncements: state => {
            return state.systemAnnouncements.filter(item => item.type === 'info').length;
        },
        numberOfWarningAnnouncements: state => {
            return state.systemAnnouncements.filter(item => item.type === 'warning').length;
        },
    },
});
