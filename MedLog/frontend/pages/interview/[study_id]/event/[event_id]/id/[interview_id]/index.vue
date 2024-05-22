<template>
    <Layout>
        <div style="text-align: center">
            <h4>{{ study.display_name }}</h4>
            <h5>{{ studyStore.event }}</h5>
        </div>
        <br>
        <UIBaseCard :naked="true">
            <UButton @click="showForm = !showForm" label="Create Intake" color="green" variant="soft"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
        </UIBaseCard>
        <div v-if="showForm">
            <UIBaseCard>
                <IntakeQuestion />
                <div v-if="drugStore.item">
                    <br>
                    <p>Medikament: {{ drugStore.item.item.name }}</p>
                    <p>PZN: {{ drugStore.item.pzn }}</p>
                    <p>Packungsgroesse: {{ drugStore.item.item.packgroesse }}</p>
                </div>
                <UFormGroup label="Dosis">
                    <UInput type="number" v-model="dose"/>
                </UFormGroup>
                <UFormGroup label="Einnahme (Uhrzeit)">
                    <UInput type="date" v-model="time"/>
                </UFormGroup>
                <URadioGroup v-model="selected" legend="Wurden heute Medikamente eingenommen?" :options="options" />
                <UButton @click="saveIntake" label="Save Intake" color="green" variant="soft"
                    class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
            </UIBaseCard>
        </div>
        <UIBaseCard>
            <h4>Medikamenteneinnahme von Proband: {{ interview.proband_external_id }}</h4>
            <div v-if="intakes.length > 0">
                <ul v-for="intake in intakes" :key="intake.id">
                    <li>
                        test: {{ drugDetailsMap[intake.pharmazentralnummer] }}
                        <p>PZN: {{ intake.pharmazentralnummer }}</p>
                    </li>
                </ul>
            </div>
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { watchEffect } from 'vue';


const route = useRoute()
const tokenStore = useTokenStore()
const drugStore = useDrugStore()
const studyStore = useStudyStore()
const runtimeConfig = useRuntimeConfig()

drugStore.item = null

const { data: interview } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/event/${route.params.event_id}/interview/${route.params.interview_id}`, {
    method: "GET",
    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

const { data: intakes, refresh } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake`, {
    method: "GET",
    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

const study = await studyStore.getStudy(route.params.study_id)

const showForm = ref(false)

const options = [{
  value: "Yes",
  label: 'Ja'
}, {
  value: "No",
  label: 'Nein', 
}, {
    value: "UNKNOWN",
    label: "Unbekannst"
}]

const selected = ref("Yes")
const time = ref(null)
const dose = ref(null)

const drugDetailsMap = ref({});

async function fetchDrugDetails(pzn) {
    if (!drugDetailsMap.value[pzn]) {
        const response = await useFetch(`${runtimeConfig.public.baseURL}drug/by-pzn/${pzn}`, {
            method: "GET",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        });
        drugDetailsMap.value[pzn] = response.data;
    }
}

watchEffect(() => {
    intakes.value.forEach(intake => {
        fetchDrugDetails(intake.pharmazentralnummer);
    });
});

async function saveIntake() {
    // const bool = selected.value === "true" ? true : false
    const date = dayjs(time.value).utc().format("YYYY-MM-DD")
    const pzn =  drugStore.item.pzn
    const myDose = dose.value.toString()

    try {        
        showForm.value = false;
        const responseData = await useCreateIntake(route.params.study_id, route.params.interview_id, pzn, date, myDose, selected.value);
        console.log(responseData);
        refresh()
    } catch (error) {
        console.error("Failed to create Intake: ", error);
    }
    console.log(bool, date, dose.value, drugStore.item.pzn); 
}

</script>