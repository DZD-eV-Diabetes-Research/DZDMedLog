import type {SchemaSystemAnnouncement} from "#open-fetch-schemas/medlogapi";

interface SystemAnnouncementsStore {
    systemAnnouncements: SchemaSystemAnnouncement[],
    dismissedIds: string[],
}

function loadDismissedIds(): string[] {
    const dismissedIds: string[] = [];

    const savedIds = localStorage.getItem('medlog-dismissed-announcements');
    if (savedIds) {
        const parsedValue = JSON.parse(savedIds);
        if (parsedValue && Array.isArray(parsedValue)) {
            dismissedIds.push(...parsedValue.filter(item => typeof item === 'string'));
        }
    }

    return dismissedIds;
}

export const useSystemAnnouncementsStore = defineStore('systemAnnouncements', {
    state: (): SystemAnnouncementsStore => ({
        systemAnnouncements: [],
        dismissedIds: loadDismissedIds(),
    }),
    actions: {
        dismissAnnouncement(id: string) {
            this.dismissedIds.push(id);
            localStorage.setItem('medlog-dismissed-announcements', JSON.stringify(this.dismissedIds));
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
