import { useMedlogapi } from "#open-fetch";
import type { SchemaInterview } from "#open-fetch-schemas/medlogapi";

export default async function (studyId: string, probandId: string): Promise<SchemaInterview | undefined> {
    const { data, error } = await useMedlogapi('/api/study/{study_id}/proband/{proband_id}/interview/current', {
        path: {
            study_id: studyId,
            proband_id: probandId,
        }
    });

    if (error.value) {
        throw error.value;
    }

    return data.value ?? undefined;
}
