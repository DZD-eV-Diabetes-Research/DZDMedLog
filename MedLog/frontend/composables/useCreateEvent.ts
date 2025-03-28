export async function useCreateEvent(name: string, study_id:string): Promise<void>{
    const tokenStore = useTokenStore()
    tokenStore.error = ""
    
    let body = {"name": name}
    
    try {        
        const runtimeConfig = useRuntimeConfig()
        const data = await $fetch(runtimeConfig.public.baseURL + "study/" + study_id + "/event", {
            method: "POST",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
            body,
        })      
    }
    catch (err: any) {
        throw err
    }
}
