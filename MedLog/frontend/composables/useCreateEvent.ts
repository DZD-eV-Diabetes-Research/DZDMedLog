// Simple function to createa an event

export async function useCreateEvent(name: string, study_id:string): Promise<void>{
    const tokenStore = useTokenStore()
    const { $medlogapi } = useNuxtApp();

    tokenStore.error = ""
    
    let body = {"name": name}
    
    try {        
        await $medlogapi("/api/study/{studyId}/event", {
            method: "POST",
            body: body,
            path: {
                studyId: study_id
            }
        })      
    }
    catch (err: any) {
        throw err
    }
}