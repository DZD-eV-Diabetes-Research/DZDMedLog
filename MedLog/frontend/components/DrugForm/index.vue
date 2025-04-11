<template>
  <div style="text-align: center" v-if="missingDrugError">
    <br />
    <p style="color: red">Es muss ein Medikament ausgewählt werden</p>
  </div>
  <UForm @submit="saveIntake()" :state="state" :schema="schema" class="space-y-4">
    <div style="padding-top: 2.5%">
      <div v-if="props.custom">
        <div class="text-center pt-4 pb-8" v-if="!props.edit">
          <h4 class="text-xl font-light">
            Hiermit wird einmalig ein Medikament angelegt, das in der
            Medikamentensuche nicht gefunden wurde
          </h4>
        </div>
        <h5 v-if="customNameError" style="color: red">
          Name wird benötigt
        </h5>
        <UFormGroup label="Name" name="customName" required class="mb-6">
          <UInput v-model="state.customName" color="yellow" />
        </UFormGroup>
        <h5 v-if="showDarrFormError" style="color: red">
          Darreichungsform wird benötigt
        </h5>
        <UFormGroup label="Darreichungsform" name="darrform" required class="mb-8">
          <UCommandPalette v-if="!state.customDarrform" v-model="state.customDarrform" :autoselect="false"
            :groups="[{ key: 'dosageFormTable', commands: dosageFormTable }]"
            :fuse="{ resultLimit: 5, fuseOptions: { threshold: 0.2 } }" />
          <div v-else class="my-5">
            <p @click="state.customDarrform = null"
              class="text-lg text-center hover:cursor-pointer hover:text-yellow-500" style="margin-bottom:2%">
              {{ state.customDarrform?.label }}
            </p>
          </div>
        </UFormGroup>
        <UAccordion :items="customDrugForm" color="yellow">
          <template #custom-form>
            <div v-if="isDataLoaded" class="bg-yellow-50 outline-yellow-200 rounded-md p-2">
              <UForm :state="attrState" class="space-y-4">
                <UFormGroup v-for="attr in drugFieldDefinitionsObject.attrs" :label="attr[0]" :name="attr[1]"
                  :key="attr[1]">
                  <UInput v-if="getFormInputType(attr[2]) !== 'checkbox'" v-model="attrState[attr[1]]" color="yellow"
                    :type="getFormInputType(attr[2])" />
                  <UCheckbox v-else v-model="attrState[attr[1]]" color="yellow" :name="attrState[attr[0]]" />
                </UFormGroup>
                <UFormGroup v-for="attr_ref in drugFieldDefinitionsObject.attrs_ref" :label="attr_ref[0]"
                  :name="attr_ref[1]" :key="attr_ref[1]">
                  <USelectMenu v-model="attr_refState[attr_ref[1]]"
                    :options="refSelectMenus.find(item => item.field_name === attr_ref[1])?.options"
                    value-attribute="value" option-attribute="display" color="yellow" />
                </UFormGroup>
                <UFormGroup v-for="attr_multi in drugFieldDefinitionsObject.attrs_multi" :label="attr_multi[0]"
                  :name="attr_multi[1]" :key="attr_multi[1]">
                  <UInput placeholder="Enter a value and press Enter" v-model="inputValues[attr_multi[1]]"
                    @keydown.enter.prevent="updateMultiState(attr_multi[1])" @blur="updateMultiState(attr_multi[1])"
                    color="yellow" />
                  <UBadge v-for="(word, index) in attr_multiState[attr_multi[1]]" :key="index"
                    class="mr-2 cursor-pointer" @click="removeItem(attr_multi[1], index)" color="yellow">
                    {{ word }}
                  </UBadge>
                </UFormGroup>
                <UFormGroup v-for="attr_multi_ref in drugFieldDefinitionsObject.attrs_multi_ref"
                  :label="attr_multi_ref[0]" :name="attr_multi_ref[1]" :key="attr_multi_ref[1]">
                  <USelectMenu v-model="attr_multi_refState[attr_multi_ref[1]]"
                    :options="multiRefSelectMenus.find(item => item.field_name === attr_multi_ref[1])?.options"
                    value-attribute="value" option-attribute="display" multiple searchable color="yellow">
                    <template #label>
                      <span
                        v-if="Array.isArray(attr_multi_refState[attr_multi_ref[1]]) && attr_multi_refState[attr_multi_ref[1]].length">
                        {{attr_multi_refState[attr_multi_ref[1]].map(val => multiRefSelectMenus.find(item =>
                          item.field_name ===
                          attr_multi_ref[1])?.options.find(option => option.value === val)?.display || val)
                          .join('; ')}}
                      </span>
                      <span v-else>Choose your fighter</span>
                    </template>
                  </USelectMenu>
                </UFormGroup>
              </UForm>
            </div>
            <div v-else>
              loading
            </div>
          </template>
        </UAccordion>
        <br />
      </div>
      <UFormGroup label="Quelle der Arzneimittelangabe">
        <USelect v-model="selectedSourceItem" :options="sourceItems" :color="props.color" />
      </UFormGroup>
    </div>
    <UFormGroup label="Einnahme regelmäßig oder nach Bedarf?">
      <USelect v-model="selectedFrequency" :options="frequency" :color="props.color" />
    </UFormGroup>
    <div class="flex-container">
      <UFormGroup label="Dosis pro Einnahme" style="border-color: red" name="dose">
        <UInput type="number" v-model="state.dose" :disabled="selectedFrequency !== 'regelmäßig'"
          :color="selectedFrequency !== 'regelmäßig' ? 'gray' : props.color" />
      </UFormGroup>
      <UFormGroup label="Intervall der Tagesdosen">
        <USelect v-model="state.intervall" :options="intervallOfDose" :disabled="selectedFrequency !== 'regelmäßig'"
          :color="selectedFrequency !== 'regelmäßig' ? 'gray' : props.color" />
      </UFormGroup>
    </div>
    <div class="flex-container">
      <UFormGroup label="Einnahme Beginn (Datum)" name="startTime">
        <UInput type="date" v-model="state.startTime" :color="props.color" />
      </UFormGroup>
      <UFormGroup label="Einnahme Ende (Datum)" name="endTime">
        <UInput type="date" v-model="state.endTime" :color="props.color" />
      </UFormGroup>
    </div>
    <URadioGroup v-model="state.selected" legend="Wurden heute Medikamente eingenommen?" name="selected"
      :options="options" :color="props.color" />
    <div style="text-align: center">
      <div v-if="props.edit" class="flex flex-row justify-center space-x-6">
        <UButton type="submit" label="Speichern" :color="props.color" variant="soft" :class="buttonClass" />
        <UButton label="Abbrechen" :color="props.color" variant="soft" :class="buttonClass" @click="drugStore.editVisibility = false"></UButton>
      </div>
      <div v-else>
        <UButton type="submit" :label="props.label" :color="props.color" variant="soft" :class="buttonClass" />
      </div>
    </div>
    <div class="flex flex-col justify-center items-center">
      <h5 v-if="showDarrFormError" style="color: red">
        Darreichungsform wird benötigt
      </h5>
      <br>
      <h5 v-if="customNameError" style="color: red">
        Name wird benötigt
      </h5>
    </div>
  </UForm>
</template>



<script setup lang="ts">

import dayjs from "dayjs";
import { object, number, date, string, type InferType, boolean } from "yup";
import { apiGetFieldDefinitions } from '~/api/drug';

const route = useRoute();
const tokenStore = useTokenStore();
const drugStore = useDrugStore();
const initialLoad = ref(true);
const runTimeConfig = useRuntimeConfig();

const props = defineProps<{
  color?: string;
  edit?: boolean;
  custom?: boolean;
  label?: string;
  row?: any;
}>();

const buttonClass = computed(() => {
  const color = props.color;
  return `border border-${color}-500 hover:bg-${color}-300 hover:border-white hover:text-white`;
});

const state = reactive({
  selected: "Yes",
  startTime: dayjs(Date()).format("YYYY-MM-DD"),
  endTime: null,
  dose: 0,
  intervall: null,
  customName: "",
  customDarrform: "",
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
const customNameError = ref(false)
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
  tempDose.value = drugStore.dose;
  drugStore.intervall = useIntervallDoseTranslator(null, state.intervall);
  tempIntervall.value = state.intervall;
  drugStore.option = state.selected;
  drugStore.intake_start_time_utc = state.startTime;
  drugStore.intake_end_time_utc = state.endTime;
  drugStore.consumed_meds_today = state.selected;

  if (props.edit && !props.custom) {
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

      await $fetch(
        `${runTimeConfig.public.baseURL}study/${route.params.study_id}/interview/${route.params.interview_id}/intake/${drugStore.editId}`,
        {
          method: "PATCH",
          headers: { Authorization: "Bearer " + tokenStore.access_token },
          body: patchBody,
        }
      );
    } catch (error) {
      console.log(error);
    }
  } else if (!props.edit && !props.custom) {

    try {
      await useCreateIntake(
        route.params.study_id,
        route.params.interview_id,
        drugStore.administered_by_doctor,
        drugStore.source,
        drugStore.intake_start_time_utc,
        drugStore.intake_end_time_utc,
        drugStore.frequency,
        drugStore.intervall,
        drugStore.dose,
        drugStore.consumed_meds_today,
        drugStore.item?.drug_id
      );
      missingDrugError.value = false
      // HIER
      selectedSourceItem.value = sourceItems[0]
      selectedFrequency.value = frequency[0]
      selectedInterval.value = intervallOfDose[0]
      state.dose = 0
      state.endTime = null
      state.selected = "Yes"
    } catch (error) {
      missingDrugError.value = true
      console.log(error);
    }
  }

  else if (!props.edit && props.custom) {

    customNameError.value = !state.customName;
    showDarrFormError.value = !state.customDarrform;

    try {
      if (!customNameError.value && !showDarrFormError.value) {
        let customDrugBody: DrugBody = {
          trade_name: state.customName,
          market_access_date: null,
          market_exit_date: null,
          custom_drug_notes: null,
          attrs: Object.entries(attrState.value).map(([key, value]) => ({ field_name: key, value: value == null ? null : String(value) })),
          attrs_ref: Object.entries(attr_refState).map(([key, value]) => ({ field_name: key, value: value })),
          attrs_multi: Object.entries(attr_multiState).map(([key, value]) => ({ field_name: key, value: value })),
          attrs_multi_ref: Object.entries(attr_multi_refState).map(([key, value]) => ({ field_name: key, value: value })),
          codes: null
        }
        const response = await $fetch(
          `${runTimeConfig.public.baseURL}v2/drug/custom`,
          {
            method: "POST",
            headers: { Authorization: "Bearer " + tokenStore.access_token },
            body: customDrugBody
          }
        );

        await useCreateIntake(
          route.params.study_id,
          route.params.interview_id,
          drugStore.administered_by_doctor,
          drugStore.source,
          drugStore.intake_start_time_utc,
          drugStore.intake_end_time_utc,
          drugStore.frequency,
          drugStore.intervall,
          drugStore.dose,
          drugStore.consumed_meds_today,
          response.id
        );

        drugStore.customVisibility = false
      } else {
        drugStore.customVisibility = true;
      }
    } catch (error) {
      console.error(error);
    }

  } else {
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

//custom drug

const customDrugForm = [
  {
    label: "Zusätzliche Information",
    icon: "i-heroicons-information-circle",
    slot: "custom-form",
  },
];


const showDarrFormError = ref(false);
const selectedDosageForm = ref();
const dosageFormTable = ref();


async function getDosageForm() {
  const dosageForm = await $fetch(
    `${runTimeConfig.public.baseURL}v2/drug/field_def/darreichungsform/refs`,
    {
      method: "GET",
      headers: { Authorization: "Bearer " + tokenStore.access_token },
    }
  );

  dosageFormTable.value = dosageForm.items.map((item) => ({
    id: item.display + " (" + item.value + ")",
    label: item.display + " (" + item.value + ")",
    bedeutung: item.display,
    darrform: item.value,
  }));
}

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

getDosageForm();

// CUSTOM DRUG STUFF

const isDataLoaded = ref(false);
let drugFieldDefinitionsObject: any = null;

const attrState = ref(null);
const attr_refState = reactive<Record<string, string | number | boolean>>({});
const attr_multiState = reactive({});
const attr_multi_refState = reactive<Record<string, string | number | boolean>>({});
const refSelectMenus = ref<{ field_name: string, options: { value: string, display: string }[] }[]>([]);
const multiRefSelectMenus = ref<{ field_name: string, options: { value: string, display: string }[] }[]>([]);
const inputValues = reactive({});

async function createRefSelectMenus(refs: any[], state: any, selectMenus: any, multiple = false) {
  try {
    for (const ref of refs) {
      let item = { field_name: ref[1], options: [] };

      const response = await $fetch(`${runTimeConfig.public.baseURL}v2/drug/field_def/${ref[1]}/refs`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${tokenStore.access_token}`,
        },
      });

      item.options = response.items.map((element) => ({
        value: element.value,
        display: element.display,
      }));

      selectMenus.value.push(item);
      state[ref[1]] = multiple ? [] : item.options[0]?.value;
    }
  } catch (error) {
    console.error("Create refSelectMenus Error:", error);
  }
}

async function createMultiState() {
  drugFieldDefinitionsObject.attrs_multi.forEach(element => {
    attr_multiState[element[1]] = [];
    inputValues[element[1]] = "";
  });
}

function updateMultiState(field) {
  const newValues = inputValues[field]
    .split(',')
    .map(w => w.trim())
    .filter(w => w !== "");

  attr_multiState[field].push(...newValues);
  inputValues[field] = "";
}

function removeItem(field, index) {
  attr_multiState[field].splice(index, 1);
}

const fetchFieldDefinitions = async () => {
  try {
    drugFieldDefinitionsObject = await apiGetFieldDefinitions("dynamic_form");
    attrState.value = reactive(generateDynamicState(drugFieldDefinitionsObject.attrs));
    //schema.value = object(generateDynamicSchema(drugFieldDefinitionsObject));
    isDataLoaded.value = true;
    createRefSelectMenus(drugFieldDefinitionsObject.attrs_ref, attr_refState, refSelectMenus)
    createRefSelectMenus(drugFieldDefinitionsObject.attrs_multi_ref, attr_multi_refState, multiRefSelectMenus, true)
    createMultiState()

  } catch (error) {
    console.error("Error fetching field definitions:", error);
  }
};

function generateDynamicState(fieldsObject: [[]]) {
  const dynamicState = {};
  fieldsObject.forEach(([label, key, type]) => {
    dynamicState[key] = type === "BOOL" ? false : null;
  });
  return dynamicState;
}

// function generateDynamicSchema(fieldsObject) {
//   const dynamicSchema = {};
//   Object.values(fieldsObject).forEach((fieldGroup) => {
//     fieldGroup.forEach(([label, key, type]) => {
//       dynamicSchema[key] = getSchemaForType(type);
//     });
//   });
//   return dynamicSchema;
// }

function getSchemaForType(type: any) {
  switch (type) {
    case "STR":
      return string();
    case "INT":
      return number().integer();
    case "FLOAT":
      return number();
    case "BOOL":
      return boolean();
    case "DATETIME":
      return date();
    case "DATE":
      return date();
    default:
      return string();
  }
}

function getFormInputType(type: any) {
  switch (type) {
    case "STR":
      return "text";
    case "INT":
      return "number";
    case "FLOAT":
      return "number";
    case "BOOL":
      return "checkbox";
    case "DATETIME":
      return "date";
    case "DATE":
      return "date";
    default:
      return "text";
  }
}

interface Attribute {
  [key: string]: any;
}

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

async function onSubmit() {
  let customDrugBody: DrugBody = {
    trade_name: "Aspirin Supercomplex",
    market_access_date: null,
    market_exit_date: null,
    custom_drug_notes: null,
    attrs: Object.entries(attrState.value).map(([key, value]) => ({ field_name: key, value: value == null ? null : String(value) })),
    attrs_ref: Object.entries(attr_refState).map(([key, value]) => ({ field_name: key, value: value })),
    attrs_multi: Object.entries(attr_multiState).map(([key, value]) => ({ field_name: key, value: value })),
    attrs_multi_ref: Object.entries(attr_multi_refState).map(([key, value]) => ({ field_name: key, value: value })),
    codes: null
  }

  try {
    const response = await $fetch(
      `${runTimeConfig.public.baseURL}v2/drug/custom`,
      {
        method: "POST",
        headers: { Authorization: "Bearer " + tokenStore.access_token },
        body: customDrugBody
      }
    );

  } catch (error) {
    console.log(error);
  }
}

onMounted(fetchFieldDefinitions);

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

:deep(td) {
  white-space: normal !important;
  word-break: break-word !important;
}

.flex-container {
  display: flex;
  gap: 16px;
}

.flex-container>* {
  flex: 1;
}

.custom-disabled {
  background-color: #c2c2c2;
  border-style: solid !important;
  border-color: white;
}

.custom-border input {
  color: sky;
  border-style: dotted !important;
  border-color: green !important;
}
</style>
