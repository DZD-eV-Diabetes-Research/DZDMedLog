import { useMedlogapi, type MedlogapiResponse } from "#open-fetch";

export type Intakes = MedlogapiResponse<'list_all_intakes_detailed_api_study__study_id__proband__proband_id__intake_details_get'>['items']

export default async function (studyId: string, probandId: string, interviewId?: string): Promise<Intakes> {
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
