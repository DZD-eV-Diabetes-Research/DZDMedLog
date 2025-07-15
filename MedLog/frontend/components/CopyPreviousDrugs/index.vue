<!-- This component serves to copy the intakes of the previous event -->

<template>
    <div class="flex flex-col justify-center items-center">
        <div class="flex flex-row justify-center">
            <UButton @click="openCopyIntakeModal()" color="green" variant="soft" label="Medikationsübernahme"
                style="margin-right: 10px"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
        </div>
        <UModal v-model="openCopyPreviousIntakesModal" :ui="{ width: 'lg:max-w-6xl' }">
            <div class="p-10 text-center">
                <div v-if="previousIntakes.length > 0">
                    <div class="flex flex-col items-center space-y-2 mb-6">
                        <h3 class="text-2xl font-normal mb-2">Medikationsübernahme</h3>
                        <h5 class="text-md font-light">Des Events: <span class="text-md font-bold">{{ lastEventName
                        }}</span></h5>
                        <h5 class="text-md font-light">Letzte Änderung: <span class="text-md font-bold">{{ lastEventDate
                        }}</span></h5>
                    </div>
                    <UTable v-model="selectedIntakes" :columns="columns" :rows="previousIntakes"
                        class="border border-slate-400 rounded-md" />
                    <UButton @click="saveIntakes()" label="Medikation Übernehmen" color="green" variant="soft"
                        style="margin-right: 10px"
                        class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white  mt-8" />
                </div>
                <div v-if="previousIntakes.length === 0">
                    <h3>Es gibt keine Einträge im letzten Event</h3>
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
    </div>
</template>

<script setup lang="ts">
const props = defineProps<{ onUpdate: () => void }>();

const runtimeConfig = useRuntimeConfig();
const { $medlogapi } = useNuxtApp();
const route = useRoute();

const openCopyPreviousIntakesModal = ref(false)
const errorMessage = ref(false)

const previousIntakes = ref<any[]>([])
const selectedIntakes = ref([])
const lastEventName = ref("")
const lastEventDate = ref("")

// Backend interaction

async function openCopyIntakeModal() {
    openCopyPreviousIntakesModal.value = true
    errorMessage.value = false

    try {
        const intakes = await $medlogapi(`/api/study/${route.params.study_id}/proband/${route.params.proband_id}/interview/last/intake/details`)


        lastEventName.value = intakes[0]?.event.name
        lastEventDate.value = new Date(intakes[0]?.interview.interview_end_time_utc).toLocaleDateString("de-DE", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
        });

        // Transform the API response into a format suitable for both the UI and the POST request body
        previousIntakes.value = Array.isArray(intakes) ? intakes.map((intake: any) => ({
            Medikament: intake.drug.trade_name,
            Custom: intake.drug?.is_custom_drug ? "Ja" : "Nein",
            Einnahmebeginn: intake.intake_start_time_utc || 'Unbekannt',
            Einnahmeende: intake.intake_end_time_utc || 'Unbekannt',
            Dosis: intake.dose_per_day || 'Unbekannt',
            ID: intake.id,
            postBody: {
                "drug_id": intake.drug_id,
                "source_of_drug_information": intake.source_of_drug_information,
                "intake_start_time_utc": intake.intake_start_time_utc,
                "intake_end_time_utc": intake.intake_end_time_utc,
                "administered_by_doctor": intake.administered_by_doctor,
                "intake_regular_or_as_needed": intake.intake_regular_or_as_needed,
                "dose_per_day": intake.dose_per_day,
                "regular_intervall_of_daily_dose": intake.regular_intervall_of_daily_dose,
                "as_needed_dose_unit": intake.as_needed_dose_unit,
                "consumed_meds_today": intake.consumed_meds_today,
            },
            // Simple css class to highlight the custom drugs yellow 
            class: intake.drug?.is_custom_drug
                ? "bg-yellow-50"
                : null,
        })) : []
        selectedIntakes.value = previousIntakes.value

    } catch (error) {
        console.log(error);
        errorMessage.value = true
        previousIntakes.value = []
    }
}

async function saveIntakes() {
    for (const element of selectedIntakes.value) {
        try {
            await $medlogapi(`/api/study/${route.params.study_id}/interview/${route.params.interview_id}/intake`, {
                method: "POST",
                body: element.postBody
            })
        } catch (error) {
            console.log(error);
        }
    }

    // Call the parent component's update handler (prop) after saving
    props.onUpdate();
    openCopyPreviousIntakesModal.value = false
}


// Template / UI Interaction

const columns = [{
    key: 'Medikament',
    label: 'Medikament'
}, {
    key: 'Custom',
    label: 'Custom'
}, {
    key: 'Einnahmebeginn',
    label: 'Einnahmebeginn'
}, {
    key: 'Einnahmeende',
    label: 'Einnahmeende'
}, {
    key: 'Dosis',
    label: 'Dosis'
},]

</script>