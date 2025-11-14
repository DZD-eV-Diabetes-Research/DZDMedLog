import { useMedlogapi } from "#open-fetch";
import type { Interview } from "~/stores/interviewStore";

export default async function (studyId: string, eventId: string, interviewId: string): Promise<Interview | null> {
    const { data, error } = await useMedlogapi('/api/study/{study_id}/event/{event_id}/interview/{interview_id}', {
        path: {
            study_id: studyId,
            event_id: eventId,
            interview_id: interviewId,
        }
    });

    if (error.value) {
        throw error.value;
    }

    return data.value;
}
