// Store to handle to current studies

import { useMedlogapi } from "#open-fetch";
import type { SchemaStudy } from "#open-fetch-schemas/medlogapi";
import { defineStore } from '#imports'

interface StudyState {
    studies: SchemaStudy[],
}

export const useStudyStore = defineStore('StudyStore', {

    state: (): StudyState => ({
        studies: [],
    }),
    actions: {
        getStudy(id: string) {
            return this.studies.find(item => item.id === id)
        },
        async loadAvailableStudies() {
            const { data, error } = await useMedlogapi("/api/study", {
                query: {
                    show_deactived: true,
                }
            })
            if (error.value) {
                throw error.value;
            }

            this.studies = data.value?.items ?? [];
        },
        upsertStudy(studyToUpsert: SchemaStudy) {
            const indexOfExistingStudy = this.studies.findIndex(study => study.id === studyToUpsert.id);
            if (indexOfExistingStudy !== -1) {
                this.studies[indexOfExistingStudy] = studyToUpsert;
            } else {
                this.studies.push(studyToUpsert);
            }
        },
    },
    getters: {
        activeStudies(state: StudyState) {
            return state.studies.filter(study => study.deactivated === false);
        },
        nameForStudy(state: StudyState) {
            return (studyId: string) => {
                const study = state.studies.find(item => item.id === studyId);

                return study ? study.display_name : undefined;
            };
        }
    },
})
