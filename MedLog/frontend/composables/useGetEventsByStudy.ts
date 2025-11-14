import { useMedlogapi } from "#open-fetch";
import type { Events } from "~/stores/eventStore";

export default async function (studyId: string): Promise<Events> {
    const { data, error } = await useMedlogapi('/api/study/{study_id}/event', {
        path: {
            study_id: studyId,
        }
    });

    if (error.value) {
        throw error.value;
    }

    return data.value?.items ?? [];
}
