<template>
    <div class="flex flex-col justify-center items-center">
        <div class="flex flex-row justify-center">
            <UButton @click="openCopyIntakeModal()" color="green" variant="soft" label="Medikationsübernahme"
                style="margin-right: 10px"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
            <div class="flex items-center ">
                <UTooltip :delay-duration="0" text="Medikatmente aus dem letzten Event übernehmen">
                    <UIcon name="i-heroicons-question-mark-circle" class="size-5" />
                </UTooltip>
            </div>
        </div>
        <UModal v-model="openCopyPreviousIntakesModal" class="custom-modal">
            <div class="p-10 text-center max-w-5xl">
                <div v-if="previousIntakes.length > 0">
                    <div class="flex flex-col items-center space-y-2">
                        <h3 class="text-xl font-light">Medikationsübernahme</h3>
                        <h5 class="text-md font-light">Des Events: <span class="text-md font-bold">{{ lastEventName }}</span></h5>
                        <h5 class="text-md font-light">Letzte Änderung: <span class="text-md font-bold">{{ lastEventDate }}</span></h5>
                    </div>
                    <UTable v-model="selecteIntakes" :columns="columns" :rows="previousIntakes" />
                    <UButton @click="saveIntakes()" label="Medikation Übernehmen" color="green" variant="soft"
                        style="margin-right: 10px"
                        class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white  mt-4" />
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
const tokenStore = useTokenStore();
const route = useRoute();

const openCopyPreviousIntakesModal = ref(false)
const errorMessage = ref(false)

const previousIntakes = ref<any[]>([])
const selecteIntakes = ref([])

const lastEventName = ref("")
const lastEventDate = ref("")

async function openCopyIntakeModal() {
    openCopyPreviousIntakesModal.value = true
    errorMessage.value = false
    
    try {
        const intakes = await $fetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/interview/last/intake/details`, {
            method: "GET",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        })

        lastEventName.value = intakes[0].event.name
        lastEventDate.value = new Date(intakes[0].interview.interview_end_time_utc)
        console.log(lastEventDate.value);
        console.log(typeof(lastEventDate.value));
        
        
        
        previousIntakes.value = Array.isArray(intakes) ? intakes.map((intake: any) => ({
            Medikament: intake.drug.trade_name,
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
            }
        })) : []
        selecteIntakes.value = previousIntakes.value

    } catch (error) {
        console.log(error);
        errorMessage.value = true
        previousIntakes.value = []
    }
}

const columns = [{
    key: 'Medikament',
    label: 'Medikament'
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

async function saveIntakes() {
    for (const element of selecteIntakes.value) {
        try {
            await $fetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake`, {
            method: "POST",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
            body: element.postBody 
        })
        } catch (error) {
            console.log(error);
        }
    }
    props.onUpdate();
    openCopyPreviousIntakesModal.value = false
}

</script>