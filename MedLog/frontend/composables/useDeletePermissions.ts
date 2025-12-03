import { useMedlogapi } from "#open-fetch";

export default async function (studyId: string, userId: string) {
    const { error } = await useMedlogapi('/api/study/{study_id}/permissions/{user_id}', {
        method: "DELETE",
        path: {
            study_id: studyId,
            user_id: userId,
        },
    });

    if (error.value) {
        throw error.value;
    }
}
