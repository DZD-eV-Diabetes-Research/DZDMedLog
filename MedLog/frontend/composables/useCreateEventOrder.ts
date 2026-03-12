// Simple function to create an event

export default async function (studyId:string, events: string[]) {
    const { $medlogapi } = useNuxtApp();

    return await $medlogapi("/api/study/{study_id}/event/order", {
        method: "POST",
        path: {
            study_id: studyId
        },
        body: events
    })
}
