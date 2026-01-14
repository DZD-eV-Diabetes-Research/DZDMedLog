// Simple function to create an event
import { useMedlogapi } from "#open-fetch";

export async function useCreateEvent(name: string, study_id:string) {
    const { data, error } = await useMedlogapi("/api/study/{study_id}/event", {
        method: "POST",
        path: {
            study_id: study_id
        },
        body: {
            name: name
        }
    })

    if (error.value) {
        throw error.value;
    }

    if (!data.value) {
        throw new Error('No data returned.');
    }

    return data.value;
}
