import type {SchemaSystemAnnouncement} from "#open-fetch-schemas/medlogapi";

interface SystemAnnouncementsStore {
    systemAnnouncements: SchemaSystemAnnouncement[],
    dismissedIds: string[],
}

export const useSystemAnnouncementsStore = defineStore('systemAnnouncements', {
    state: (): SystemAnnouncementsStore => ({
        systemAnnouncements: [],
        dismissedIds: [],
    }),
    actions: {
        dismissAnnouncement(id: string) {
            this.dismissedIds.push(id);
            // TODO save to localStorage
        },
        async fetchSystemAnnouncements() {
            const { $medlogapi } = useNuxtApp();
            this.systemAnnouncements = await $medlogapi('/api/config/announcements');
        },
    },
    getters: {
        allAnnouncements(state: SystemAnnouncementsStore): SchemaSystemAnnouncement[] {
            return this.systemAnnouncements.filter(item => !state.dismissedIds.includes(item.id));
        },
        numberOfAlertAnnouncements(): number {
            return this.allAnnouncements.filter(item => item.type === 'alert').length;
        },
        numberOfInfoAnnouncements(): number {
            return this.allAnnouncements.filter(item => item.type === 'info').length;
        },
        numberOfWarningAnnouncements(): number {
            return this.allAnnouncements.filter(item => item.type === 'warning').length;
        },
    },
});
