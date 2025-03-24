<template>
    <div class="flex flex-col justify-center items-center">
        <div class="flex flex-row justify-center">
            <UButton @click="openCopyIntakeModal()" label="Medikation Übernehmen" color="green" variant="soft"
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
                    <h3>Medikationsübernahme</h3>
                    <UTable v-model="selecteIntakes" :columns="columns" :rows="previousIntakes" />
                    <UButton @click="saveIntakes()" label="Medikation Übernehmen" color="green" variant="soft"
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
        <p v-for="intake in previousIntakes">
            intake: {{ intake }}
            <br>
            <br>
        </p>
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

async function openCopyIntakeModal() {
    openCopyPreviousIntakesModal.value = true
    errorMessage.value = false
    
    try {
<<<<<<< HEAD
        //`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/interview/current/intake`
        const intakes = await $fetch(`${runtimeConfig.public.baseURL}study/b326a6e1-c2d1-4761-8590-05ca50d4e851/proband/1234/interview/current/intake`, {
            method: "GET",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        })
        
        previousIntakes.value = Array.isArray(intakes) ? intakes.map((intake: any) => ({
            Medikament: intake.drug_id,
=======
        const intakes = await $fetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/interview/last/details`, {
            method: "GET",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        })

        console.log(intakes);
        
        previousIntakes.value = Array.isArray(intakes) ? intakes.map((intake: any) => ({
            Medikament: intake.drug.trade_name,
>>>>>>> detailed-last-current-endpoint
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
<<<<<<< HEAD
    loadingSpinner.value = true
    // selecteIntakes.value.forEach(element => {
    //     try {
    //         //`${runtimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake`
    //         await $fetch(`${runtimeConfig.public.baseURL}study/b6f2c61b-d388-4412-8c9a-461ece251116/interview/1234/intake`, {
    //         method: "POST",
    //         headers: { 'Authorization': "Bearer " + tokenStore.access_token },
    //     })

    //     } catch (error) {
    //         console.log(error);
            
    //     }
    // });
    for (const element of selecteIntakes.value) {
        console.log(element.postBody);
        try {
            //`${runtimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake`
            await $fetch(`${runtimeConfig.public.baseURL}study/8713edbc-4190-4ccc-9c2d-21fc75883e77/interview/440ff1cb-0ab3-4a97-a8b5-789ab5830bc1/intake`, {
            method: "POST",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        })

        } catch (error) {
            console.log(error);
    }
}
    loadingSpinner.value = false
=======
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
>>>>>>> detailed-last-current-endpoint
    openCopyPreviousIntakesModal.value = false
}

</script>