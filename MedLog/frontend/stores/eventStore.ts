import { defineStore } from 'pinia'
import type { MedlogapiResponse } from '#open-fetch';
import useGetEventsByStudy from "~/composables/useGetEventsByStudy";

export type Events = MedlogapiResponse<'list_events_api_study__study_id__event_get'>['items']

interface EventStore {
    events: Events
}

export const useEventStore = defineStore('events', {
    state: (): EventStore => ({
        events: [],
    }),
    actions: {
        async loadAllEventsForStudy(studyId: string) {
            this.events = await useGetEventsByStudy(studyId);
        }
    },
    getters: {
        nameForEvent(state: EventStore) {
            return (eventId: string) => {
                const event = state.events.find(item => item.id === eventId);

                return event ? event.name : undefined;
            };
        }
    },
});
