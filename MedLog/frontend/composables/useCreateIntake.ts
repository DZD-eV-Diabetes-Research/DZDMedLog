export async function useCreateIntake(study_id:string, interview_id:string, pzn: string, intake_start_time:string, dose_unit:number, meds_today:boolean): Promise<void>{
    const tokenStore = useTokenStore()
    tokenStore.error = ""
    
    let body = {"pharmazentralnummer": pzn,
                "intake_start_time_utc": intake_start_time,
                "as_needed_dose_unit": dose_unit,
                "dose_per_day": dose_unit,
                "consumed_meds_today": meds_today
    }    

    try {
        const runtimeConfig = useRuntimeConfig()
        const response = await $fetch(runtimeConfig.public.baseURL + "study/" + study_id + "/interview/" + interview_id + "/intake", {
            method: "POST",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
            body,
        })
        return response     
    }
    catch (err: any) {
        tokenStore.error = err.response.data.detail
    }
}
