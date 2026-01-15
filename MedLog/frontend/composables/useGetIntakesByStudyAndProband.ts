import { useMedlogapi } from "#open-fetch";
import type { SchemaIntakeDetailListItem } from "#open-fetch-schemas/medlogapi";

export default async function (studyId: string, probandId: string, interviewId?: string): Promise<SchemaIntakeDetailListItem[]> {
    const { data, error } = await useMedlogapi('/api/study/{study_id}/proband/{proband_id}/intake/details', {
        path: {
            study_id: studyId,
            proband_id: probandId,
        },
        query: {
            interview_id: interviewId,
        }
    });

    if (error.value) {
        throw error.value;
    }

    return data.value?.items ?? [];
}
