export async function useCreateInterview(study_id:string, event_id:string, proband_external_id: string, proband_has_taken_meds:boolean, interview_number:number): Promise<void>{
    const tokenStore = useTokenStore()
    tokenStore.error = ""
    
    let body = {"proband_external_id": proband_external_id,
                "proband_has_taken_meds": proband_has_taken_meds,
                "interview_number": interview_number
    }    

    try {
        const runtimeConfig = useRuntimeConfig()
        const data = await $fetch(runtimeConfig.public.baseURL + "study/" + study_id + "/event/" + event_id + "/interview", {
            method: "POST",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
            body,
        })      
    }
    catch (err: any) {
        tokenStore.error = err.response.data.detail
    }
}
