import { useMedlogapi } from "#open-fetch";
import type { SchemaStudyPermissionRead } from "#open-fetch-schemas/medlogapi";

export default async function (studyId: string): Promise<SchemaStudyPermissionRead[]> {
    const { data, error } = await useMedlogapi('/api/study/{study_id}/permissions', {
        path: {
            study_id: studyId,
        }
    });

    if (error.value) {
        throw error.value;
    }

    return data.value?.items ?? [];
}
