// Helper to create Interview
import { useMedlogapi } from "#open-fetch";
import type {SchemaInterviewCreateApi} from "#open-fetch-schemas/medlogapi";

export async function useCreateInterview(studyId:string, eventId:string, probandExternalId: string, probandHasTakenMeds:boolean): Promise<SchemaInterviewCreateApi | null>{
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
