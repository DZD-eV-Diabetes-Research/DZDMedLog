import { useMedlogapi } from "#open-fetch";

export default async function (studyId: string, interviewId: string, intakeId: string): Promise<void> {
    const { error } = await useMedlogapi('/api/study/{study_id}/interview/{interview_id}/intake/{intake_id}', {
        method: "DELETE",
        path: {
            study_id: studyId,
            interview_id: interviewId,
            intake_id: intakeId,
        }
    });

    if (error.value) {
        throw error.value;
    }
}
