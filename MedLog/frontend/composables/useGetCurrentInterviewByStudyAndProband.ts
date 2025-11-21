import { useMedlogapi } from "#open-fetch";
import type { Interview } from "~/stores/interviewStore";

export default async function (studyId: string, probandId: string): Promise<Interview | undefined> {
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
