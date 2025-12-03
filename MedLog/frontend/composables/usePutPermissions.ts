import { useMedlogapi } from "#open-fetch";
import type { SchemaStudyPermissionRead } from "#open-fetch-schemas/medlogapi";

export default async function (studyId: string, userId: string, body: any): Promise<SchemaStudyPermissionRead | null> {
    const { data, error } = await useMedlogapi('/api/study/{study_id}/permissions/{user_id}', {
        method: "PUT",
        path: {
            study_id: studyId,
            user_id: userId,
        },
        body: body,
    });

    if (error.value) {
        throw error.value;
    }

    return data.value;
}
