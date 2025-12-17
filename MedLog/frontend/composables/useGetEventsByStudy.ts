import { useMedlogapi } from "#open-fetch";
import type { SchemaEvent } from "#open-fetch-schemas/medlogapi";

export default async function (studyId: string): Promise<SchemaEvent[]> {
    const { data, error } = await useMedlogapi('/api/study/{study_id}/event', {
        path: {
            study_id: studyId,
        }
    });

    if (error.value) {
        throw error.value;
    }

    return data.value?.items ?? [];
}
