export async function useCreateIntake(study_id: string, interview_id: string, pzn: string | null = null, source_of_drug_information: string, intake_start_time: string, intake_end_time: string | null = null, intake_regular_or_as_needed: string, regular_intervall_of_daily_dose: string, dose_unit: number, meds_today: boolean, custom_drug_id: string | null = null): Promise<void> {
    const tokenStore = useTokenStore()
    tokenStore.error = ""

    let regular_intervall_of_daily_dose_final: null|string = null
    let dose_unit_final: null|number = null

    if (source_of_drug_information === "Probandenangabe") {
        source_of_drug_information = "Study participant: verbal specification"
    } else if (source_of_drug_information === "Medikamentenpackung: PZN gescannt") {
        source_of_drug_information = "Medication package: Scanned PZN"
    } else if (source_of_drug_information === "Medikamentenpackung: PZN getippt") {
        source_of_drug_information = "Medication package: Typed in PZN"
    } else if (source_of_drug_information === "Medikamentenpackung: Arzneimittelname") {
        source_of_drug_information = "Medication package: Drug name"
    } else if (source_of_drug_information === "Beipackzettel") {
        source_of_drug_information = "Medication leaflet"
    } else if (source_of_drug_information === "Medikamentenplan") {
        source_of_drug_information = "Study participant: medication plan"
    } else if (source_of_drug_information === "Rezept") {
        source_of_drug_information = "Study participant: Medication prescription"
    } else if (source_of_drug_information === "Nacherhebung: Tastatureingabe der PZN") {
        source_of_drug_information = "Follow up via phone/message: Typed in PZN"
    } else if (source_of_drug_information === "Nacherhebung: Arzneimittelname") {
        source_of_drug_information = "Follow up via phone/message: Medication name"
    }


    if (intake_regular_or_as_needed === "regelmäßig") {
        intake_regular_or_as_needed = "regular"
        if (regular_intervall_of_daily_dose === "unbekannt"){
            regular_intervall_of_daily_dose = "Unknown"
        } else if (regular_intervall_of_daily_dose === "täglich") {
            regular_intervall_of_daily_dose = "Daily"
        } else if (regular_intervall_of_daily_dose === "jeden 2. Tag") {
            regular_intervall_of_daily_dose = "every 2. day"
        } else if (regular_intervall_of_daily_dose === "jeden 3. Tag") {
            regular_intervall_of_daily_dose = "every 3. day"
        } else if (regular_intervall_of_daily_dose === "jeden 4. Tag = 2x pro Woche") {
            regular_intervall_of_daily_dose = "every 4. day / twice a week"
        } else {
            regular_intervall_of_daily_dose = "intervals of one week or more"
        }
        regular_intervall_of_daily_dose_final = regular_intervall_of_daily_dose
        dose_unit_final = dose_unit
    } else {
        intake_regular_or_as_needed = "as needed"
    }

   


    let body = {
        "custom_drug_id": custom_drug_id,
        "pharmazentralnummer": pzn,
        "source_of_drug_information": source_of_drug_information,
        "intake_start_time_utc": intake_start_time,
        "intake_end_time_utc": intake_end_time,
        "intake_regular_or_as_needed": intake_regular_or_as_needed,
        "dose_per_day": dose_unit_final,
        "regular_intervall_of_daily_dose": regular_intervall_of_daily_dose_final,
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
