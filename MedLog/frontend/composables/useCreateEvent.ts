// Simple function to createa an event

export async function useCreateEvent(name: string, study_id:string): Promise<void>{
    const tokenStore = useTokenStore()
    const { $medlogapi } = useNuxtApp();

    tokenStore.error = ""
    
    let body = {"name": name}
    
    try {        
        const runtimeConfig = useRuntimeConfig()
        await $medlogapi("/api/study/" + study_id + "/event", {
            method: "POST",
            body: body,
        })      
    }
    catch (err: any) {
        throw err
    }
}