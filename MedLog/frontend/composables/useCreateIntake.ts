import useDrugSourceTranslator from "./useDrugSourceTranslator"
import useIntervallDoseTranslator from "./useIntervallDoseTranslator"

export async function useCreateIntake(study_id: string, interview_id: string, pzn: string | null = null, source_of_drug_information: string, intake_start_time: string, intake_end_time: string | null = null, intake_regular_or_as_needed: string, regular_intervall_of_daily_dose: string| null | undefined, dose_unit: number, meds_today: boolean, custom_drug_id: string | null = null): Promise<void> {
    
    const tokenStore = useTokenStore()
    tokenStore.error = ""

    let body = {
        "custom_drug_id": custom_drug_id,
        "pharmazentralnummer": pzn,
        "source_of_drug_information": source_of_drug_information,
        "intake_start_time_utc": intake_start_time,
        "intake_end_time_utc": intake_end_time,
        "intake_regular_or_as_needed": intake_regular_or_as_needed,
        "dose_per_day": dose_unit,
        "regular_intervall_of_daily_dose": regular_intervall_of_daily_dose,
        "as_needed_dose_unit": null,
        "consumed_meds_today": meds_today
    }    

    console.log(body);
    

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
