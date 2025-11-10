import { defineStore } from 'pinia'
import type { MedlogapiResponse } from '#open-fetch';

export type Interview = MedlogapiResponse<'get_interview_api_study__study_id__event__event_id__interview__interview_id__get'>

interface InterviewsStore {
    interviews: Interview[]
}

export const useInterviewStore = defineStore('interviews', {
    state: (): InterviewsStore => ({
        interviews: [],
    }),
});
