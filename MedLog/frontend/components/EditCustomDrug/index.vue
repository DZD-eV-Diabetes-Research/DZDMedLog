<template>
    <IntakeQuestion color="yellow" edit="true" custom="true" :drug="drug" />
    <div style="text-align: center" v-if="missingDrugError">
        <br />
        <p style="color: red">Es muss ein Medikament ausgewählt werden</p>
    </div>
    <UForm @submit="saveIntake()" :state="state" :schema="schema" class="space-y-4">
        <div style="padding-top: 2.5%">
            <br />
            <UFormGroup label="Quelle der Arzneimittelangabe">
                <USelect v-model="selectedSourceItem" :options="sourceItems" color="yellow" />
            </UFormGroup>
        </div>
        <UFormGroup label="Einnahme regelmäßig oder nach Bedarf?">
            <USelect v-model="selectedFrequency" :options="frequency" color="yellow" />
        </UFormGroup>
        <div class="flex flex-row space-x-4">
            <div class="flex-1">
                <UFormGroup label="Dosis pro Einnahme" style="border-color: red" name="dose">
                    <UInput type="number" v-model="state.dose" :disabled="selectedFrequency !== 'regelmäßig'"
                        :color="selectedFrequency !== 'regelmäßig' ? 'gray' : 'yellow'" />
                </UFormGroup>
            </div>
            <div class="flex-1">
                <UFormGroup label="Intervall der Tagesdosen">
                    <USelect v-model="state.intervall" :options="intervallOfDose"
                        :disabled="selectedFrequency !== 'regelmäßig'"
                        :color="selectedFrequency !== 'regelmäßig' ? 'gray' : 'yellow'" />
                </UFormGroup>
            </div>
        </div>
        <div class="flex flex-row space-x-4">
            <div class="flex-1">
                <UFormGroup label="Einnahme Beginn (Datum)" name="startTime">
                    <UInput type="date" v-model="state.startTime" color="yellow" />
                </UFormGroup>
            </div>
            <div class="flex-1">
                <UFormGroup label="Einnahme Ende (Datum)" name="endTime">
                    <UInput type="date" v-model="state.endTime" color="yellow" />
                </UFormGroup>
            </div>
        </div>
        <URadioGroup v-model="state.selected" legend="Wurden heute Medikamente eingenommen?" name="selected"
            :options="options" color="yellow" />
        <div style="text-align: center">
            <div class="flex flex-row justify-center space-x-6">
                <UButton type="submit" label="Speichern" color="yellow" variant="soft" :class="buttonClass" />
                <UButton label="Abbrechen" color="yellow" variant="soft" :class="buttonClass" @click="closeEditModal()">
                </UButton>
            </div>
        </div>
    </UForm>
</template>



<script setup lang="ts">

import dayjs from "dayjs";
import { object, number, date, string, type InferType, boolean } from "yup";
import { apiGetFieldDefinitions } from '~/api/drug';
const { $api } = useNuxtApp();


const route = useRoute();
const tokenStore = useTokenStore();
const drugStore = useDrugStore();
const initialLoad = ref(true);
const runTimeConfig = useRuntimeConfig();

const props = defineProps<{
    drug?: string;
    label?: string;
    row?: any;
}>();

const buttonClass = computed(() => {
    const color = 'yellow';
    return `border border-${color}-500 hover:bg-${color}-300 hover:border-white hover:text-white`;
});

const state = reactive({
    selected: "Yes",
    startTime: dayjs(Date()).format("YYYY-MM-DD"),
    endTime: null,
    dose: 0,
    intervall: null,
    customName: "",
});

const schema = object({
    selected: string().required("Required"),
    startTime: date().required("Required"),
    dose: number().min(0, "Required"),
    name: string(),
    darrform: string(),
});

type Schema = InferType<typeof schema>;

const sourceItems = [
    "Probandenangabe",
    "Medikamentenpackung: PZN gescannt",
    "Medikamentenpackung: PZN getippt",
    "Medikamentenpackung: Arzneimittelname",
    "Beipackzettel",
    "Medikamentenplan",
    "Rezept",
    "Nacherhebung: Tastatureingabe der PZN",
    "Nacherhebung: Arzneimittelname",
];
const selectedSourceItem = ref(sourceItems[0]);

const frequency = ["nach Bedarf", "regelmäßig"];
const selectedFrequency = ref(frequency[0]);

const intervallOfDose = [
    "unbekannt",
    "täglich",
    "jeden 2. Tag",
    "jeden 3. Tag",
    "jeden 4. Tag = 2x pro Woche",
    "Im Abstand von 1 Woche und mehr",
];
const selectedInterval = ref(intervallOfDose[0]);

const options = [
    {
        value: "Yes",
        label: "Ja",
    },
    {
        value: "No",
        label: "Nein",
    },
    {
        value: "UNKNOWN",
        label: "Unbekannt",
    },
];

const tempDose = ref();
const tempIntervall = ref();
const missingDrugError = ref(false)

async function saveIntake() {

    drugStore.action = false;
    initialLoad.value = false;
    tempDose.value = null;
    tempIntervall.value = null;

    drugStore.source = useDrugSourceTranslator(null, selectedSourceItem.value);
    if (selectedFrequency.value === "nach Bedarf") {
        drugStore.frequency = "as needed";
    } else {
        drugStore.frequency = "regular";
    }

    drugStore.dose = state.dose;
    tempDose.value = drugStore.dose; props
    drugStore.intervall = useIntervallDoseTranslator(null, state.intervall);
    tempIntervall.value = state.intervall;
    drugStore.option = state.selected;
    drugStore.intake_start_time_utc = state.startTime;
    drugStore.intake_end_time_utc = state.endTime;
    drugStore.consumed_meds_today = state.selected;

    try {
        drugStore.editVisibility = false;
        const frequency = ref();

        if (drugStore.frequency === "nach Bedarf") {
            frequency.value = "as needed";
        } else {
            frequency.value = "regular";
        }

        const patchBody = {
            drug_id: drugStore.item.drug_id,
            source_of_drug_information: drugStore.source,
            intake_start_time_utc: drugStore.intake_start_time_utc,
            intake_end_time_utc: drugStore.intake_end_time_utc,
            administered_by_doctor: "prescribed",
            intake_regular_or_as_needed: frequency.value,
            dose_per_day: drugStore.dose,
            regular_intervall_of_daily_dose: drugStore.intervall,
            as_needed_dose_unit: null,
            consumed_meds_today: drugStore.consumed_meds_today,
        };

        await $api(
            `${runTimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake/${drugStore.editId}`,
            {
                method: "PATCH",
                body: patchBody,
            }
        );
    } catch (error) {
        console.log(error);
    }

    drugStore.action = !drugStore.action;
}

watch(selectedFrequency, (newValue) => {
    if (newValue === "nach Bedarf") {
        drugStore.frequency = "as needed";
        tempDose.value = state.dose;
        state.dose = 0;
        tempIntervall.value = state.intervall;
        state.intervall = null;
        selectedInterval.value = null;
    } else if (!props.edit) {
        drugStore.frequency = "regular";
        state.dose = tempDose.value ? tempDose.value : 1;
        state.intervall = tempIntervall.value ? tempIntervall.value : "unbekannt";
    } else {
        state.dose = drugStore.dose;
        state.intervall = drugStore.intervall;
    }
});

// functioning

if (props.edit) {
    selectedSourceItem.value = drugStore.source;
    selectedFrequency.value = drugStore.frequency;
    state.dose = drugStore.dose;
    state.intervall = drugStore.intervall;
    state.startTime = drugStore.intake_start_time_utc;
    state.endTime = drugStore.intake_end_time_utc;
    state.selected = drugStore.consumed_meds_today;
}

if (props.custom && props.edit) {
    state.name = drugStore.drugName
    selectedDosageForm.value = { "label": drugStore.darrForm }
}

// CUSTOM DRUG

interface DrugBody {
    trade_name: string;
    market_access_date: string | null;
    market_exit_date: string | null;
    custom_drug_notes: string | null;
    attrs: Attribute[] | null;
    attrs_ref: Attribute[] | null;
    attrs_multi: Attribute[] | null;
    attrs_multi_ref: Attribute[] | null;
    codes: Attribute[] | null;
}

const closeEditModal = function () {
    drugStore.editVisibility = false
    drugStore.item = null
}

</script>