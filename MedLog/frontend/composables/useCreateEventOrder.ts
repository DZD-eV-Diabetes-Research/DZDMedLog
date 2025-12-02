// Simple function to create an event

export default async function (studyId:string, events: string[]) {
    const { $medlogapi } = useNuxtApp();

    return await $medlogapi("/api/study/{studyId}/event/order", {
        method: "POST",
        path: {
            studyId: studyId
        },
        body: events
    })
}
