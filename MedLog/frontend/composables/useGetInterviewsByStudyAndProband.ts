import { useMedlogapi } from "#open-fetch";
import type { Interview } from "~/stores/interviewStore";

export default async function (studyId: string, probandId: string): Promise<Interview[]> {
    const { data, error } = await useMedlogapi('/api/study/{study_id}/proband/{proband_id}/interview', {
        path: {
            study_id: studyId,
            proband_id: probandId,
        }
    });

    if (error.value) {
        throw error.value;
    }

    return data.value ?? [];
}
