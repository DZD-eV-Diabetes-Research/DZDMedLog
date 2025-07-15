// Helper to create an Intake

export async function useCreateIntake(study_id: string, interview_id: string, administered_by_doctor: string | "prescribed", source_of_drug_information: string, intake_start_time: string, intake_end_time: string | null = null, intake_regular_or_as_needed: string, regular_intervall_of_daily_dose: string| null | undefined, dose_unit: number, meds_today: boolean, drug_id: string | null = null): Promise<void> {
    
    const tokenStore = useTokenStore()
    const { $medlogapi } = useNuxtApp();

    tokenStore.error = ""

    let body = {
        "drug_id": drug_id,
        "source_of_drug_information": source_of_drug_information,
        "intake_start_time_utc": intake_start_time,
        "intake_end_time_utc": intake_end_time,
        "administered_by_doctor": administered_by_doctor,
        "intake_regular_or_as_needed": intake_regular_or_as_needed,
        "dose_per_day": dose_unit,
        "regular_intervall_of_daily_dose": regular_intervall_of_daily_dose,
        "as_needed_dose_unit": null,
        "consumed_meds_today": meds_today
    }            

    try {
        const runtimeConfig = useRuntimeConfig()
        const response = await $medlogapi("/api/study/" + study_id + "/interview/" + interview_id + "/intake", {
            method: "POST",
            body: body,
        })    
        return response     
    }
    catch (err: any) {        
        console.log(err);
        tokenStore.error = err.response.data.detail
    }
}