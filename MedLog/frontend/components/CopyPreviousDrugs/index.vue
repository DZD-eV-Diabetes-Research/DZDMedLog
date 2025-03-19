<template>
    <div class="flex flex-col justify-center items-center">
        <div class="flex flex-row justify-center">
            <UButton @click="openCopyIntakeModal()" label="Medikation Übernehmen" color="green" variant="soft"
                style="margin-right: 10px"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
            <div class="flex items-center ">
                <UTooltip :delay-duration="0" text="Medikatmente aus dem letzten Events übernehmen">
                    <UIcon name="i-heroicons-question-mark-circle" class="size-5" />
                </UTooltip>
            </div>
        </div>
        <UModal v-model="copyPreviousIntakesModal" class="custom-modal">
            <div class="p-10 text-center max-w-5xl">
                <div v-if="previousIntakes">
                    <UTable v-model="selecteIntakes" :rows="test2"/>
                    <UButton @click="test()" label="Medikation Übernehmen" color="green" variant="soft"
                        style="margin-right: 10px"
                        class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white  mt-4" />
                </div>
                <div v-if="!previousIntakes && !errorMessage">
                    loading
                </div>
                <div v-if="errorMessage">
                    <h3 class="text-red-500">Es gab ein Problem beim Laden der Medikamente. Bitte melden Sie sich bei
                        ihrem Admin</h3>
                </div>
            </div>
        </UModal>
        {{ previousIntakes }}
    </div>
</template>

<script setup lang="ts">

const runtimeConfig = useRuntimeConfig();
const tokenStore = useTokenStore();
const route = useRoute();

const copyPreviousIntakesModal = ref(false)
const errorMessage = ref(false)

const previousIntakes = ref<any[]>([])
// const previousIntakes = [ { "Medikament": "65422", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": "Unbekannt" }, { "Medikament": "5dfd1", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": 1 }, { "Medikament": "5dfd1", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": 1 }, { "Medikament": "c7361", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": 2 }, { "Medikament": "d1a12", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": 2 }, { "Medikament": "97a60", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": "Unbekannt" }, { "Medikament": "2451c", "Einnahmebeginn": "2025-03-18", "Einnahmeende": "Unbekannt", "Dosis": "Unbekannt" } ]
const selecteIntakes = ref([])

async function openCopyIntakeModal() {
    copyPreviousIntakesModal.value = true
    errorMessage.value = false
    try {
        //`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/interview/current/intake`
        const intakes = await $fetch(`${runtimeConfig.public.baseURL}study/b6f2c61b-d388-4412-8c9a-461ece251116/proband/1234/interview/current/intake`, {
            method: "GET",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        })

        previousIntakes.value = Array.isArray(intakes) ? intakes.map((intake: any) => ({
            Medikament: intake.drug_id.substring(0, 5),
            Einnahmebeginn: intake.intake_start_time_utc || 'Unbekannt',
            Einnahmeende: intake.intake_end_time_utc || 'Unbekannt',
            Dosis: intake.dose_per_day || 'Unbekannt',
        })) : []

    } catch (error) {
        console.log(error);
        errorMessage.value = true
        previousIntakes.value = []
    }
}

function test() {
    console.log("speichert");
    copyPreviousIntakesModal.value = false
}

const test2 = [
  {
    "intake_start_time_utc": "2025-03-18",
    "drug_id": "65422f38-18b5-47e0-95a6-5f073b18cf09",
    "source_of_drug_information": "Study participant: verbal specification",
    "administered_by_doctor": null,
    "dose_per_day": 0,
    "as_needed_dose_unit": null,
    "id": "7a0672fe-43f9-463a-adcd-8bbbffabac6f",
    "created_at": "2025-03-18T10:06:58.461556",
    "intake_end_time_utc": null,
    "intake_regular_or_as_needed": "as needed",
    "regular_intervall_of_daily_dose": null,
    "consumed_meds_today": "Yes",
    "interview_id": "8f2f9697-7233-41fa-96da-c53005126d8a"
  },
  {
    "intake_start_time_utc": "2025-03-18",
    "drug_id": "5dfd1d75-ab94-4f46-83e2-28f2551bf0a2",
    "source_of_drug_information": "Study participant: medication plan",
    "administered_by_doctor": null,
    "dose_per_day": 1,
    "as_needed_dose_unit": null,
    "id": "6f3a0b7c-8e97-4d47-89fc-e7a0420d69f0",
    "created_at": "2025-03-18T10:09:09.050519",
    "intake_end_time_utc": null,
    "intake_regular_or_as_needed": "regular",
    "regular_intervall_of_daily_dose": "every 2. day",
    "consumed_meds_today": "Yes",
    "interview_id": "8f2f9697-7233-41fa-96da-c53005126d8a"
  },
  {
    "intake_start_time_utc": "2025-03-18",
    "drug_id": "5dfd1d75-ab94-4f46-83e2-28f2551bf0a2",
    "source_of_drug_information": "Study participant: medication plan",
    "administered_by_doctor": null,
    "dose_per_day": 1,
    "as_needed_dose_unit": null,
    "id": "873fc2b2-0d04-4982-a093-8dfa85cb734a",
    "created_at": "2025-03-18T10:09:37.650357",
    "intake_end_time_utc": null,
    "intake_regular_or_as_needed": "regular",
    "regular_intervall_of_daily_dose": "every 2. day",
    "consumed_meds_today": "Yes",
    "interview_id": "8f2f9697-7233-41fa-96da-c53005126d8a"
  },
  {
    "intake_start_time_utc": "2025-03-18",
    "drug_id": "c7361ac5-212f-43de-b42c-db5c0d4a129c",
    "source_of_drug_information": "Study participant: Medication prescription",
    "administered_by_doctor": null,
    "dose_per_day": 2,
    "as_needed_dose_unit": null,
    "id": "73584eaa-7548-4d75-9124-e1bbe49c496d",
    "created_at": "2025-03-18T10:10:38.862953",
    "intake_end_time_utc": null,
    "intake_regular_or_as_needed": "regular",
    "regular_intervall_of_daily_dose": "every 4. day / twice a week",
    "consumed_meds_today": "Yes",
    "interview_id": "8f2f9697-7233-41fa-96da-c53005126d8a"
  },
  {
    "intake_start_time_utc": "2025-03-18",
    "drug_id": "d1a12283-10e1-4b95-ba5b-c114ead29cbe",
    "source_of_drug_information": "Study participant: Medication prescription",
    "administered_by_doctor": null,
    "dose_per_day": 2,
    "as_needed_dose_unit": null,
    "id": "6a498a2e-0516-4786-a76d-80408317086f",
    "created_at": "2025-03-18T10:11:04.582381",
    "intake_end_time_utc": null,
    "intake_regular_or_as_needed": "regular",
    "regular_intervall_of_daily_dose": "every 4. day / twice a week",
    "consumed_meds_today": "Yes",
    "interview_id": "8f2f9697-7233-41fa-96da-c53005126d8a"
  },
  {
    "intake_start_time_utc": "2025-03-18",
    "drug_id": "97a60a15-c19d-4dfa-8ccd-343dda4af2a3",
    "source_of_drug_information": "Study participant: verbal specification",
    "administered_by_doctor": null,
    "dose_per_day": 0,
    "as_needed_dose_unit": null,
    "id": "15c9edbd-a278-47f5-86d1-001d8cb0f889",
    "created_at": "2025-03-18T10:19:13.739106",
    "intake_end_time_utc": null,
    "intake_regular_or_as_needed": "as needed",
    "regular_intervall_of_daily_dose": null,
    "consumed_meds_today": "Yes",
    "interview_id": "8f2f9697-7233-41fa-96da-c53005126d8a"
  },
  {
    "intake_start_time_utc": "2025-03-18",
    "drug_id": "2451c9e8-38fb-4983-8f7b-980c93766f44",
    "source_of_drug_information": "Study participant: verbal specification",
    "administered_by_doctor": null,
    "dose_per_day": 0,
    "as_needed_dose_unit": null,
    "id": "04700e63-74b1-48dc-ab34-09d120b51b5f",
    "created_at": "2025-03-18T10:30:20.626756",
    "intake_end_time_utc": null,
    "intake_regular_or_as_needed": "as needed",
    "regular_intervall_of_daily_dose": null,
    "consumed_meds_today": "Yes",
    "interview_id": "8f2f9697-7233-41fa-96da-c53005126d8a"
  }
]

</script>