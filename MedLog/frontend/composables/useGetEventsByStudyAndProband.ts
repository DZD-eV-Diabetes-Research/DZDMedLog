import { useMedlogapi } from "#open-fetch";
import type { SchemaEventReadPerProband } from "#open-fetch-schemas/medlogapi";

export default async function (studyId: string, probandId: string): Promise<SchemaEventReadPerProband[]> {
    const { data, error } = await useMedlogapi('/api/study/{study_id}/proband/{proband_id}/event', {
        path: {
            study_id: studyId,
            proband_id: probandId,
        }
    });

    if (error.value) {
        throw error.value;
    }

    return data.value?.items ?? [];
}
