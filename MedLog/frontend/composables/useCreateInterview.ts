// Helper to create Interview

export async function useCreateInterview(study_id:string, event_id:string, proband_external_id: string, proband_has_taken_meds:boolean, interview_number:number): Promise<any>{
    const tokenStore = useTokenStore()
    const { $api } = useNuxtApp();

    tokenStore.error = ""
    
    let body = {"proband_external_id": proband_external_id,
                "proband_has_taken_meds": proband_has_taken_meds,
                "interview_number": interview_number
    }    

    try {
        const runtimeConfig = useRuntimeConfig()
        const response = await $api(runtimeConfig.public.baseURL + "study/" + study_id + "/event/" + event_id + "/interview", {
            method: "POST",
            body,
        })
        return response     
    }
    catch (err: any) {
        tokenStore.error = err.response.data.detail
    }
}