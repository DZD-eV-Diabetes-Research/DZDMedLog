import { defineStore } from '#imports'
import useGetEventsByStudy from "~/composables/useGetEventsByStudy";
import type { SchemaEvent } from "#open-fetch-schemas/medlogapi";

interface EventStore {
    events: SchemaEvent[]
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
        eventsForStudy(state: EventStore) {
            return (studyId: string) => {
                return state.events.filter(event => event.study_id === studyId);
            }
        },
        nameForEvent(state: EventStore) {
            return (eventId: string) => {
                const event = state.events.find(item => item.id === eventId);

                return event ? event.name : undefined;
            };
        }
    },
});
