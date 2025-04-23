export async function useCreateEvent(name: string, study_id:string): Promise<void>{
    const tokenStore = useTokenStore()
    const { $api } = useNuxtApp();

    tokenStore.error = ""
    
    let body = {"name": name}
    
    try {        
        const runtimeConfig = useRuntimeConfig()
        const data = await $api(runtimeConfig.public.baseURL + "study/" + study_id + "/event", {
            method: "POST",
            body,
        })      
    }
    catch (err: any) {
        throw err
    }
}
