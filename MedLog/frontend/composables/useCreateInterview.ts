// Helper to create Interview

export async function useCreateInterview(study_id:string, event_id:string, proband_external_id: string, proband_has_taken_meds:boolean, interview_number:number): Promise<any>{
    const tokenStore = useTokenStore()
    const { $medlogapi } = useNuxtApp();

    tokenStore.error = ""
    
    let body = {"proband_external_id": proband_external_id,
                "proband_has_taken_meds": proband_has_taken_meds,
                "interview_number": interview_number
    }    

    try {
        const response = await $medlogapi("/api/study/{studyId}/event/{eventId}/interview", {
            method: "POST",
            body: body,
            path: {
                studyId: study_id,
                eventId: event_id
            }
        })
        return response     
    }
    catch (err: any) {
        tokenStore.error = err.response.data.detail
    }
}