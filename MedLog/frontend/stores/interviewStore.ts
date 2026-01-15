import { defineStore, usePatchInterview  } from '#imports'
import type { SchemaInterview } from '#open-fetch-schemas/medlogapi';

interface InterviewsStore {
    interviews: SchemaInterview[]
}

export const useInterviewStore = defineStore('interviews', {
    state: (): InterviewsStore => ({
        interviews: [],
    }),
    actions: {
        async endInterview(studyId: string, eventId: string, interviewId: string) {
            await usePatchInterview(studyId, eventId, interviewId, {
                interview_end_time_utc: new Date().toISOString()
            });
        }
    },
});
