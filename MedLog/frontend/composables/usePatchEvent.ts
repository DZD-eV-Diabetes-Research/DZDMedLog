import type { SchemaEvent, SchemaEventUpdate } from "#open-fetch-schemas/medlogapi";

export default async function (studyId: string, eventId: string, body: SchemaEventUpdate): Promise<SchemaEvent> {
    const { $medlogapi } = useNuxtApp();
    const data = await $medlogapi('/api/study/{study_id}/event/{event_id}', {
        method: "PATCH",
        path: {
            study_id: studyId,
            event_id: eventId,
        },
        body,
    });

    if (!data) {
        throw new Error('No data returned.');
    }

    return data;
}
