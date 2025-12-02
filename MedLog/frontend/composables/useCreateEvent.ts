// Simple function to create an event

export async function useCreateEvent(name: string, study_id:string): Promise<void>{
    const { $medlogapi } = useNuxtApp();

    await $medlogapi("/api/study/{studyId}/event", {
        method: "POST",
        path: {
            studyId: study_id
        },
        body: {
            name: name
        }
    })
}
