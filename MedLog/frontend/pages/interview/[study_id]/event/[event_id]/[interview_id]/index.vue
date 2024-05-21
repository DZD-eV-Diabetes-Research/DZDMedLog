<template>
    <Layout>
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
            <h1>Hello from the other side</h1>
            {{ route.params }}
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';

const route = useRoute()
const tokenStore = useTokenStore()
const drugStore = useDrugStore()
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

const showForm = ref(false)

function createInterview() {
    console.log("test");
}

const options = [{
  value: "true",
  label: 'Ja'
}, {
  value: "false",
  label: 'Nein'
}]

const selected = ref("true")
const time = ref(null)
const dose = ref(null)

console.log(Date.now());

console.log(dayjs(Date.now()).utc().toString());


function saveIntake() {
    console.log(selected.value, time.value, dose.value, drugStore.item.pzn);
    
}

</script>