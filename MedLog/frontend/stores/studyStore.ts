// Store to handle to current studies

import { useMedlogapi } from "#open-fetch";
import type { SchemaStudyApiRead } from "#open-fetch-schemas/medlogapi";
import { defineStore, useCreateStudy } from '#imports'

interface StudyState {
    studies: SchemaStudyApiRead[],
}

export const useStudyStore = defineStore('StudyStore', {

    state: (): StudyState => ({
        studies: [],
    }),
    actions: {
        async cloneStudy(existingStudyId: string, newName: string): Promise<SchemaStudyApiRead> {
            const { data, error } = await useMedlogapi("/api/study/{study_id}/clone", {
                method: "POST",
                path: {
                    study_id: existingStudyId,
                },
                body: {
                    display_name: newName,
                }
            })
            if (error.value) {
                throw error.value;
            }

            if (!data.value) {
                throw new Error('Study clone endpoint did not return a new study');
            }

            this.upsertStudy(data.value)
            return data.value
        },
        async createStudy(name: string): Promise<SchemaStudyApiRead> {
            const newStudy = await useCreateStudy(name);
            this.upsertStudy(newStudy);
            return newStudy;
        },
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
        upsertStudy(studyToUpsert: SchemaStudyApiRead) {
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
        allStudies(state: StudyState) {
            return state.studies;
        },
        deactivatedStudies(state: StudyState) {
            return state.studies.filter(study => study.deactivated === true);
        },
        isStudyActive() {
            return (studyId: string) => {
                const study = this.studyById(studyId);
                return study && study.deactivated === false;
            };
        },
        nameForStudy(state: StudyState) {
            return (studyId: string) => {
                const study = state.studies.find(item => item.id === studyId);

                return study ? study.display_name : undefined;
            };
        },
        studyById(state: StudyState) {
            return (studyId: string): SchemaStudyApiRead|undefined => {
                return state.studies.find(item => item.id === studyId);
            };
        },
    },
})
