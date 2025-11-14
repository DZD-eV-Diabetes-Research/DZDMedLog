// Helper to create Interview
import { useMedlogapi, type MedlogapiResponse } from "#open-fetch";

type Interview = MedlogapiResponse<'create_interview_api_study__study_id__event__event_id__interview_post'>

export async function useCreateInterview(studyId:string, eventId:string, probandExternalId: string, probandHasTakenMeds:boolean): Promise<Interview | null>{
    const body = {
        "proband_external_id": probandExternalId,
        "proband_has_taken_meds": probandHasTakenMeds,
    }

    const { data, error } = await useMedlogapi("/api/study/{study_id}/event/{event_id}/interview", {
        method: "POST",
        body: body,
        path: {
            study_id: studyId,
            event_id: eventId
        }
    })

    if (error.value) {
        throw error.value;
    }

    return data.value;
}
