<template>
    <Layout>
        <UIBaseCard :naked="true">
            <UButton @click="showForm = !showForm" label="Eingabe Präparat" color="green" variant="soft"
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
                <UForm @submit="saveIntake" :state="state" :schema="schema" class="space-y-4">
                    <UFormGroup label="Dosis" style="border-color: red;">
                        <UInput type="number" v-model="state.dose" />
                    </UFormGroup>
                    <UFormGroup label="Einnahme (Uhrzeit)">
                        <UInput type="date" v-model="state.time" />
                    </UFormGroup>
                    <URadioGroup v-model="state.selected" legend="Wurden heute Medikamente eingenommen?"
                        :options="options" />
                    <UButton type="submit" label="Speichern" color="green" variant="soft"
                        class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
                </UForm>
                <br>
                <UAccordion :items="items" :ui="{ wrapper: 'flex flex-col w-full' }">
                    <template #default="{ item, index, open }">
                        <UButton color="green" variant="link" class="newDrugButton"
                            :ui="{ rounded: 'rounded-none', padding: { sm: 'p-3' } }">
                            <span class="truncate">{{ item.label }}</span>
                            <template #trailing>
                                <UIcon name="i-heroicons-chevron-right-20-solid"
                                    class="w-5 h-5 ms-auto transform transition-transform duration-200"
                                    :class="[open && 'rotate-90']" />
                            </template>
                        </UButton>
                    </template>                    
                    <template #newDrug="{ content }">
                        <div class="new-drug-box">
                            <UForm :schema="newDrugSchema" :state="newDrugState" class="space-y-4" @submit="test">
                                <UFormGroup label="Name" name="name" required>
                                    <UInput v-model="newDrugState.name" />
                                </UFormGroup>
                                <UFormGroup label="PZN" name="pzn">
                                    <UInput v-model="newDrugState.pzn" placeholder="Falls bekannt"/>
                                </UFormGroup>
                                <UFormGroup label="Herstellercode" name="herstellerCode">
                                    <UInput v-model="newDrugState.herstellerCode" placeholder="Falls bekannt"/>
                                </UFormGroup>
                                <UFormGroup label="Darreichungsform" name="darrform">
                                    <UInput v-model="newDrugState.darrform" placeholder="Falls bekannt"/>
                                </UFormGroup>
                                <UFormGroup label="Applikationsform" name="appform">
                                    <UInput v-model="newDrugState.appform" placeholder="Falls bekannt"/>
                                </UFormGroup>
                                <UFormGroup label="ATC-Code" name="atc_code">
                                    <UInput v-model="newDrugState.atc_code" placeholder="Falls bekannt"/>
                                </UFormGroup>
                                <UFormGroup label="Packungsgroesse" name="packgroesse">
                                    <UInput v-model="newDrugState.packgroesse" placeholder="Falls bekannt"/>
                                </UFormGroup>
                                <UButton type="submit" color="green" variant="soft"
                                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white">
                                    Neues Medikament speichern
                                </UButton>
                            </UForm>
                        </div>
                    </template>
                </UAccordion>
            </UIBaseCard>
        </div>
        <UIBaseCard>
            <h4>Medikamenteneinnahme von Proband: {{ interview.proband_external_id }}</h4>
            <div v-if="intakes.length > 0">
                <ul v-for="intake in intakes" :key="intake.id">
                    <li v-if="drugDetailsMap[intake.pharmazentralnummer]">
                        <h5>Medikament Details: {{ drugDetailsMap[intake.pharmazentralnummer].name }} </h5>
                        <p>PZN: {{ intake.pharmazentralnummer }}</p>
                        <p>Dose: {{ intake.as_needed_dose_unit }}</p>
                        <p>Starttime: {{ intake.intake_start_time_utc }}</p>
                        <p>Medicine taken today: {{ intake.consumed_meds_today }}</p>
                        <br>
                    </li>
                    <li v-else>
                        Loading drug details...
                    </li>
                </ul>
            </div>
        </UIBaseCard>
    </Layout>
</template>

<script setup lang="ts">

const newDrugState = reactive({
    pzn: "",
    name: null,
    herstellerCode: "",
    darrform: "",
    appform: "",
    atc_code: "",
    packgroesse: 0
})

const newDrugSchema = object({
    pzn: string(),
    name: string().required('Required'),
    herstellerCode: string(),
    darrform: string(),
    appform: string(),
    atc_code: string(),
    packgroesse: number()

})

type NewDrugSchema = Infertype<typeof newDrugSchema>

async function test() {
    console.log("hello");
}

import dayjs from 'dayjs';
import { watchEffect } from 'vue';
import type { FormSubmitEvent } from "#ui/types";
import { object, number, date, string, type InferType } from "yup";

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

const items = [{ label: 'Neues Medikament anlegen', slot: 'newDrug' }]
const additionalItems = [{ label: 'Weitere Informationen', slot: 'additionalInfo' }]

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
    label: "Unbekannt"
}]

const state = reactive({
    selected: "Yes",
    time: null,
    dose: null
});

const schema = object({
    selected: string().required("Required"),
    time: date().required("Required"),
    dose: number().min(0, "Hallo"),
});

type Schema = InferType<typeof schema>;

const drugDetailsMap = ref({});

async function fetchDrugDetails(pzn) {
    if (!drugDetailsMap.value[pzn]) {
        try {
            const response = await $fetch(`${runtimeConfig.public.baseURL}drug/by-pzn/${pzn}`, {
                method: "GET",
                headers: { 'Authorization': "Bearer " + tokenStore.access_token },
            });
            drugDetailsMap.value[pzn] = response;
        }
        catch (error) {
            console.log(error);
        }
    }
}

watchEffect(() => {
    intakes.value.forEach(intake => {
        fetchDrugDetails(intake.pharmazentralnummer);
    });
});

async function saveIntake() {
    const date = dayjs(state.time).utc().format("YYYY-MM-DD")
    const pzn = drugStore.item.pzn
    const myDose = state.dose.toString()

    try {
        showForm.value = false;
        const responseData = await useCreateIntake(route.params.study_id, route.params.interview_id, pzn, date, myDose, state.selected);
        refresh()
    } catch (error) {
        console.error("Failed to create Intake: ", error);
    }
}

</script>

<style scoped>
.newDrugButton {
    text-align: center;
    border-color: #a9e7bc;
    border-radius: 10px;
    background-color: white;
}

.new-drug-box{
    padding: 20px;
    border-style: solid;
    border-color: #adecc0;
    border-radius: 10px;
    border-width: 2px;
}
</style>