import { useMedlogapi } from "#open-fetch";
import type { SchemaIntake } from "#open-fetch-schemas/medlogapi";

export default async function (studyId: string, interviewId: string, intakeId: string): Promise<SchemaIntake> {
    const { data, error } = await useMedlogapi('/api/study/{study_id}/interview/{interview_id}/intake/{intake_id}', {
        path: {
            study_id: studyId,
            interview_id: interviewId,
            intake_id: intakeId,
        }
    });

    if (error.value) {
        throw error.value;
    }

    if (!data.value) {
        throw new Error('No data returned.');
    }

    return data.value;
}
