import { useMedlogapi } from "#open-fetch";

export default async function (studyId: string, body: any) {
    const { data, error } = await useMedlogapi('/api/study/{study_id}', {
        method: "PATCH",
        path: {
            study_id: studyId,
        },
        body,
    });

    if (error.value) {
        throw error.value;
    }

    return data.value;
}
