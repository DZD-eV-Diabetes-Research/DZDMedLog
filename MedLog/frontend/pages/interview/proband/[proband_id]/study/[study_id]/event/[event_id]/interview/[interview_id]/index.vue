<template>
    <Layout>
        <UIBaseCard :naked="true">
            <UButton @click="openIntakeForm()" label="Eingabe Präparat" color="green" variant="soft"
                style="margin-right: 10px;"
                class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" />
            <!-- <UButton v-if="tableContent.length == 0" @click="openIntakeForm()" label="Medikamente übernehmen"
                color="blue" variant="soft" style="margin-left: 10px;"
                class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white" /> -->
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
                    <UFormGroup label="Dosis" style="border-color: red;" name="dose">
                        <UInput type="number" v-model="state.dose"/>
                    </UFormGroup>
                    <UFormGroup label="Einnahme (Datum)" name="time">
                        <UInput type="date" v-model="state.time" />
                    </UFormGroup>
                    <URadioGroup v-model="state.selected" legend="Wurden heute Medikamente eingenommen?" name="selected"
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
                            <UForm :schema="newDrugSchema" :state="newDrugState" class="space-y-4"
                                @submit="createNewDrug">
                                <UFormGroup label="Name" name="name" required>
                                    <UInput v-model="newDrugState.name" />
                                </UFormGroup>
                                <UFormGroup label="Darreichungsform" name="darrform" required>
                                    <UInput v-model="newDrugState.darrform" />
                                </UFormGroup>
                                <UFormGroup label="Dosis" name="dose">
                                    <UInput v-model="newDrugState.dose" />
                                </UFormGroup>
                                <UFormGroup label="PZN" name="pzn">
                                    <UInput v-model="newDrugState.pzn" placeholder="Falls bekannt" />
                                </UFormGroup>
                                <UFormGroup label="Herstellercode" name="herstellerCode">
                                    <UInput v-model="newDrugState.herstellerCode" placeholder="Falls bekannt" />
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
            <h4 style="text-align: center; padding-top: 25px;">Probandenhistorie</h4>
            <div>
                <div class="flex px-3 py-3.5 border-b border-gray-200 dark:border-gray-700">
                    <UInput v-model="q" placeholder="Tabelle Filtern" />
                </div>
                <UTable :rows="rows" :columns="columns">
                    <template v-if="userStore.isAdmin" #actions-data="{ row }">
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
            <div style="text-align: center;">
                <UButton @click="backToOverview()" label="Zurück zur Übersicht" color="green" variant="soft"
                    class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white"
                    style="margin: 25px;" />
            </div>
        </div>
        <UModal v-model="deleteModalVisibility">
            <div class="p-4">
                <div style="text-align: center;">
                    <h4 style="color:red">Sie löschen folgenden Eintrag: </h4>
                    <br>
                    <h4>{{ drugToDelete.drug }}</h4>
                    <br>
                    <p style="color: red">PZN: {{ drugToDelete.pzn }}</p>
                    <br>
                    <UForm :schema="deleteSchema" :state="deleteState" class="space-y-4" @submit="deleteIntake">
                        <UFormGroup label="Zum löschen die PZN eintragen" name="pzn">
                            <UInput v-model="deleteState.pzn" color="red" :placeholder="drugToDelete.pzn" />
                        </UFormGroup>
                        <br>
                        <UButton type="submit" color="red" variant="soft"
                            class="border border-red-500 hover:bg-red-300 hover:border-white hover:text-white">
                            Eintrag löschen
                        </UButton>
                    </UForm>
                </div>
            </div>
        </UModal>
        <UModal v-model="editModalVisibility">
            <div class="p-4">
                <div style="text-align: center;">
                    <IntakeQuestion :drug="toEditDrug" />
                    <div v-if="drugStore.item">
                        <br>
                        <p>Medikament: {{ drugStore.item.item.name }}</p>
                        <p>PZN: {{ drugStore.item.pzn }}</p>
                        <p>Packungsgroesse: {{ drugStore.item.item.packgroesse }}</p>
                    </div>
                    <UForm @submit="editEntry" :state="editState" :schema="editSchema" class="space-y-4">
                        <UFormGroup label="Dosis" style="border-color: red;">
                            <UInput type="number" v-model="editState.dose" name="editState.dose" color="blue" />
                        </UFormGroup>
                        <UFormGroup label="Einnahme (Datum)">
                            <UInput type="date" v-model="editState.time" name="time" color="blue" />
                        </UFormGroup>
                        <URadioGroup v-model="editState.selected" legend="Wurden heute Medikamente eingenommen?"
                            name="selected" :options="editOptions" />
                        <UButton type="submit" label="Bearbeiten" color="blue" variant="soft"
                            class="border border-blue-500 hover:bg-blue-300 hover:border-white hover:text-white" />
                    </UForm>
                </div>
            </div>
        </UModal>
    </Layout>
</template>

<script setup lang="ts">

import dayjs from 'dayjs';
import { watchEffect } from 'vue';
import type { FormSubmitEvent } from "#ui/types";
import { object, number, date, string, type InferType } from "yup";

const toEditDrug = ref()

const editModalVisibility = ref(false)

const editSchema = object({
    selected: string().required("Required"),
    time: date().required("Required"),
    dose: number().min(0, "Hallo"),
})

type EditSchema = InferType<typeof editSchema>

const editState = reactive({
    selected: "Yes",
    time: null,
    dose: null
})


const editOptions = [{
    value: "Yes",
    label: 'Ja'
}, {
    value: "No",
    label: 'Nein',
}, {
    value: "UNKNOWN",
    label: "Unbekannt"
}]

const toEditDrugId = ref()

async function editModalVisibilityFunction(row: object) {
    try {
        editModalVisibility.value = true
        editState.time = row.startTime
        editState.dose = row.dose
        toEditDrug.value = row.drug
        toEditDrugId.value = row.id
    } catch (error) {
        console.log(error);
    }
}


async function editEntry() {

    try {
        const fetchBody = {
            pharmazentralnummer: drugStore.item.pzn,
            custom_drug_id: null,
            intake_start_time_utc: editState.time,
            intake_end_time_utc: null,
            administered_by_doctor: "prescribed",
            intake_regular_or_as_needed: "regular",
            dose_per_day: editState.dose,
            regular_intervall_of_daily_dose: "regular",
            as_needed_dose_unit: null,
            consumed_meds_today: editState.selected
        }

        await $fetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake/${toEditDrugId.value}`, {
            method: "PATCH",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
            body: fetchBody

        })

        toEditDrugId.value = null
        editModalVisibility.value = false
        createIntakeList()

    } catch (error) {
        console.log(error);
    }
}

const deleteSchema = object({
    pzn: string().required('Required').test('is-dynamic-value', 'PZN muss übereinstimmen', function (value) {
        return value === drugToDelete.value.pzn;
    }),
})

type DeleteSchema = InferType<typeof deleteSchema>

const deleteState = reactive({
    pzn: undefined
})

const page = ref(1)
const pageCount = 15

const rows = computed(() => {
    const data = q.value ? filteredRows.value : tableContent.value;
    return data.slice((page.value - 1) * pageCount, page.value * pageCount);
})

const columns = [{
    key: 'pzn',
    label: 'PZN'
}, {
    key: 'drug',
    label: 'Medikament',
    sortable: true
},
{
    key: 'dose',
    label: 'Dosis',
    sortable: true
},
{
    key: 'startTime',
    label: 'Einnahme Start',
    sortable: true
},
{
    key: 'darr',
    label: 'Darreichung',
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
        click: () => editModalVisibilityFunction(row)
    }, {
        label: 'Löschen',
        icon: 'i-heroicons-trash-20-solid',
        click: () => openDeleteModal(row)
    }]
]

const deleteModalVisibility = ref(false)
const drugToDelete = ref()

async function openDeleteModal(row: object) {
    deleteState.pzn = ""
    deleteModalVisibility.value = true
    drugToDelete.value = row
}

async function deleteIntake() {
    try {
        await $fetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake/${drugToDelete.value.id}`, {
            method: "DELETE",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
        })
        deleteModalVisibility.value = false
        createIntakeList()
    } catch (error) {
        console.log(error);
    }
}

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

async function createNewDrug() {
    try {
    const date = dayjs(Date()).format("YYYY-MM-DD")
    const myDose = newDrugState.dose
    const response = await $fetch(`${runtimeConfig.public.baseURL}drug/user-custom`, {
            method: "POST",
            headers: { 'Authorization': "Bearer " + tokenStore.access_token },
            body: {
                created_at: date,
                pzn: newDrugState.pzn ? newDrugState.pzn : null,
                name: newDrugState.name ? newDrugState.name : null,
                hersteller_code: newDrugState.herstellerCode ? newDrugState.herstellerCode : null,
                darrform: newDrugState.darrform ? newDrugState.darrform : null,
                appform: newDrugState.appform ? newDrugState.appform : null,
                atc_code: newDrugState.atc_code ? newDrugState.atc_code : null,
                packgroesse: newDrugState.packgroesse ? newDrugState.packgroesse : null 
            }
        })

    const pzn = newDrugState.pzn ? newDrugState.pzn : null
    
    await useCreateIntake(route.params.study_id, route.params.interview_id, pzn, date, myDose, "Yes", response.id);
        
    router.go()

    } catch (error) {
                console.error("Failed to create Intake: ", error);
            }
}

const newDrugState = reactive({
    pzn: "",
    name: "",
    dose: "",
    herstellerCode: "",
    darrform: "",
    appform: "",
    atc_code: "",
    packgroesse: 0
})

const newDrugSchema = object({
    pzn: string(),
    name: string().required('Required'),
    dose: number(),
    herstellerCode: string(),
    darrform: string().required('Required'),
    appform: string(),
    atc_code: string(),
    packgroesse: number()

})

type NewDrugSchema = Infertype<typeof newDrugSchema>

const route = useRoute()
const router = useRouter()
const tokenStore = useTokenStore()
const drugStore = useDrugStore()
const studyStore = useStudyStore()
const userStore = useUserStore()
const runtimeConfig = useRuntimeConfig()

drugStore.item = null

const { data: intakes, refresh } = await useFetch(`${runtimeConfig.public.baseURL}study/${route.params.study_id}/proband/${route.params.proband_id}/intake/details?interview_id=${route.params.interview_id}`, {
    method: "GET",
    headers: { 'Authorization': "Bearer " + tokenStore.access_token },
})

const items = [{ label: 'Neues Medikament anlegen', slot: 'newDrug' }]
const additionalItems = [{ label: 'Weitere Informationen', slot: 'additionalInfo' }]

const study = await studyStore.getStudy(route.params.study_id)

const showForm = ref(true)

async function openIntakeForm() {
    showForm.value = !showForm.value
    state.selected = "Yes"
    state.time = null
    state.dose = null
    drugStore.$reset()
}

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
    const date = dayjs(state.time).format("YYYY-MM-DD")
    const pzn = drugStore.item.pzn
    const myDose = state.dose

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
                pzn: item.pharmazentralnummer,
                drug: item.drug.name,
                dose: item.dose_per_day,
                startTime: item.intake_start_time_utc,
                darr: item.drug.darrform_ref.darrform,
                manufac: item.drug.hersteller_ref ? item.drug.hersteller_ref.bedeutung : null,
                // customDrug: item.custom_drug_id ? true: false,
                class: item.custom_drug_id ? 'bg-yellow-500/50 dark:bg-yellow-400/50' : null
            }))
        }
    } catch (error) {
        console.log(error);
    }
}

createIntakeList()

async function backToOverview() {
    router.push({ path: '/interview/proband/' + route.params.proband_id + '/study/' + route.params.study_id })
}


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