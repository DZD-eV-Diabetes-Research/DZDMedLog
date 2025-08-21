<!-- This is the main drugform component that deals with the creation of intakes, both regular and custom as well as the editing -->

<template>
  <div style="text-align: center" v-if="missingDrugError">
    <br />
    <p style="color: red">Es muss ein Medikament ausgewählt werden</p>
  </div>

  <!-- Main Form -->

  <UForm @submit="saveIntake()" :state="state" :schema="schema" class="space-y-4">
    <div style="padding-top: 2.5%">
      <div v-if="props.custom">
        <div class="text-center pt-4 pb-8" v-if="!props.edit">
          <h4 class="text-xl font-light">
            Hiermit wird einmalig ein Medikament angelegt, das in der
            Medikamentensuche nicht gefunden wurde.
          </h4>
        </div>

        <!-- Error message if no drug is selected and the field is left blank -->
        <h5 v-if="customNameError" style="color: red">
          Name wird benötigt
        </h5>
        <UFormGroup label="Name" name="customName" required class="mb-6">
          <UInput v-model="state.customName" color="yellow" />
        </UFormGroup>
        <UAccordion :items="customDrugForm" color="yellow">

          <!-- Here starts the custom form which is quite complex -->

          <template #custom-form>
            <div v-if="isDataLoaded" class="bg-yellow-50 outline-yellow-200 rounded-md p-2">

              <!-- After the drugFieldDefinitionsObject is created we loop through each of the 4 arrays:
              attr: A free field in case of yes and no questions, boolean
              attr_ref: A predefined selection of options
              attr_multi: Multiple answers possible
              attr_multi_ref: Multiple answers of predefined selction possible
              and created inputs for each item in this array. -->

              <UForm :state="attrState" class="space-y-4">
                <UFormGroup v-for="attr in drugFieldDefinitionsObject.attrs" :key="attr[1]" :name="attr[1]">
                  <!-- Label-Slot: Text + Tooltip-Icon -->
                  <template #label>
                    <span class="inline-flex items-center gap-1">
                      {{ attr[0] }}
                      <UTooltip :text="attr[3]"  :popper="{placement: 'right'}" :ui="{ width: 'max-w-4xl' }">
                        <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-yellow-500 cursor-pointer" />
                      </UTooltip>
                    </span>
                  </template>

                  <!-- Input oder Checkbox -->
                  <UInput v-if="getFormInputType(attr[2]) !== 'checkbox'" v-model="attrState[attr[1]]"
                    :type="getFormInputType(attr[2])" color="yellow" />
                  <UCheckbox v-else v-model="attrState[attr[1]]" color="yellow" :name="attr[1]" />
                </UFormGroup>


                <UFormGroup v-for="attr_ref in drugFieldDefinitionsObject.attrs_ref" :name="attr_ref[1]"
                  :key="attr_ref[1]">
                  <template #label>
                    <span class="inline-flex items-center gap-1">
                      {{ attr_ref[0] }}
                      <UTooltip :text="attr_ref[3]" :popper="{placement: 'right'}" :ui="{ width: 'max-w-4xl' }">
                        <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-yellow-500 cursor-pointer" />
                      </UTooltip>
                    </span>
                  </template>
                  
                  <USelectMenu v-model="attr_refState[attr_ref[1]]"
                    :options="refSelectMenus.find(item => item.field_name === attr_ref[1])?.options"
                    value-attribute="value" option-attribute="display" color="yellow" placeholder="Option auswählen" />
                </UFormGroup>
                <UFormGroup v-for="attr_multi in drugFieldDefinitionsObject.attrs_multi" :name="attr_multi[1]"
                  :key="attr_multi[1]">
                  <template #label>
                    <span class="inline-flex items-center gap-1">
                      {{ attr_multi[0] }}
                      <UTooltip :text="attr_multi[3]" :popper="{placement: 'right'}" :ui="{ width: 'max-w-4xl' }">
                        <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-yellow-500 cursor-pointer" />
                      </UTooltip>
                    </span>
                  </template>
                  <UInput placeholder="Option auswählen und Enter drücken" v-model="inputValues[attr_multi[1]]"
                    @keydown.enter.prevent="updateMultiState(attr_multi[1])" @blur="updateMultiState(attr_multi[1])"
                    color="yellow" />
                  <UBadge v-for="(word, index) in attr_multiState[attr_multi[1]]" :key="index"
                    class="mr-2 cursor-pointer" @click="removeItem(attr_multi[1], index)" color="yellow">
                    {{ word }}
                  </UBadge>
                </UFormGroup>
                <UFormGroup v-for="attr_multi_ref in drugFieldDefinitionsObject.attrs_multi_ref"
                  :name="attr_multi_ref[1]" :key="attr_multi_ref[1]">
                  <template #label>
                    <span class="inline-flex items-center gap-1">
                      {{ attr_multi_ref[0] }}
                      <UTooltip :text="attr_multi_ref[3]" :popper="{placement: 'right'}" :ui="{ width: 'max-w-4xl' }">
                        <UIcon name="i-heroicons-question-mark-circle" class="w-4 h-4 text-yellow-500 cursor-pointer" />
                      </UTooltip>
                    </span>
                  </template>
                  <USelectMenu v-model="attr_multi_refState[attr_multi_ref[1]]"
                    :options="multiRefSelectMenus.find(item => item.field_name === attr_multi_ref[1])?.options"
                    value-attribute="value" option-attribute="display" multiple searchable color="yellow"
                    placeholder="Option auswählen">
                    <template #label>
                      <span
                        v-if="Array.isArray(attr_multi_refState[attr_multi_ref[1]]) && attr_multi_refState[attr_multi_ref[1]].length">
                        {{attr_multi_refState[attr_multi_ref[1]].map(val => multiRefSelectMenus.find(item =>
                          item.field_name ===
                          attr_multi_ref[1])?.options.find(option => option.value === val)?.display || val)
                          .join('; ')}}
                      </span>
                      <span v-else>Mehrfachauswahl möglich</span>
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

      <!-- From this point on this is the part that is visibile to all drugforms -->

      <UFormGroup label="Quelle der Arzneimittelangabe">
        <USelect v-model="selectedSourceItem" :options="sourceItems" :color="props.color" />
      </UFormGroup>
    </div>
    <UFormGroup label="Einnahme regelmäßig oder nach Bedarf?">
      <USelect v-model="selectedFrequency" :options="frequency" :color="props.color" />
    </UFormGroup>
    <div class="flex flex-row space-x-4">
      <div class="flex-1">
        <UFormGroup label="Dosis pro Einnahme" style="border-color: red" name="dose">
          <UInput type="number" v-model="state.dose" :disabled="selectedFrequency !== 'regelmäßig'"
            :color="selectedFrequency !== 'regelmäßig' ? 'gray' : props.color" />
        </UFormGroup>
      </div>
      <div class="flex-1">
        <UFormGroup label="Intervall der Tagesdosen">
          <USelect v-model="state.intervall" :options="intervallOfDose" :disabled="selectedFrequency !== 'regelmäßig'"
            :color="selectedFrequency !== 'regelmäßig' ? 'gray' : props.color" />
        </UFormGroup>
      </div>
    </div>
    <div class="flex flex-row space-x-4">
      <div class="flex-1">
        <UFormGroup label="Einnahme Beginn (Datum)" name="startTime">
          <UInput type="date" v-model="state.startTime" :color="props.color" />
        </UFormGroup>
      </div>
      <div class="flex-1">
        <UFormGroup label="Einnahme Ende (Datum)" name="endTime">
          <UInput type="date" v-model="state.endTime" :color="props.color" />
        </UFormGroup>
      </div>
    </div>
    <URadioGroup v-model="state.selected" legend="Wurden heute Medikamente eingenommen?" name="selected"
      :options="options" :color="props.color" />
    <div style="text-align: center">
      <div v-if="props.edit" class="flex flex-row justify-center space-x-6">
        <UButton type="submit" label="Speichern" :color="props.color" variant="soft" :class="buttonClass" />
        <UButton label="Abbrechen" :color="props.color" variant="soft" :class="buttonClass" @click="closeEditModal()">
        </UButton>
      </div>
      <div v-else>
        <UButton type="submit" :label="props.label" :color="props.color" class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" variant="soft" :class="buttonClass" />
      </div>
    </div>
    <div class="flex flex-col justify-center items-center">
      <h5 v-if="showDarrFormError" style="color: red">
        Darreichungsform wird benötigt
      </h5>
      <br>

      <!-- Again the error message the,same from the top for better userexperience -->
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
const { $medlogapi } = useNuxtApp();


const route = useRoute();
const drugStore = useDrugStore();
const initialLoad = ref(true);

const props = defineProps<{
  color?: string;
  edit?: boolean;
  custom?: boolean;
  label?: string;
  row?: any;
}>();

const buttonClass = computed(() => {
  const color = props.color;
  if (color === "primary"){
    return `border border-green-500 hover:bg-green-300 hover:border-white hover:text-white`;
  }
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

      await $medlogapi(
        `/api/study/{studyId}/interview/{interviewId}/intake/{toEditDrugId}`,
        {
          method: "PATCH",
          body: patchBody,
          path: {
            studyId: route.params.study_id,
            interviewId: route.params.interview_id,
            toEditDrugId: drugStore.editId
          }
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


    try {
      if (!customNameError.value) {
        let customDrugBody: DrugBody = {
          trade_name: state.customName,
          market_access_date: null,
          market_exit_date: null,
          custom_drug_notes: null,
          attrs: Object.entries(attrState.value).map(([key, value]) => ({ field_name: key, value: value == null ? null : String(value) })),
          attrs_ref: Object.entries(attr_refState).map(([key, value]) => ({ field_name: key, value: value })),
          attrs_multi: Object.entries(attr_multiState).map(([key, value]) => ({ field_name: key, values: value })),
          attrs_multi_ref: Object.entries(attr_multi_refState).map(([key, value]) => ({ field_name: key, values: value })),
          codes: null
        }

        const response = await $medlogapi(
          `/api/drug/custom`,
          {
            method: "POST",
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

const selectedDosageForm = ref();
const dosageFormTable = ref();


async function getDosageForm() {
  const dosageForm = await $medlogapi(
    `/api/drug/field_def/darreichungsform/refs`);

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

// CUSTOM DRUG

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

      //DIRTY FIX FOR COMPLETE REFS (?limit=99999)
      const response = await $medlogapi(`/api/drug/field_def/{ref}/refs?limit=99999`, {
        path: {
          ref: ref[1]
        }
      });

      item.options = response.items.map((element) => ({
        value: element.value,
        display: element.display,
      }));

      selectMenus.value.push(item);
      state[ref[1]] = multiple ? [] : null;
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

const closeEditModal = function () {
  drugStore.editVisibility = false
  drugStore.item = null
}

onMounted(() => {
  if (props.custom) {
    // nur für das Custom-Form laden
    getDosageForm()
    fetchFieldDefinitions()
  }
})
</script>