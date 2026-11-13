export default async function (studyId: string, eventId: string): Promise<void> {
    const { $medlogapi } = useNuxtApp();
    await $medlogapi('/api/study/{study_id}/event/{event_id}', {
        method: "DELETE",
        path: {
            study_id: studyId,
            event_id: eventId,
        },

    });
}
