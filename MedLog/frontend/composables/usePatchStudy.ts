import { useMedlogapi } from "#open-fetch";
import type { SchemaStudyApiRead, SchemaStudyUpdate } from "#open-fetch-schemas/medlogapi";

export default async function (studyId: string, body: SchemaStudyUpdate, confirmNormalizationChange: boolean = false): Promise<SchemaStudyApiRead> {
    let query: { confirm_normalization_change?: boolean } = {};

    if (confirmNormalizationChange) {
        query = {
            confirm_normalization_change: confirmNormalizationChange,
        };
    }

    const { data, error } = await useMedlogapi('/api/study/{study_id}', {
        method: "PATCH",
        path: {
            study_id: studyId,
        },
        body,
        query: query
    });

    if (error.value) {
        throw error.value;
    }

    if (!data.value) {
        throw new Error('No data returned.');
    }

    return data.value;
}
