<template>
    <div style="text-align:center" v-if="!drugStore.item && !initialLoad">
    <br>
    <p style="color:red">Es muss ein Medikament ausgewählt werden</p>
    </div>
  <UForm
    @submit="saveIntake()"
    :state="state"
    :schema="schema"
    class="space-y-4"
  >
    <div style="padding-top: 2.5%">
      <UFormGroup label="Quelle der Arzneimittelangabe">
        <USelect
          v-model="selectedSourceItem"
          :options="sourceItems"
          :color="props.color"
        />
      </UFormGroup>
    </div>
    <UFormGroup label="Einnahme regelmäßig oder nach Bedarf?">
      <USelect v-model="selectedFrequency" :options="frequency" :color="props.color" />
    </UFormGroup>
    <div class="flex-container">
      <UFormGroup
        label="Dosis pro Einnahme"
        style="border-color: red"
        name="dose"
      >
        <UInput
          type="number"
          v-model="state.dose"
          :disabled="selectedFrequency !== 'regelmäßig'"
          :color="selectedFrequency !== 'regelmäßig' ? 'gray' : props.color"
        />
      </UFormGroup>
      <UFormGroup label="Intervall der Tagesdosen">
        <USelect
          v-model="state.intervall"
          :options="intervallOfDose"
          :disabled="selectedFrequency !== 'regelmäßig'"
          :color="selectedFrequency !== 'regelmäßig' ? 'gray' : props.color"
        />
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
    <URadioGroup
      v-model="state.selected"
      legend="Wurden heute Medikamente eingenommen?"
      name="selected"
      :options="options"
      :color="props.color"
    /> 
    <UButton
      type="submit"
      label="Medikament Speichern"
      :color="props.color"
      variant="soft"
      :class="buttonClass"
    /> 
  </UForm>
</template>

<script setup lang="ts">
import dayjs from "dayjs";
import { object, number, date, string, type InferType } from "yup";

const route = useRoute();
// const router = useRouter();
// const tokenStore = useTokenStore();

const drugStore = useDrugStore();
drugStore.$reset()
const initialLoad = ref(true)

// const studyStore = useStudyStore();
// const userStore = useUserStore();
// const runtimeConfig = useRuntimeConfig();

const props = defineProps<{ 
    color? : string 
    edit? : boolean 
    custom? : boolean   
}>();

const buttonClass = computed(() => {
  const color = props.color;
  return `border border-${color}-500 hover:bg-${color}-300 hover:border-white hover:text-white`;
});

// drugStore.item = null;

// // Intakeform

// const drugChosen = ref(true);
// const showIntakeForm = ref(true);

const state = reactive({
  selected: "Yes",
  startTime: dayjs(Date()).format("YYYY-MM-DD"),
  endTime: null,
  dose: 0,
  intervall: null
});

const schema = object({
  selected: string().required("Required"),
  startTime: date().required("Required"),
  dose: number().min(0, "Required"),
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

const tempDose = ref()
const tempIntervall = ref()

async function saveIntake() {    
    drugStore.action = false
    initialLoad.value = false
    tempDose.value = null
    tempIntervall.value = null

    drugStore.source = useDrugSourceTranslator(null, selectedSourceItem.value)    
    if (selectedFrequency.value === "nach Bedarf"){
        drugStore.frequency = "as needed"
    } else {
        drugStore.frequency = "regular"
    }
    drugStore.dose = state.dose
    tempDose.value = drugStore.dose
    drugStore.intervall = useIntervallDoseTranslator(null, state.intervall)
    tempIntervall.value = state.intervall
    drugStore.option = state.selected
    drugStore.intake_start_time_utc = state.startTime 
    drugStore.intake_end_time_utc = state.endTime
    drugStore.consumed_meds_today = state.selected
    
    await useCreateIntake(route.params.study_id, route.params.interview_id, drugStore.item.pzn, drugStore.source, drugStore.intake_start_time_utc, drugStore.intake_end_time_utc, drugStore.frequency, drugStore.intervall, drugStore.dose, drugStore.consumed_meds_today, null)
    drugStore.action = true

}

watch(selectedFrequency, (newValue) => {
  if (newValue === "nach Bedarf") {
    drugStore.frequency = "as needed";
    tempDose.value = state.dose
    state.dose = 0;
    tempIntervall.value = state.intervall
    state.intervall = null;
    selectedInterval.value = null;
  } else {
    drugStore.frequency = "regular";
    state.dose = tempDose.value ? tempDose.value : 1;
    state.intervall = tempIntervall.value
      ? tempIntervall.value
      : "unbekannt";
  }
});

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

.selectedDarrForm:hover {
  color: #efc85d;
  cursor: pointer;
}

.flex-container {
  display: flex;
  gap: 16px;
}

.flex-container > * {
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