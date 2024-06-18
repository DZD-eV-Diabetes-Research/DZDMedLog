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
                                    <UInput v-model="newDrugState.pzn" placeholder="Falls bekannt" />
                                </UFormGroup>
                                <UFormGroup label="Herstellercode" name="herstellerCode">
                                    <UInput v-model="newDrugState.herstellerCode" placeholder="Falls bekannt" />
                                </UFormGroup>
                                <UFormGroup label="Darreichungsform" name="darrform">
                                    <UInput v-model="newDrugState.darrform" placeholder="Falls bekannt" />
                                </UFormGroup>
                                <UFormGroup label="Applikationsform" name="appform">
                                    <UInput v-model="newDrugState.appform" placeholder="Falls bekannt" />
                                </UFormGroup>
                                <UFormGroup label="ATC-Code" name="atc_code">
                                    <UInput v-model="newDrugState.atc_code" placeholder="Falls bekannt" />
                                </UFormGroup>
                                <UFormGroup label="Packungsgroesse" name="packgroesse">
                                    <UInput v-model="newDrugState.packgroesse" placeholder="Falls bekannt" />
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
        <div class="tableDiv">
            <h4 style="text-align: center; padding-top: 25px;d">Medikamentenübersicht</h4>
            <div>
                <div class="flex px-3 py-3.5 border-b border-gray-200 dark:border-gray-700">
                    <UInput v-model="q" placeholder="Tabelle Filtern" />
                </div>
                <UTable :rows="rows" :columns="columns">
                    <template #actions-data="{ row }">
                        <UDropdown :items="myOptions(row)">
                            <UButton color="gray" variant="ghost" icon="i-heroicons-ellipsis-horizontal-20-solid" />
                        </UDropdown>
                    </template>
                </UTable>
                <div v-if="tableContent.length >= pageCount || filteredRows.length >= pageCount" class="flex justify-center px-3 py-3.5 border-t 
        dark:border-green-700 dark:border-red-500">
                    <UPagination v-model="page" :page-count="pageCount" :total="filteredRows.length" :ui="{
                        wrapper: 'flex items-center gap-1',
                        rounded: 'rounded-sm',
                        default: {
                            activeButton: {
                                variant: 'outline',
                            }
                        }
                    }" />
                </div>
            </div>
        </div>
    </Layout>
</template>

<script setup lang="ts">

const page = ref(1)
const pageCount = 15

const rows = computed(() => {
    const data = q.value ? filteredRows.value : tableContent.value;
    return data.slice((page.value - 1) * pageCount, page.value * pageCount);
})

const columns = [{
    key: 'drug',
    label: 'Medikament',
    sortable: true
}, {
    key: 'darr',
    label: 'Darreichungsform',
    sortable: true
}, {
    key: 'manufac',
    label: 'Hersteller',
    sortable: true
}, {
    key: 'actions'
}]

const myOptions = (row) => [
    [{
        label: 'Bearbeiten',
        icon: 'i-heroicons-pencil-square-20-solid',
        click: () => console.log('Edit', row)
    }, {
        label: 'Delete',
        icon: 'i-heroicons-trash-20-solid',
        click: () => console.log('Delete', row)
    }]
]

const q = ref('')

const filteredRows = computed(() => {
    if (!q.value) {
        return tableContent.value
    }

    return tableContent.value.filter((tableContent) => {
        return Object.values(tableContent).some((value) => {
            return String(value).toLowerCase().includes(q.value.toLowerCase())
        })
    })
})

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

const { data: intakes, refresh } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/intake/details?interview_id=${route.params.interview_id}`, {
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

async function saveIntake() {
    const date = dayjs(state.time).utc().format("YYYY-MM-DD")
    const pzn = drugStore.item.pzn
    const myDose = state.dose.toString()

    try {
        showForm.value = false;
        const responseData = await useCreateIntake(route.params.study_id, route.params.interview_id, pzn, date, myDose, state.selected);
        createIntakeList()
    } catch (error) {
        console.error("Failed to create Intake: ", error);
    }
}

const tableContent = ref([])

async function createIntakeList() {

    try {
        const intakes = await $fetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/intake/details?interview_id=${route.params.interview_id}`, {
            method: "GET",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        })
        if (intakes && intakes.items) {
            tableContent.value = intakes.items.map(item => ({
                drug: item.drug.name,
                darr: item.drug.darrform_ref.darrform,
                manufac: item.drug.hersteller_ref.bedeutung
            }))
        }
    } catch (error) {
        console.log(error);
    }
}

createIntakeList()


</script>

<style scoped>
.newDrugButton {
    text-align: center;
    border-color: #a9e7bc;
    border-radius: 10px;
    background-color: white;
}

.new-drug-box {
    padding: 20px;
    border-style: solid;
    border-color: #adecc0;
    border-radius: 10px;
    border-width: 2px;
}

.tableDiv {
    border-radius: 10px;
    border-width: 2px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.26);
}
</style>