import { useMedlogapi } from "#open-fetch";
import type { SchemaStudyUpdate } from "#open-fetch-schemas/medlogapi";

export default async function (studyId: string, body: any): Promise<SchemaStudyUpdate> {
    const { data, error } = await useMedlogapi('/api/study/{study_id}', {
        method: "PATCH",
        path: {
            study_id: studyId,
        },
        body,
    });

    if (error.value) {
        throw error.value;
    }

    if (!data.value) {
        throw new Error('No data returned.');
    }

    return data.value;
}
