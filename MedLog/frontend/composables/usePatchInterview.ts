import { useMedlogapi } from "#open-fetch";
import type { SchemaInterviewUpdateApi, SchemaInterview } from "#open-fetch-schemas/medlogapi";

export default async function (studyId: string, eventId: string, interviewId: string, body: SchemaInterviewUpdateApi): Promise<SchemaInterview> {
    const { data, error } = await useMedlogapi('/api/study/{study_id}/event/{event_id}/interview/{interview_id}', {
        method: "PATCH",
        path: {
            study_id: studyId,
            event_id: eventId,
            interview_id: interviewId,
        },
        body,
    });

    if (error.value) {
        throw error.value;
    }

    if (!data.value) {
        throw new Error('No data.');
    }

    return data.value;
}
