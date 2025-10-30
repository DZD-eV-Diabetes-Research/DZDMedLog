<!-- This is the main drug intake form component that deals with the creation of intakes, both regular and custom as well as the editing -->
<template>
  <div v-if="missingDrugError" style="text-align: center">
    <br>
    <p style="color: red">Es muss ein Medikament ausgewählt werden</p>
  </div>

  <!-- Main Form -->

  <UForm :state="state" :schema="schema" class="space-y-4" @submit="saveIntake()">
    <div style="padding-top: 2.5%">
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
          <UInput
            v-model="state.dose" type="number" :disabled="selectedFrequency !== 'regelmäßig'"
            :color="selectedFrequency !== 'regelmäßig' ? 'gray' : props.color" />
        </UFormGroup>
      </div>
      <div class="flex-1">
        <UFormGroup label="Intervall der Tagesdosen">
          <USelect
            v-model="state.intervall" :options="intervallOfDose" :disabled="selectedFrequency !== 'regelmäßig'"
            :color="selectedFrequency !== 'regelmäßig' ? 'gray' : props.color" />
        </UFormGroup>
      </div>
    </div>
    <div class="flex flex-row space-x-4">
      <div class="flex-1">
        <UFormGroup label="Einnahme Beginn (Datum)" name="startTime">
          <UInput v-model="state.startTime" type="date" :color="props.color" />
        </UFormGroup>
      </div>
      <div class="flex-1">
        <UFormGroup label="Einnahme Ende (Datum)" name="endTime">
          <UInput v-model="state.endTime" type="date" :color="props.color" />
        </UFormGroup>
      </div>
    </div>
    <URadioGroup
      v-model="state.selected" legend="Wurden heute Medikamente eingenommen?" name="selected"
      :options="options" :color="props.color" />
    <div style="text-align: center">
      <div v-if="props.edit" class="flex flex-row justify-center space-x-6">
        <UButton type="submit" label="Speichern" :color="props.color" variant="soft" :class="buttonClass" />
        <UButton label="Abbrechen" :color="props.color" variant="soft" :class="buttonClass" @click="closeEditModal()" />
      </div>
      <div v-else>
        <UButton
          type="submit" :label="props.label" :color="props.color"
          class="border border-green-500 hover:bg-green-300 hover:border-white hover:text-white" variant="soft"
          :class="buttonClass" />
      </div>
    </div>
  </UForm>
</template>

<script setup lang="ts">

import dayjs from "dayjs";
import { object, number, date, string, type InferType } from "yup";


const { $medlogapi } = useNuxtApp();
const route = useRoute();
const drugStore = useDrugStore();
const initialLoad = ref(true);

const props = defineProps<{
  color?: string;
  edit?: boolean;
  label?: string;
  row?: any;
}>();

const buttonClass = computed(() => {
  const color = props.color;
  if (color === "primary") {
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
});

const schema = object({
  selected: string().required("Required"),
  startTime: date().required("Required"),
  dose: number().min(0, "Required"),
  name: string(),
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
  tempDose.value = drugStore.dose;
  drugStore.intervall = useIntervallDoseTranslator(null, state.intervall);
  tempIntervall.value = state.intervall;
  drugStore.option = state.selected;
  drugStore.intake_start_time_utc = state.startTime;
  drugStore.intake_end_time_utc = state.endTime;
  drugStore.consumed_meds_today = state.selected;

  if (props.edit) {
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
  } else if (!props.edit) {

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


const closeEditModal = function () {
  drugStore.editVisibility = false
  drugStore.item = null
}
</script>
