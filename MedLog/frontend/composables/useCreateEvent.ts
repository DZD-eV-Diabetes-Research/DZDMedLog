// Simple function to create an event
import { useMedlogapi } from "#open-fetch";
import type { SchemaEventCreateApi } from "#open-fetch-schemas/medlogapi";

export async function useCreateEvent(event: SchemaEventCreateApi, study_id:string) {
    const { data, error } = await useMedlogapi("/api/study/{study_id}/event", {
        method: "POST",
        path: {
            study_id: study_id
        },
        body: event
    })

    if (error.value) {
        throw error.value;
    }

    if (!data.value) {
        throw new Error('No data returned.');
    }

    return data.value;
}
