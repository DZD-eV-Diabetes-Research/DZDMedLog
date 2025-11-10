// Store to handle to current studies

import { type MedlogapiResponse, useMedlogapi } from "#open-fetch";
import { defineStore } from 'pinia'

type Studies = MedlogapiResponse<'list_studies_api_study_get'>['items']

interface StudyState {
    studies: Studies,
}

export const useStudyStore = defineStore('StudyStore', {

    state: (): StudyState => ({
        studies: [],
    }),
    actions: {
        async getAvailableStudies() {
            const { data, error } = await useMedlogapi("/api/study")
            if (error.value) {
                throw error.value;
            }

            this.studies = data.value?.items ?? [];
        },

        async getStudy(id: string) {
            return this.studies.find(item => item.id === id)
        },
    },
    getters: {
        nameForStudy(state: StudyState) {
            return (studyId: string) => {
                const study = state.studies.find(item => item.id === studyId);

                return study ? study.display_name : undefined;
            };
        }
    },
})
